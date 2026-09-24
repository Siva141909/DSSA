"""
DSSA Phase 2C - resumable full-matrix runner.

Executes the pre-registered unique-run matrix, built ONLY from
dssa/config/phase2b_training_protocol.json via manifest.py (never
hand-reconstructed), using the exact frozen protocol - train.py's
run_training() is called with NO overrides, so every run uses the real
2000 steps, checkpoint/validate every 200 steps, all 5 target-validation
files, warmup 100 steps, batch size 8, etc.

Resumable: each run's result is persisted to
dssa/artifacts/phase2c/runs/<run_id>/result.json only after that run fully
completes. A restart skips a run ONLY if result.json has status="completed"
AND its config_hash matches the current (run_id, K, layer_indices,
training_seed, protocol-file-hash) - so a stale or partial result is never
treated as valid. An IN_PROGRESS marker file is written at run start and
removed only on successful completion; a crash mid-run leaves it in place,
which is never read as completion evidence (the completion check only looks
at result.json's status field).

--max-new-runs N stops after N new (not-already-completed) runs finish in
this invocation - used for staged review batches. It changes nothing about
which runs exist, their order, or their per-run protocol; it only pauses
execution between runs, in between which nothing scientific happens.

target-test is never referenced anywhere in this file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import manifest as manifest_mod  # noqa: E402
import train as train_mod  # noqa: E402
from model_wrapper import build_model  # noqa: E402
from efficiency import hardware_info  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR = ROOT / "artifacts" / "phase2c" / "runs"
RUNS_DIR.mkdir(parents=True, exist_ok=True)


def protocol_file_hash() -> str:
    with open(manifest_mod.CONFIG_PATH, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def run_config_hash(run: dict, proto_hash: str) -> str:
    payload = {
        "run_id": run["run_id"], "K": run["K"], "layer_indices": run["layer_indices"],
        "training_seed": run["training_seed"], "condition_labels": run["condition_labels"],
        "protocol_file_hash": proto_hash,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def run_dir_for(run_id: str) -> Path:
    d = RUNS_DIR / run_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def load_existing_result(run_id: str) -> dict | None:
    p = run_dir_for(run_id) / "result.json"
    if not p.exists():
        return None
    try:
        with open(p) as f:
            return json.load(f)
    except Exception:
        return None


def is_valid_completed(existing: dict | None, expected_hash: str) -> bool:
    return bool(existing) and existing.get("status") == "completed" and existing.get("config_hash") == expected_hash


def backbone_fingerprint(model) -> str:
    """SHA-256 over a handful of frozen (never LoRA-wrapped, never trained)
    backbone tensors - patch_embed and two blocks' mlp/norm weights. Used to
    verify the frozen backbone's actual VALUES (not just requires_grad flags)
    never drift during a run, independent of and in addition to the
    requires_grad-based isolation check already performed inside
    train.run_training() via lora.assert_only_intended_trainable()."""
    h = hashlib.sha256()
    with torch.no_grad():
        h.update(model.encoder.patch_embed.proj.weight.detach().cpu().numpy().tobytes())
        h.update(model.encoder.blocks[0].mlp.fc1.weight.detach().cpu().numpy().tobytes())
        h.update(model.encoder.blocks[12].norm1.weight.detach().cpu().numpy().tobytes())
        h.update(model.encoder.blocks[23].mlp.fc2.bias.detach().cpu().numpy().tobytes())
    return h.hexdigest()


def execute_one_run(run: dict, device: str, log) -> tuple[dict, str]:
    rdir = run_dir_for(run["run_id"])
    inprogress_path = rdir / "IN_PROGRESS"
    inprogress_path.write_text(json.dumps({"started_at": time.time(), "run_id": run["run_id"]}))

    run_spec = {
        "run_id": run["run_id"], "K": run["K"], "layer_indices": run["layer_indices"],
        "condition_labels": run["condition_labels"], "training_seed": run["training_seed"],
    }

    t_wall0 = time.time()
    # NO overrides passed here: total_steps/checkpoint_every/warmup_steps/
    # val_files_override/eval_max_size all stay at train.py's frozen defaults
    # (2000 / 200 / 100 / None(=all 5 val files) / None(=full image size)).
    train_result, model, lora_modules = train_mod.run_training(
        run_spec, device=device, out_dir=rdir, preflight=False, log=log,
    )
    fp_after = backbone_fingerprint(model)
    del model, lora_modules

    result = {
        "status": "completed",
        "run": run,
        "train_result": train_result,
        "backbone_fingerprint_after_training": fp_after,
        "wall_clock_total_seconds": time.time() - t_wall0,
        "hardware": hardware_info(),
        "completed_at": time.time(),
    }
    inprogress_path.unlink(missing_ok=True)
    return result, str(rdir / "result.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-new-runs", type=int, default=None)
    args = ap.parse_args()

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    proto_hash = protocol_file_hash()

    m = manifest_mod.build_manifest()
    assert m["total_condition_slots"] == m["expected_total_condition_slots"] == 42
    assert m["unique_training_runs"] == m["expected_unique_training_runs"] == 39
    runs = m["runs"]

    print(f"[matrix] device={device} protocol_hash={proto_hash[:12]}... total_unique_runs={len(runs)}")
    print("[matrix] === full frozen matrix (from phase2b_training_protocol.json) ===")
    for r in runs:
        tag = " (COLLISION - trained once, shared by all listed labels)" if r["is_collision"] else ""
        print(f"  {r['run_id']:35s} K={r['K']:2d} layers={r['layer_indices']} labels={r['condition_labels']} seed={r['training_seed']}{tag}")
    print("[matrix] === end matrix ===\n")

    baseline_model, _ = build_model([], device=device)
    baseline_fp = backbone_fingerprint(baseline_model)
    del baseline_model
    print(f"[matrix] frozen-backbone baseline fingerprint: {baseline_fp[:16]}...\n")

    n_new_completed = 0
    for run in runs:
        expected_hash = run_config_hash(run, proto_hash)
        existing = load_existing_result(run["run_id"])
        if is_valid_completed(existing, expected_hash):
            print(f"[skip] {run['run_id']} already completed (config hash matches) - "
                  f"best_val_mIoU={existing['train_result']['best_val_mean_iou']:.4f}")
            continue

        if args.max_new_runs is not None and n_new_completed >= args.max_new_runs:
            print(f"[matrix] reached --max-new-runs={args.max_new_runs}; stopping before starting {run['run_id']}")
            break

        print(f"\n[run] starting {run['run_id']} K={run['K']} layers={run['layer_indices']} labels={run['condition_labels']}")
        result, result_path = execute_one_run(run, device, log=print)
        result["config_hash"] = expected_hash
        result["backbone_unchanged"] = (result["backbone_fingerprint_after_training"] == baseline_fp)
        if not result["backbone_unchanged"]:
            print(f"[WARNING] backbone fingerprint changed for {run['run_id']}! "
                  f"expected {baseline_fp[:16]} got {result['backbone_fingerprint_after_training'][:16]}")
        with open(result_path, "w") as f:
            json.dump(result, f, indent=2, default=str)
        n_new_completed += 1
        tr = result["train_result"]
        print(f"[done] {run['run_id']}: best_val_mIoU={tr['best_val_mean_iou']:.4f} "
              f"best_step={tr['best_step']} wall_clock={result['wall_clock_total_seconds']:.1f}s "
              f"backbone_unchanged={result['backbone_unchanged']}")

    print(f"\n[matrix] session complete: {n_new_completed} new run(s) completed this invocation.")


if __name__ == "__main__":
    main()
