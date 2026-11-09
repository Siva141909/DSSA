"""Reload verification in a fresh process: the saved step-2000 checkpoint must have the
recorded SHA-256, rebuild to the recorded trainable-parameter hash, and reproduce the
probe logits written by the training process. No tile is read."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import p3common as C  # noqa: E402

C.install_guards()
C.setup_paths()
import sigsafe  # noqa: E402

sigsafe.restore()
import numpy as np  # noqa: E402
from checkpoint import load_checkpoint  # noqa: E402
import models as M  # noqa: E402
import p3models as P  # noqa: E402
import p3run as R  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_id")
    a = ap.parse_args()
    t0 = time.time()
    d = C.RUNS / a.run_id
    res = json.load(open(d / "result.json"))
    e, ck = res["entry"], res["checkpoint"]
    p = d / ck["path"]
    sha = C.sha256_file(p)
    if sha != ck["sha256"]:
        raise RuntimeError("checkpoint SHA-256 changed")
    model, mods = P.build(sorted(e["layer_indices"]), "mps", e["lora_init_seed"], e.get("rank", 8))
    payload = load_checkpoint(p, model, mods, sorted(e["layer_indices"]))
    if payload["step"] != 2000:
        raise RuntimeError(f"checkpoint step {payload['step']}")
    th = R.trainable_hash(model)
    pl = R.probe_logits(model).numpy()
    ref = np.load(d / "probe_logits.npy")
    exact = M.tensor_hash([R.probe_logits(model)]) == ck["probe_logits_hash"]
    diff = float(np.abs(pl - ref).max())
    ok = th == ck["trainable_hash"] and (exact or diff <= 1e-5)
    out = {"run_id": a.run_id, "checkpoint_sha256": sha, "trainable_hash_match": th == ck["trainable_hash"], "probe_logits_exact": exact,
           "probe_logits_max_abs_diff": diff, "pass": ok, "seconds": time.time() - t0, "peak_mb": C.rusage()["lifetime_max_phys_footprint_mb"]}
    C.write_json_atomic(d / "reload_check.json", out)
    print("[reload]", json.dumps(out), flush=True)
    if not ok:
        raise RuntimeError("reload verification failed")


if __name__ == "__main__":
    main()
