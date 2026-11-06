"""Runs the 63 runs of manifest v4 in manifest order, then stops. No retry logic:
any failure stops the whole sequence and is left for the research lead."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

C.install_guards()
STATUS = C.ART / "gate2_status_v4.json"


def stop(msg, done):
    print(f"[GATE 2 STOPPED] {msg}", flush=True)
    C.write_json_atomic(STATUS, {"state": "stopped", "reason": msg, "completed": done, "time": time.time()})
    sys.exit(1)


def main():
    m = json.load(open(C.ART / "manifest_gate2_v4.json"))
    assert len(m["runs"]) == 63
    done = []
    for i, e in enumerate(m["runs"], 1):
        rid = e["run_id"]
        if (C.RUNS / rid).exists():
            stop(f"{rid}: destination already exists; never overwritten", done)
        C.write_json_atomic(STATUS, {"state": "running", "current": rid, "index": i, "completed": done, "time": time.time()})
        print(f"[gate2] {i}/63 {rid} est {e['est_seconds']/60:.1f} min", flush=True)
        with open(C.ART / "logs" / f"{rid}.log", "w") as lf:
            if subprocess.run([sys.executable, "-B", str(C.CODE / "run_one_v4.py"), rid], stdout=lf, stderr=subprocess.STDOUT).returncode:
                stop(f"{rid}: run failed; see runs/{rid}/incident.json", done)
            if subprocess.run([sys.executable, "-B", str(C.CODE / "verify_reload.py"), rid], stdout=lf, stderr=subprocess.STDOUT).returncode:
                stop(f"{rid}: reload verification failed", done)
        try:
            C.assert_frozen_unchanged()
        except RuntimeError as ex:
            stop(str(ex), done)
        done.append(rid)
        print(open(C.ART / "logs" / f"{rid}.log").read().split("[done]")[-1].split("\n")[0], flush=True)
    C.write_json_atomic(STATUS, {"state": "complete_63_of_63", "completed": done, "time": time.time()})
    print("[GATE 2 COMPLETE] 63 of 63. Authorization ends here.", flush=True)


if __name__ == "__main__":
    main()
