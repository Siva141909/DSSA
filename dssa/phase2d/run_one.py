"""Executes one approved Phase 2D run.

Training is train.run_training itself, unchanged: only three names inside the
train module are replaced from outside, to add instrumentation.
  train.build_model -> isolated LoRA init plus pre-run assertions
  train.evaluate    -> per-tile matrices, validation timing
  train.make_batch  -> runtime, memory and integrity ticks
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

C.install_guards()
sys.path.insert(0, str(C.ROOT / "train"))
import numpy as np  # noqa: E402
import torch  # noqa: E402
import dataset as ds_mod  # noqa: E402
import train as T  # noqa: E402
from checkpoint import save_checkpoint  # noqa: E402
from metrics import ConfusionMatrixAccumulator  # noqa: E402
import lora as lora_mod  # noqa: E402
import models as M  # noqa: E402
import evaluation as E  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_id")
    ap.add_argument("--smoke", action="store_true", help="2-step wiring test, written under gate0/smoke, never a result")
    a = ap.parse_args()
    t_start = time.time()
    base = json.load(open(C.BASELINE))
    C.assert_frozen_unchanged()

    manifest = json.load(open(C.MANIFEST))
    entry = next(r for r in manifest["runs"] if r["run_id"] == a.run_id)
    if C.config_hash(entry) != entry["config_hash"]:
        raise RuntimeError("config hash mismatch")
    if C.code_hash() != manifest["code_hash"]:
        raise RuntimeError("Phase 2D code differs from the manifest")
    seed, layers, lora_seed = entry["training_seed"], entry["layer_indices"], entry["lora_init_seed"]
    exp = base["expected"][str(seed)]

    out = (C.GATE0 / "smoke" / a.run_id) if a.smoke else (C.RUNS / a.run_id)
    C.check_write_path(out)
    if out.exists():
        raise FileExistsError(f"destination exists: {out}")
    if C.simulate_data_stream(seed) != exp["data_stream_final"]:
        raise RuntimeError("data stream replay does not match Gate 0")
    out.mkdir(parents=True)
    (out / "IN_PROGRESS").write_text(str(time.time()))

    opened: set = set()
    C.install_tile_allowlist(ds_mod, opened)
    mon = C.Monitor()
    mon.start()
    state = {"pre": {}, "evals": [], "ds": None, "steps": 0, "val_s": 0.0}
    limit_s = entry["est_seconds"] * 1.5

    def tick():
        if mon.fault:
            raise RuntimeError(f"STOP: {mon.fault}")
        if not a.smoke and time.time() - t_start > limit_s:
            raise RuntimeError(f"STOP: runtime above 1.5x estimate ({limit_s:.0f}s)")

    def p_build(layer_indices, device):
        if list(layer_indices) != layers:
            raise RuntimeError("layer list mismatch")
        model, mods = M.build(list(layer_indices), device, lora_seed)
        chk = {}
        chk["decoder_hash"] = M.decoder_hash(model.decoder)
        chk["torch_rng_hash"] = M.tensor_hash([torch.get_rng_state()])
        chk["backbone_fp"] = M.backbone_fingerprint(model)
        chk["probe_hash"] = M.probe_output_hash(model, device)
        for k, want in (("decoder_hash", exp["decoder_hash"]), ("torch_rng_hash", exp["torch_rng_hash"]),
                        ("backbone_fp", base["expected_common"]["backbone_fp"]), ("probe_hash", base["expected_common"]["probe_hash"])):
            if chk[k] != want:
                raise RuntimeError(f"pre-run assertion failed: {k}")
        lora_mod.assert_only_intended_trainable(model.encoder, set(layers))
        n_lora = sum(m.lora_param_count() for m in mods)
        if n_lora != 32768 * len(layers):
            raise RuntimeError("LoRA parameter count")
        for m in mods:
            if not (torch.count_nonzero(m.lora_B_q) == 0 and torch.count_nonzero(m.lora_B_v) == 0):
                raise RuntimeError("B not zero")
            if M.tensor_hash([m.lora_A_q, m.lora_A_v]) != exp["lora_A_hash"]:
                raise RuntimeError("A init hash mismatch")
        chk["lora_params"] = n_lora
        state["pre"] = chk
        return model, mods

    orig_batch = T.make_batch

    def p_batch(dataset, batch_size, device):
        state["ds"] = dataset
        tick()
        state["steps"] += 1
        return orig_batch(dataset, batch_size, device)

    def p_eval(model, filenames, device, eval_max_size=None):
        t0 = time.time()
        if not a.smoke and sorted(filenames) != sorted(C.VAL):
            raise RuntimeError("validation file list mismatch")
        ds = ds_mod.TargetSegDataset(filenames, mode="eval", eval_max_size=eval_max_size)
        total, tiles, ce, n = ConfusionMatrixAccumulator(), {}, 0.0, 0
        for i in range(len(ds)):
            tick()
            cal, lab, fn = ds[i]
            _, cm, c = E.eval_tile(model, cal, lab, device)
            total.matrix += cm
            tiles[fn] = cm.tolist()
            ce += c
            n += lab.size
        torch.mps.synchronize()
        res = total.compute()
        dt = time.time() - t0
        state["val_s"] += dt
        if not np.isfinite([res["mean_iou"], res["macro_f1"], res["pixel_accuracy"], ce]).all():
            raise RuntimeError("non-finite validation metric")
        state["evals"].append({"step": state["steps"], "seconds": dt, "mean_iou": res["mean_iou"], "val_ce": ce / n, "tiles": tiles, "per_class_iou": res["per_class_iou"]})
        return res

    T.build_model, T.make_batch, T.evaluate = p_build, p_batch, p_eval
    spec = {"run_id": a.run_id, "K": entry["K"], "layer_indices": layers, "condition_labels": entry["condition_labels"], "training_seed": seed}
    kw = dict(total_steps=2, checkpoint_every=2, warmup_steps=1, val_files_override=C.VAL[-1:], eval_max_size=448, preflight=True) if a.smoke else dict(preflight=False)
    train_result, model, mods = T.run_training(spec, device="mps", out_dir=out, log=print, **kw)
    torch.mps.synchronize()

    final_ckpt = out / f"{a.run_id}_final.pt"
    save_checkpoint(final_ckpt, model, mods, sorted(layers), state["steps"], extra={"val_metrics_step": state["evals"][-1]["step"]})
    fp_after = M.backbone_fingerprint(model)
    if fp_after != base["expected_common"]["backbone_fp"]:
        raise RuntimeError("backbone fingerprint changed")
    if not a.smoke and C.rng_state_hash(state["ds"]._rng) != exp["data_stream_final"]:
        raise RuntimeError("final data-stream state does not match replay")
    bad = opened - C.ALLOWED_TILES
    if bad:
        raise RuntimeError(f"unapproved tiles opened: {bad}")
    mon.halt = True
    mon.join()
    C.assert_frozen_unchanged()
    total_train = train_result["training_wall_clock_seconds"]
    r = C.rusage()
    res = {
        "status": "completed_unverified", "smoke": a.smoke, "entry": entry, "manifest_sha": C.sha256_file(C.MANIFEST),
        "train_result": {k: v for k, v in train_result.items() if k not in ("peak_memory_mb", "validation_history")},
        "validation_history": train_result["validation_history"], "evals": state["evals"], "pre_run_checks": state["pre"],
        "post_run_checks": {"backbone_fp": fp_after, "data_stream_ok": True, "tiles_opened": sorted(opened), "steps": state["steps"]},
        "timing": {"loop_seconds": total_train, "validation_seconds": state["val_s"], "training_seconds": total_train - state["val_s"], "process_seconds": time.time() - t_start},
        "memory": {"kernel_lifetime_max_footprint_mb": r["lifetime_max_phys_footprint_mb"], "sampled_max": mon.max, "pressure_warn_samples": mon.pressure_warn_samples, "samples": mon.samples, "series": mon.series},
        "env": {"torch": torch.__version__, "hardware": T.hardware_info()},
    }
    C.write_json_atomic(out / "result.json", res)
    (out / "IN_PROGRESS").unlink()
    print(f"[done] {a.run_id} best={train_result['best_val_mean_iou']:.4f}@{train_result['best_step']} final={state['evals'][-1]['mean_iou']:.4f} loop={total_train:.0f}s val={state['val_s']:.0f}s peak={r['lifetime_max_phys_footprint_mb']:.0f}MB")


if __name__ == "__main__":
    main()
