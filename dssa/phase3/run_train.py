"""Phase 3 training process for one manifest entry. The frozen Phase 2C/2D recipe
(train.run_training) with one deliberate difference (D9, D22): no evaluation of any kind in
this process; the step-2000 checkpoint is evaluated afterwards, one fresh process per tile.
Loop body, order of RNG use, optimiser, schedule, loss and clipping are those of
train.run_training. Telemetry every 0.25 s; 11.5 GB fault, 11.0 GB early abort, swap and
pressure faults, runtime limit (manifest runtime_factor x est_seconds, default 1.5x); incident.json on any failure; never overwrites."""
from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import p3common as C  # noqa: E402

C.install_guards()
C.setup_paths()
import sigsafe  # noqa: E402

sigsafe.restore()
import numpy as np  # noqa: E402
import torch  # noqa: E402
import torch.optim.optimizer as optimizer_module  # noqa: E402
import train as T  # noqa: E402
from checkpoint import save_checkpoint  # noqa: E402
from losses import CEDiceLoss  # noqa: E402
import models as M  # noqa: E402
import p3run as R  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_id")
    a = ap.parse_args()
    t_start = time.time()
    mpath = C.manifest_for(a.run_id)
    manifest = json.load(open(mpath))
    entry = next(r for r in manifest["runs"] if r["run_id"] == a.run_id)
    if C.config_hash(entry) != entry["config_hash"]:
        raise RuntimeError("config hash mismatch")
    if C.code_hash() != manifest["code_hash"]:
        raise RuntimeError("Phase 3 code differs from the manifest")
    s = C.split()
    if C.sha256_file(C.SPLIT_FILE) != manifest["split_sha256"]:
        raise RuntimeError("split hash differs from the manifest")
    seed, layers, lora_seed = entry["training_seed"], sorted(entry["layer_indices"]), entry["lora_init_seed"]
    rank, stage_d = entry.get("rank", 8), a.run_id.startswith("p3d_")
    train_files = s["train"]
    out = C.RUNS / a.run_id
    C.check_write_path(out)
    if out.exists():
        raise FileExistsError(f"destination exists: {out}")
    draws = T.TOTAL_STEPS * T.BATCH_SIZE
    expected_stream = R.replay_stream(seed, train_files, draws)
    out.mkdir(parents=True)
    (out / "IN_PROGRESS").write_text(str(time.time()))
    C.LABEL_ALLOW.update(C.potsdam_tile_id(n) for n in train_files)

    state = {"opt_steps": 0, "stage": "startup", "batches": 0}
    mon = C.Telemetry(out / "telemetry.jsonl", state, out)
    mon.start()
    factor = manifest.get("runtime_factor", 1.5)
    limit_s = entry["est_seconds"] * factor
    try:
        optimizer_module.register_optimizer_step_post_hook(lambda o, ar, kw: state.__setitem__("opt_steps", state["opt_steps"] + 1))

        def tick():
            if mon.fault:
                raise RuntimeError(f"STOP: {mon.fault}")
            if time.time() - t_start > limit_s:
                raise RuntimeError(f"STOP: runtime above {factor}x estimate ({limit_s:.0f}s)")

        state["stage"] = "build_model"
        model, mods, pre = R.build_checked(layers, seed, lora_seed, rank=rank, stage_d=stage_d)
        total_params = sum(p.numel() for p in model.parameters())
        trainable = [p for p in model.parameters() if p.requires_grad]
        n_train = sum(p.numel() for p in trainable)
        dec = sum(p.numel() for p in model.decoder.parameters())
        lo = sum(m.lora_param_count() for m in mods)
        assert n_train == dec + lo
        train_ds = R.PotsdamSegDatasetU8(train_files, seed=seed)
        optimizer = torch.optim.AdamW(trainable, lr=T.LR, betas=T.BETAS, weight_decay=T.WEIGHT_DECAY)
        loss_fn = CEDiceLoss()
        losses = []
        print(f"[{a.run_id}] layers={layers} trainable={n_train} (decoder={dec}, lora={lo}) seed={seed}", flush=True)
        t_loop = time.time()
        for step in range(T.TOTAL_STEPS):
            state["stage"] = "train"
            model.train()
            lr = T.cosine_lr(step, T.TOTAL_STEPS, T.WARMUP_STEPS, T.LR)
            for g in optimizer.param_groups:
                g["lr"] = lr
            tick()
            state["batches"] += 1
            x_batch, y_batch = T.make_batch(train_ds, T.BATCH_SIZE, "mps")
            optimizer.zero_grad(set_to_none=True)
            logits = model(x_batch)
            assert logits.shape == (T.BATCH_SIZE, 6, 224, 224)
            loss = loss_fn(logits, y_batch)
            if not torch.isfinite(loss):
                raise RuntimeError(f"non-finite loss at step {step}: {loss.item()}")
            loss.backward()
            gn = torch.nn.utils.clip_grad_norm_(trainable, T.GRAD_CLIP_NORM)
            if not torch.isfinite(gn):
                raise RuntimeError(f"non-finite grad norm at step {step}: {gn}")
            optimizer.step()
            if (step + 1) % 200 == 0:
                losses.append({"step": step + 1, "train_loss": float(loss.item()), "lr": lr})
                print(f"[{a.run_id}] step={step + 1} loss={loss.item():.4f} t={time.time() - t_loop:.0f}s", flush=True)
        torch.mps.synchronize()
        loop_s = time.time() - t_loop
        state["stage"] = "post_run"
        if state["opt_steps"] != T.TOTAL_STEPS:
            raise RuntimeError("optimizer step count")
        final_ckpt = out / f"{a.run_id}_final.pt"
        save_checkpoint(final_ckpt, model, mods, layers, state["opt_steps"], extra={"phase": 3, "evaluated_in_process": False})
        pl = R.probe_logits(model)
        np.save(out / "probe_logits.npy", pl.numpy())
        fp_after = M.backbone_fingerprint(model)
        if fp_after != R.baseline()["expected_common"]["backbone_fp"]:
            raise RuntimeError("backbone fingerprint changed")
        stream = R.rng_hash(train_ds._rng)
        if stream != expected_stream:
            raise RuntimeError("final data-stream state does not match replay")
        if set(C.OPENED["labels"]) - {C.potsdam_tile_id(n) for n in train_files}:
            raise RuntimeError("non-training label opened")
        mon.halt = True
        mon.join()
        res = {"status": "trained_unverified", "entry": entry, "manifest_sha256": C.sha256_file(mpath),
               "pre_run_checks": pre,
               "post_run_checks": {"backbone_fp": fp_after, "data_stream_final": stream, "data_stream_ok": True, "steps": state["opt_steps"],
                                   "tiles_opened": sorted(C.OPENED["images"]), "labels_opened": sorted(C.OPENED["labels"]), "snapped_labels": C.SNAPPED},
               "checkpoint": {"path": final_ckpt.name, "sha256": C.sha256_file(final_ckpt), "size": final_ckpt.stat().st_size, "step": state["opt_steps"],
                              "trainable_hash": R.trainable_hash(model), "probe_logits_hash": M.tensor_hash([pl]),
                              "probe_logits_file_sha256": C.sha256_file(out / "probe_logits.npy")},
               "parameter_counts": {"total": total_params, "trainable": n_train, "decoder": dec, "lora": lo},
               "loss_history": losses,
               "timing": {"training_seconds": loop_s, "process_seconds": time.time() - t_start, "startup_seconds": t_loop - t_start},
               "memory": C.memory_record(mon), "env": {"torch": torch.__version__}}
        C.write_json_atomic(out / "result.json", res)
        (out / "IN_PROGRESS").unlink()
        print(f"[done] {a.run_id} train={loop_s:.0f}s peak={res['memory']['kernel_lifetime_max_footprint_mb']:.0f}MB "
              f"swapgrow={mon.max['swap_growth_mb']:.0f}MB final_loss={losses[-1]['train_loss']:.4f}", flush=True)
    except BaseException as ex:
        C.write_json_atomic(out / "incident.json", {"error": repr(ex), "traceback": traceback.format_exc(), "time": time.time(), "elapsed_s": time.time() - t_start,
                                                    "optimizer_steps_completed": state["opt_steps"], "batches_drawn": state["batches"], "stage": state["stage"],
                                                    "memory_final": C.rusage(), "swap_used_mb": C.swap_used_mb(), "swap_at_start_mb": mon.swap0,
                                                    "pressure": C.pressure_level(), "sampled_max": mon.max, "telemetry_tail": mon.tail,
                                                    "tiles_opened": sorted(C.OPENED["images"]), "labels_opened": sorted(C.OPENED["labels"])})
        mon.halt = True
        print(f"[incident] {ex!r} at optimizer step {state['opt_steps']} stage {state['stage']}", flush=True)
        raise


if __name__ == "__main__":
    main()
