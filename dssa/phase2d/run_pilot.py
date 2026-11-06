"""Runs the 12 approved pilot runs in manifest order, then stops. There is no
option to run anything else: the manifest contains only these 12 entries."""
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
PY = sys.executable


def stop(msg):
    print(f"[PILOT STOPPED] {msg}", flush=True)
    C.write_json_atomic(C.ART / "pilot_status.json", {"state": "stopped", "reason": msg, "time": time.time()})
    sys.exit(1)


def main():
    m = json.load(open(C.MANIFEST))
    assert len(m["runs"]) == 12
    done = []
    for e in m["runs"]:
        rid = e["run_id"]
        res = C.RUNS / rid / "result.json"
        if res.exists() and json.load(open(res)).get("status") == "completed":
            done.append(rid)
            continue
        if (C.RUNS / rid).exists():
            stop(f"{rid}: incomplete destination exists; never overwritten")
        C.write_json_atomic(C.ART / "pilot_status.json", {"state": "running", "current": rid, "completed": done, "time": time.time()})
        print(f"[pilot] {len(done)+1}/12 {rid} est {e['est_seconds']/60:.1f} min", flush=True)
        with open(C.ART / "logs" / f"{rid}.log", "w") as lf:
            if subprocess.run([PY, "-B", str(C.CODE / "run_one.py"), rid], stdout=lf, stderr=subprocess.STDOUT).returncode:
                stop(f"{rid}: run_one failed; see logs/{rid}.log")
            if subprocess.run([PY, "-B", str(C.CODE / "verify_reload.py"), rid], stdout=lf, stderr=subprocess.STDOUT).returncode:
                stop(f"{rid}: reload verification failed")
        try:
            C.assert_frozen_unchanged()
        except RuntimeError as ex:
            stop(str(ex))
        done.append(rid)
        print(open(C.ART / "logs" / f"{rid}.log").read().split("[done]")[-1].split("\n")[0], flush=True)
    C.write_json_atomic(C.ART / "pilot_status.json", {"state": "complete_12_of_12", "completed": done, "time": time.time()})
    print("[PILOT COMPLETE] 12 of 12. Authorization ends here.", flush=True)


if __name__ == "__main__":
    main()
