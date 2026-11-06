"""Written before the 10 v3 runs. The frozen pilot_analysis.py, with one mapping:
Layer 0 seed 1000 is run p2d_oracle_L00_s1000_a3 (the two failed attempts produced
no results). Then per-class differences, which the v3 deliverable adds."""
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pilot_analysis as P  # noqa: E402

C, np = P.C, P.np
_rid = P.rid
P.rid = lambda a, s: "p2d_oracle_L00_s1000_a3" if (a, s) == ("L00", 1000) else _rid(a, s)


def per_class():
    out = {}
    for s in P.SEEDS:
        res = {a: json.load(open(C.RUNS / P.rid(a, s) / "result.json")) for a in P.ARMS}

        def iou(a, ev):
            c = P.stack(res[a]["evals"][ev]).sum(0)
            tp, d = np.diag(c), c.sum(0) + c.sum(1) - np.diag(c)
            return np.where(d > 0, tp / np.maximum(d, 1), np.nan)
        base = iou("K0", -1)
        out[str(s)] = {"K0_iou": base.tolist(), **{a: {"iou": iou(a, -1).tolist(), "diff_vs_K0": (iou(a, -1) - base).tolist()} for a in P.ARMS[1:]}}
    C.write_json_atomic(C.ART / "pilot_per_class_v3.json", out)


if __name__ == "__main__":
    P.main()
    per_class()
