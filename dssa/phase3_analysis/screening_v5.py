"""Runs the frozen screening.py unchanged against the manifest v5 run IDs.

screening.py reads runs/<p3_Lxx_sNNNN>/summary.json. Three runs were stopped by guards and
rerun under new IDs (manifest v3: p3_L00_s1000 -> _r1; v4: p3_L06_s2000 -> _r1;
v5: p3_L10_s3000 -> _r1). This wrapper only redirects those three summary paths to the
rerun that manifest v5 lists; the interrupted folders have no summary.json and are never
read. Same approach as phase2d gate2_analysis_v12.py."""
from __future__ import annotations

import builtins
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import screening as S  # noqa: E402

MANIFEST = S.ART / "manifest_stage_c_v5.json"


def aliases():
    m = json.load(open(MANIFEST))
    ids = {e["run_id"] for e in m["runs"]}
    out = {}
    for old in m["interrupted_runs"]:
        new = old + "_r1"
        if new not in ids or old in ids:
            raise RuntimeError(f"manifest v5 does not map {old} to {new}")
        e = next(e for e in m["runs"] if e["run_id"] == new)
        summ = json.load(open(S.ART / "runs" / new / "summary.json"))
        if summ.get("run_id", new) != new:
            raise RuntimeError(f"{new} summary has run_id {summ.get('run_id')}")
        if (S.ART / "runs" / old / "summary.json").exists():
            raise RuntimeError(f"interrupted run {old} unexpectedly has a summary")
        out[old] = new
    return out


ALIAS = aliases()


def _open(path, *a, **k):
    p = Path(path)
    if p.name == "summary.json" and p.parent.name in ALIAS:
        p = p.parent.with_name(ALIAS[p.parent.name]) / "summary.json"
    return builtins.open(p, *a, **k)


S.open = _open  # module-global lookup takes precedence over the builtin

if __name__ == "__main__":
    print("aliases:", ALIAS, file=sys.stderr)
    sys.exit(S.main())
