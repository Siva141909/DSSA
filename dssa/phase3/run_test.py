"""Potsdam test opening runner (approved by the user 2026-11-11 after Stage D). For each of the
70 frozen models and each of the 10 frozen test tiles: one test_tile.py process under the
Stage D guards of run_sequence.py (sleep, battery floor, thermal, critical pressure, 400 s
watchdog, SIGINT on a hazard, no retry; any failure stops), a preflight before every model, and
the 10.5 GB per-process stop rule. Resume continues the same single opening: completed tile
files are kept, a tile with an incident stops the runner. After the last tile it runs the
frozen test_analysis.py."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import p3common as C  # noqa: E402
import run_sequence as RS  # noqa: E402

TDIR = C.ART / "test_potsdam"


def main():
    import sigsafe
    sigsafe.restore()
    RS.BATTERY_MODE["on"] = True
    tm_path = TDIR / "test_manifest.json"
    tm = json.load(open(tm_path))
    if C.sha256_file(tm_path) != (TDIR / "test_manifest.sha256").read_text().split()[0]:
        raise SystemExit("test manifest hash mismatch")
    if C.code_hash() != tm["code_hash"] or C.sha256_file(C.CODE / "test_analysis.py") != tm["test_analysis_sha256"]:
        raise SystemExit("Phase 3 code or analysis differs from the test manifest")
    RS.log_guard({"stage": "test opening start", "models": len(tm["models"]), "tiles": len(tm["tiles"])})
    done = []
    try:
        incidents = sorted(str(p) for p in TDIR.glob("*/*_incident.json")) + sorted(str(p) for p in TDIR.glob("*/abort.json"))
        if incidents:
            RS.stop(f"test opening has unresolved incidents: {incidents}", done)
        n = len(tm["models"])
        for i, m in enumerate(tm["models"], 1):
            rid = m["run_id"]
            todo = [t for t in tm["tiles"] if not (TDIR / rid / f"{C.potsdam_tile_id(t)}.json").exists()]
            if not todo:
                done.append(rid)
                continue
            checks, info = RS.preflight()
            RS.log_guard({"run": rid, "stage": "test preflight", "checks": checks, **info})
            if not all(checks.values()):
                RS.stop(f"preflight failed before test of {rid}: {[k for k, v in checks.items() if not v]}", done, rid)
            C.write_json_atomic(RS.STATUS, {"state": "test_running", "current": rid, "index": i, "of": n, "time": time.time()})
            print(f"[test] {i}/{n} {rid} ({len(todo)} tiles)", flush=True)
            with open(C.LOGS / f"test_{rid}.log", "a") as lf:
                for t in todo:
                    tid = C.potsdam_tile_id(t)
                    rc, hz, _ = RS.run_guarded([RS.PY, "-B", str(C.CODE / "test_tile.py"), rid, t], lf, rid, f"test {tid}", RS.EVAL_HANG_S)
                    if (TDIR / rid / "abort.json").exists():
                        RS.stop(f"{rid}: test of {t} hit the 11.0 GB early abort", done, rid)
                    if hz or rc:
                        RS.stop(f"{rid}: test of {t} {'interrupted: ' + hz if hz else 'failed'}", done, rid)
                    RS.check_memory(rid, f"test process {tid}", RS.peak_of(TDIR / rid / f"{tid}.json"), done)
            done.append(rid)
    except (KeyboardInterrupt, sigsafe.Terminated) as ex:
        RS.stop(f"test runner received {'SIGINT' if isinstance(ex, KeyboardInterrupt) else 'SIGTERM'} (manual stop)", done)
    print(f"[TEST OPENING COMPLETE] {len(done)} models x {len(tm['tiles'])} tiles", flush=True)
    C.write_json_atomic(RS.STATUS, {"state": "complete_test", "completed": len(done), "time": time.time()})
    subprocess.run([RS.PY, "-B", str(C.CODE / "test_analysis.py")], check=True)


if __name__ == "__main__":
    main()
