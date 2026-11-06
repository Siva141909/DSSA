"""Runs the 10 runs of manifest v3 in manifest order, then stops. No retry logic:
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
STATUS = C.ART / "pilot_status_v3.json"


def stop(msg):
    print(f"[PILOT STOPPED] {msg}", flush=True)
    C.write_json_atomic(STATUS, {"state": "stopped", "reason": msg, "time": time.time()})
    sys.exit(1)


def main():
    m = json.load(open(C.ART / "manifest_pilot_v3.json"))
    assert len(m["runs"]) == 10
    done = []
    for i, e in enumerate(m["runs"], 1):
        rid = e["run_id"]
        if (C.RUNS / rid).exists():
            stop(f"{rid}: destination already exists; never overwritten")
        C.write_json_atomic(STATUS, {"state": "running", "current": rid, "completed": done, "time": time.time()})
        print(f"[pilot] {i}/10 {rid} est {e['est_seconds']/60:.1f} min", flush=True)
        with open(C.ART / "logs" / f"{rid}.log", "w") as lf:
            if subprocess.run([sys.executable, "-B", str(C.CODE / "run_one_v3.py"), rid], stdout=lf, stderr=subprocess.STDOUT).returncode:
                stop(f"{rid}: run failed; see runs/{rid}/incident.json")
            if subprocess.run([sys.executable, "-B", str(C.CODE / "verify_reload.py"), rid], stdout=lf, stderr=subprocess.STDOUT).returncode:
                stop(f"{rid}: reload verification failed")
        try:
            C.assert_frozen_unchanged()
        except RuntimeError as ex:
            stop(str(ex))
        done.append(rid)
        print(open(C.ART / "logs" / f"{rid}.log").read().split("[done]")[-1].split("\n")[0], flush=True)
    C.write_json_atomic(STATUS, {"state": "complete_10_of_10", "completed": done, "time": time.time()})
    print("[PILOT COMPLETE] 10 of 10. Authorization ends here.", flush=True)


if __name__ == "__main__":
    main()
