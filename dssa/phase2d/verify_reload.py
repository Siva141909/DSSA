"""Post-run check in a fresh process: every saved checkpoint must reproduce its
stored confusion matrix on one validation tile. Records checkpoint hashes."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

C.install_guards()
sys.path.insert(0, str(C.ROOT / "train"))
import numpy as np  # noqa: E402
import torch  # noqa: E402
import dataset as ds_mod  # noqa: E402
import train as T  # noqa: E402,F401
from checkpoint import load_checkpoint  # noqa: E402
import models as M  # noqa: E402
import evaluation as E  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_id")
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    d = (C.GATE0 / "smoke" / a.run_id) if a.smoke else (C.RUNS / a.run_id)
    res = json.load(open(d / "result.json"))
    C.install_tile_allowlist(ds_mod, set())
    layers = res["entry"]["layer_indices"]
    tile = C.VAL[-1]
    ds = ds_mod.TargetSegDataset([tile], mode="eval", eval_max_size=448 if a.smoke else None)
    by_step = {e["step"]: e for e in res["evals"]}
    out = {}
    for tag, step in (("best", res["train_result"]["best_step"]), ("final", res["post_run_checks"]["steps"])):
        p = d / f"{a.run_id}_{tag}.pt"
        model, mods = M.build(layers, "mps", res["entry"]["lora_init_seed"])
        payload = load_checkpoint(p, model, mods, sorted(layers))
        if payload["step"] != step:
            raise RuntimeError(f"{tag}: checkpoint step {payload['step']} != {step}")
        cal, lab, fn = ds[0]
        _, cm, _ = E.eval_tile(model, cal, lab, "mps")
        diff = int(np.abs(cm - np.array(by_step[step]["tiles"][fn])).sum())
        if diff:
            raise RuntimeError(f"{tag}: reload changed {diff} matrix cells")
        out[tag] = {"sha256": C.sha256_file(p), "step": step, "cm_diff": diff, "size": p.stat().st_size}
        del model, mods
        torch.mps.empty_cache()
    out["result_sha256_before_verify"] = C.sha256_file(d / "result.json")
    res["status"] = "completed"
    res["reload_verification"] = out
    C.write_json_atomic(d / "result.json", res)
    C.write_json_atomic(d / "hashes.json", {"checkpoints": out, "result_sha256": C.sha256_file(d / "result.json")})
    print("[reload ok]", a.run_id)


if __name__ == "__main__":
    main()
