"""Manifest v2 runner. Differs from run_one.py in three ways only:
  1. train.TargetSegDataset -> TargetSegDatasetU8 (training-tile cache).
  2. Continuous telemetry (telemetry.jsonl) with exact optimizer step and stage.
  3. incident.json is written on any failure.
train.run_training is still called unchanged."""
from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

C.install_guards()
sys.path.insert(0, str(C.ROOT / "train"))
import numpy as np  # noqa: E402
import torch  # noqa: E402
import torch.optim.optimizer as optimizer_module  # noqa: E402
import dataset as ds_mod  # noqa: E402
import train as T  # noqa: E402
from checkpoint import save_checkpoint  # noqa: E402
from metrics import ConfusionMatrixAccumulator  # noqa: E402
import lora as lora_mod  # noqa: E402
import models as M  # noqa: E402
import evaluation as E  # noqa: E402
from dataset_u8 import TargetSegDatasetU8  # noqa: E402

MANIFEST_V2 = C.ART / "manifest_pilot_v2.json"


class Telemetry(C.Monitor):
    def __init__(self, path, state, dt=0.25):
        super().__init__(dt=dt)
        self.f, self.state, self.tail = open(path, "a", buffering=1), state, []

    def run(self):
        while not self.halt:
            r = C.rusage()
            d, c = torch.mps.driver_allocated_memory() / 2**20, torch.mps.current_allocated_memory() / 2**20
            lv, used = C.pressure_level(), C.swap_used_mb()
            sw = used - self.swap0
            m = self.max
            m["driver_mb"], m["current_mb"] = max(m["driver_mb"], d), max(m["current_mb"], c)
            m["phys_mb"], m["swap_growth_mb"], m["pressure"] = max(m["phys_mb"], r["phys_footprint_mb"]), max(m["swap_growth_mb"], sw), max(m["pressure"], lv)
            self.samples += 1
            self.pressure_warn_samples += lv >= 2
            rec = {"t": round(time.time(), 3), "opt_step": self.state["opt_steps"], "stage": self.state["stage"], "phys_mb": round(r["phys_footprint_mb"], 1),
                   "life_max_mb": round(r["lifetime_max_phys_footprint_mb"], 1), "resident_mb": round(r["resident_mb"], 1), "driver_mb": round(d, 1), "current_mb": round(c, 1),
                   "pressure": lv, "swap_used_mb": round(used, 1), "swap_growth_mb": round(sw, 1)}
            self.f.write(json.dumps(rec) + "\n")
            self.tail = (self.tail + [rec])[-200:]
            if r["lifetime_max_phys_footprint_mb"] > C.MEM_LIMIT_MB:
                self.fault = f"process footprint {r['lifetime_max_phys_footprint_mb']:.0f} MB above limit"
            elif sw > C.SWAP_GROWTH_LIMIT_MB:
                self.fault = f"swap growth {sw:.0f} MB above limit"
            elif lv >= 4:
                self.fault = "macOS memory pressure critical"
            time.sleep(self.dt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_id")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--inject-stop", action="store_true", help="smoke only: proves incident.json is written")
    a = ap.parse_args()
    if a.inject_stop and not a.smoke:
        raise SystemExit("--inject-stop requires --smoke")
    t_start = time.time()
    base = json.load(open(C.BASELINE))
    C.assert_frozen_unchanged()
    manifest = json.load(open(MANIFEST_V2))
    entry = next(r for r in manifest["runs"] if r["run_id"] == a.run_id)
    if C.config_hash(entry) != entry["config_hash"]:
        raise RuntimeError("config hash mismatch")
    if C.code_hash() != manifest["code_hash"]:
        raise RuntimeError("Phase 2D code differs from manifest v2")
    seed, layers, lora_seed = entry["training_seed"], entry["layer_indices"], entry["lora_init_seed"]
    exp = base["expected"][str(seed)]
    out = C.GATE0 / "smoke" / (a.run_id + ("_faulttest" if a.inject_stop else "")) if a.smoke else C.RUNS / a.run_id
    C.check_write_path(out)
    if out.exists():
        raise FileExistsError(f"destination exists: {out}")
    if C.simulate_data_stream(seed) != exp["data_stream_final"]:
        raise RuntimeError("data stream replay does not match Gate 0")
    out.mkdir(parents=True)
    (out / "IN_PROGRESS").write_text(str(time.time()))

    state = {"pre": {}, "evals": [], "ds": None, "batches": 0, "opt_steps": 0, "val_s": 0.0, "stage": "startup"}
    opened: set = set()
    mon = Telemetry(out / "telemetry.jsonl", state)
    mon.start()
    try:
        C.install_tile_allowlist(ds_mod, opened)
        optimizer_module.register_optimizer_step_post_hook(lambda o, ar, kw: state.__setitem__("opt_steps", state["opt_steps"] + 1))
        limit_s = entry["est_seconds"] * 1.5

        def tick():
            if mon.fault:
                raise RuntimeError(f"STOP: {mon.fault}")
            if not a.smoke and time.time() - t_start > limit_s:
                raise RuntimeError(f"STOP: runtime above 1.5x estimate ({limit_s:.0f}s)")

        def p_build(layer_indices, device):
            state["stage"] = "build_model"
            if list(layer_indices) != layers:
                raise RuntimeError("layer list mismatch")
            model, mods = M.build(list(layer_indices), device, lora_seed)
            state["stage"] = "pre_run_checks"
            chk = {"decoder_hash": M.decoder_hash(model.decoder), "torch_rng_hash": M.tensor_hash([torch.get_rng_state()]),
                   "backbone_fp": M.backbone_fingerprint(model), "probe_hash": M.probe_output_hash(model, device)}
            for k, want in (("decoder_hash", exp["decoder_hash"]), ("torch_rng_hash", exp["torch_rng_hash"]),
                            ("backbone_fp", base["expected_common"]["backbone_fp"]), ("probe_hash", base["expected_common"]["probe_hash"])):
                if chk[k] != want:
                    raise RuntimeError(f"pre-run assertion failed: {k}")
            lora_mod.assert_only_intended_trainable(model.encoder, set(layers))
            if sum(m.lora_param_count() for m in mods) != 32768 * len(layers):
                raise RuntimeError("LoRA parameter count")
            for m in mods:
                if not (torch.count_nonzero(m.lora_B_q) == 0 and torch.count_nonzero(m.lora_B_v) == 0):
                    raise RuntimeError("B not zero")
                if M.tensor_hash([m.lora_A_q, m.lora_A_v]) != exp["lora_A_hash"]:
                    raise RuntimeError("A init hash mismatch")
            state["pre"] = chk
            return model, mods

        orig_batch = T.make_batch

        def p_batch(dataset, batch_size, device):
            state["ds"] = dataset
            state["stage"] = "train"
            if a.inject_stop and state["opt_steps"] >= 1:
                mon.fault = "injected test fault"
            tick()
            state["batches"] += 1
            return orig_batch(dataset, batch_size, device)

        def p_eval(model, filenames, device, eval_max_size=None):
            state["stage"] = "validation"
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
            state["evals"].append({"step": state["opt_steps"], "seconds": dt, "mean_iou": res["mean_iou"], "val_ce": ce / n, "tiles": tiles, "per_class_iou": res["per_class_iou"]})
            state["stage"] = "train"
            return res

        T.build_model, T.make_batch, T.evaluate, T.TargetSegDataset = p_build, p_batch, p_eval, TargetSegDatasetU8
        spec = {"run_id": a.run_id, "K": entry["K"], "layer_indices": layers, "condition_labels": entry["condition_labels"], "training_seed": seed}
        kw = dict(total_steps=4 if a.inject_stop else 2, checkpoint_every=2, warmup_steps=1, val_files_override=C.VAL[-1:], eval_max_size=448, preflight=True) if a.smoke else dict(preflight=False)
        train_result, model, mods = T.run_training(spec, device="mps", out_dir=out, log=print, **kw)
        torch.mps.synchronize()
        state["stage"] = "post_run"
        final_ckpt = out / f"{a.run_id}_final.pt"
        save_checkpoint(final_ckpt, model, mods, sorted(layers), state["opt_steps"], extra={"val_metrics_step": state["evals"][-1]["step"]})
        fp_after = M.backbone_fingerprint(model)
        if fp_after != base["expected_common"]["backbone_fp"]:
            raise RuntimeError("backbone fingerprint changed")
        if not a.smoke and C.rng_state_hash(state["ds"]._rng) != exp["data_stream_final"]:
            raise RuntimeError("final data-stream state does not match replay")
        if opened - C.ALLOWED_TILES:
            raise RuntimeError("unapproved tiles opened")
        mon.halt = True
        mon.join()
        C.assert_frozen_unchanged()
        r = C.rusage()
        loop = train_result["training_wall_clock_seconds"]
        res = {"status": "completed_unverified", "smoke": a.smoke, "entry": entry, "manifest_sha": C.sha256_file(MANIFEST_V2),
               "train_result": {k: v for k, v in train_result.items() if k not in ("peak_memory_mb", "validation_history")},
               "validation_history": train_result["validation_history"], "evals": state["evals"], "pre_run_checks": state["pre"],
               "post_run_checks": {"backbone_fp": fp_after, "data_stream_ok": True, "tiles_opened": sorted(opened), "steps": state["opt_steps"]},
               "timing": {"loop_seconds": loop, "validation_seconds": state["val_s"], "training_seconds": loop - state["val_s"], "process_seconds": time.time() - t_start},
               "memory": {"kernel_lifetime_max_footprint_mb": r["lifetime_max_phys_footprint_mb"], "sampled_max": mon.max, "pressure_warn_samples": mon.pressure_warn_samples, "samples": mon.samples, "swap_at_start_mb": mon.swap0},
               "env": {"torch": torch.__version__, "hardware": T.hardware_info()}}
        C.write_json_atomic(out / "result.json", res)
        (out / "IN_PROGRESS").unlink()
        print(f"[done] {a.run_id} best={train_result['best_val_mean_iou']:.4f}@{train_result['best_step']} final={state['evals'][-1]['mean_iou']:.4f} loop={loop:.0f}s val={state['val_s']:.0f}s peak={r['lifetime_max_phys_footprint_mb']:.0f}MB swapgrow={mon.max['swap_growth_mb']:.0f}MB")
    except BaseException as ex:
        C.write_json_atomic(out / "incident.json", {"error": repr(ex), "traceback": traceback.format_exc(), "time": time.time(), "elapsed_s": time.time() - t_start,
                                                    "optimizer_steps_completed": state["opt_steps"], "batches_drawn": state["batches"], "stage": state["stage"], "evals_completed": len(state["evals"]),
                                                    "memory_final": C.rusage(), "swap_used_mb": C.swap_used_mb(), "swap_at_start_mb": mon.swap0, "pressure": C.pressure_level(), "sampled_max": mon.max,
                                                    "telemetry_tail": mon.tail, "tiles_opened": sorted(opened)})
        mon.halt = True
        print(f"[incident] {ex!r} at optimizer step {state['opt_steps']} stage {state['stage']}", flush=True)
        raise


if __name__ == "__main__":
    main()
