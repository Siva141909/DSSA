"""One fresh process: re-evaluates one completed K0 tile evaluation with p3eval.eval_tile_u8
and compares it with the stored result of the original evaluator (exact confusion matrix;
CE to relative 1e-6). Writes artifacts/phase3/eval_v2_verification/<run>_<tile>.json."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import p3common as C  # noqa: E402

C.install_guards()
C.setup_paths()
import numpy as np  # noqa: E402
from checkpoint import load_checkpoint  # noqa: E402
import models as M  # noqa: E402
import p3eval as P  # noqa: E402
import p3run as R  # noqa: E402


def main():
    rid, tile = sys.argv[1], sys.argv[2]
    t0 = time.time()
    tid = C.potsdam_tile_id(tile)
    out = C.ART / "eval_v2_verification" / f"{rid}_{tid}.json"
    out.parent.mkdir(exist_ok=True)
    if out.exists():
        raise FileExistsError(out)
    if tile not in C.split()["validation"] or "_K0_" not in rid:
        raise PermissionError("verification is limited to completed K0 validation evaluations")
    d = C.RUNS / rid
    old = json.load(open(d / "eval" / f"{tid}.json"))
    state = {"stage": "verify"}
    mon = C.Telemetry(None, state, out.parent)
    mon.start()
    res = json.load(open(d / "result.json"))
    e = res["entry"]
    model, mods = M.build(sorted(e["layer_indices"]), "mps", e["lora_init_seed"])
    load_checkpoint(d / res["checkpoint"]["path"], model, mods, sorted(e["layer_indices"]))
    C.LABEL_ALLOW.add(tid)
    img = C.potsdam_image(tile)
    lab = C.potsdam_label(tile).astype(np.int64)
    t = time.time()
    cm, ce = P.eval_tile_u8(model, img, R.transform(), lab, "mps")
    t_eval = time.time() - t
    if mon.fault:
        raise RuntimeError(f"STOP: {mon.fault}")
    mon.halt = True
    diff = int(np.abs(cm - np.array(old["confusion_matrix"])).sum())
    rel = abs(ce - old["ce_sum"]) / abs(old["ce_sum"])
    rec = {"run_id": rid, "tile": tile, "cm_cells_differing_total": diff, "ce_rel_diff": rel, "pass": diff == 0 and rel <= 1e-6,
           "new_peak_mb": C.rusage()["lifetime_max_phys_footprint_mb"], "old_peak_mb": old["memory"]["kernel_lifetime_max_footprint_mb"],
           "eval_s": t_eval, "process_s": time.time() - t0, "memory": C.memory_record(mon)}
    C.write_json_atomic(out, rec)
    print(f"[verify] {rid} {tid} cm_diff={diff} ce_rel={rel:.2e} peak {rec['new_peak_mb']:.0f} MB (was {rec['old_peak_mb']:.0f}) pass={rec['pass']}", flush=True)
    if not rec["pass"]:
        sys.exit(2)


if __name__ == "__main__":
    main()
