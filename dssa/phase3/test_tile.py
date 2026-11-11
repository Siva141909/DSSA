"""Potsdam test opening (approved by the user 2026-11-11 after Stage D; protocol v2 section 9 and
v3 section 9): one test tile, one fresh process, exactly as eval_tile.py evaluates a validation
tile (same checkpoint checks, same p3eval evaluator, same guards). The model and its checkpoint
SHA-256 must be listed in the frozen test manifest, and only this one test tile is allowed in
this process. Writes artifacts/phase3/test_potsdam/<run_id>/<tile>.json; never overwrites."""
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
from checkpoint import load_checkpoint  # noqa: E402
import p3models as P3  # noqa: E402
import p3eval as P  # noqa: E402
import p3run as R  # noqa: E402

TEST_MANIFEST = C.ART / "test_potsdam" / "test_manifest.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_id")
    ap.add_argument("tile")
    a = ap.parse_args()
    t0 = time.time()
    tm = json.load(open(TEST_MANIFEST))
    if C.sha256_file(TEST_MANIFEST) != (TEST_MANIFEST.parent / "test_manifest.sha256").read_text().split()[0]:
        raise RuntimeError("test manifest hash mismatch")
    if C.code_hash() != tm["code_hash"]:
        raise RuntimeError("Phase 3 code differs from the test manifest")
    s = C.split()
    if a.tile not in s["test"] or a.tile not in tm["tiles"]:
        raise PermissionError(f"not a frozen Potsdam test tile: {a.tile}")
    model_rec = next(m for m in tm["models"] if m["run_id"] == a.run_id)
    tid = C.potsdam_tile_id(a.tile)
    d = C.RUNS / a.run_id
    ev = C.ART / "test_potsdam" / a.run_id
    ev.mkdir(parents=True, exist_ok=True)
    outp = ev / f"{tid}.json"
    if outp.exists():
        raise FileExistsError(outp)
    state = {"stage": "startup", "opt_steps": 2000}
    mon = C.Telemetry(None, state, ev, dt=0.25)
    mon.start()
    try:
        res = json.load(open(d / "result.json"))
        if not json.load(open(d / "reload_check.json"))["pass"]:
            raise RuntimeError("reload check did not pass")
        e, ck = res["entry"], res["checkpoint"]
        p = d / ck["path"]
        sha = C.sha256_file(p)
        if sha != ck["sha256"] or sha != model_rec["checkpoint_sha256"]:
            raise RuntimeError("checkpoint SHA-256 differs from the run record or the test manifest")
        state["stage"] = "build"
        model, mods = P3.build(sorted(e["layer_indices"]), "mps", e["lora_init_seed"], e.get("rank", 8))
        load_checkpoint(p, model, mods, sorted(e["layer_indices"]))
        if R.trainable_hash(model) != ck["trainable_hash"]:
            raise RuntimeError("trainable hash mismatch after load")
        t_model = time.time() - t0
        state["stage"] = "read"
        C.TEST_ALLOW.add(tid)
        C.LABEL_ALLOW.add(tid)
        t = time.time()
        img = C.potsdam_image(a.tile)
        lab = C.potsdam_label(a.tile).astype(np.int64)
        if img.shape[:2] != lab.shape:
            raise RuntimeError("image/label shape mismatch")
        co = R.transform()
        t_io = time.time() - t
        state["stage"] = "eval"
        if mon.fault:
            raise RuntimeError(f"STOP: {mon.fault}")
        t = time.time()
        cm, ce = P.eval_tile_u8(model, img, co, lab, "mps")
        del img
        torch.mps.synchronize()
        t_eval = time.time() - t
        if mon.fault:
            raise RuntimeError(f"STOP: {mon.fault}")
        if not np.isfinite(ce) or cm.sum() != lab.size:
            raise RuntimeError("non-finite CE or pixel count mismatch")
        mon.halt = True
        mon.join()
        out = {"run_id": a.run_id, "tile": a.tile, "split": "test", "evaluator": "p3eval.eval_tile_u8", "checkpoint_sha256": sha,
               "confusion_matrix": cm.tolist(), "ce_sum": ce, "pixels": int(lab.size), "snapped_label": C.SNAPPED.get(tid),
               "timing": {"model_s": t_model, "io_s": t_io, "eval_s": t_eval, "process_s": time.time() - t0},
               "memory": C.memory_record(mon), "labels_opened": sorted(C.OPENED["labels"]), "images_opened": sorted(C.OPENED["images"])}
        if out["labels_opened"] != [tid] or out["images_opened"] != [tid]:
            raise RuntimeError("more than the one allowed tile was opened")
        C.write_json_atomic(outp, out)
        print(f"[test] {a.run_id} {a.tile} eval={t_eval:.1f}s total={time.time() - t0:.1f}s peak={out['memory']['kernel_lifetime_max_footprint_mb']:.0f}MB", flush=True)
    except BaseException as ex:
        C.write_json_atomic(ev / f"{tid}_incident.json", {"error": repr(ex), "traceback": traceback.format_exc(), "stage": state["stage"],
                                                          "memory_final": C.rusage(), "sampled_max": mon.max, "telemetry_tail": mon.tail[-40:]})
        mon.halt = True
        raise


if __name__ == "__main__":
    main()
