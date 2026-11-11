"""Writes Stage D manifest v4. Never overwrites. Approved by the user 2026-11-11.

p3d_RAND3d09_s9000 was stopped at optimizer step 1835 by the 1.5x runtime guard (2402 s): for
its first 28 minutes it trained at about a quarter of the normal speed (no thermal warning, no
sleep, no swap growth, memory under the limits), most likely GPU contention from another
application. Its folder is preserved untouched and recorded under interrupted_runs; the run is
redone from scratch as p3d_RAND3d09_s9000_r1 with the identical configuration, in the same
position. At the user's request the training runtime limit is raised from 1.5x to 2.5x
est_seconds for the remaining runs (manifest field runtime_factor). Every other entry and every
other guard is unchanged, including the 300 s no-optimizer-step stall guard."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import p3common as C  # noqa: E402

C.install_guards()

OLD, NEW = "p3d_RAND3d09_s9000", "p3d_RAND3d09_s9000_r1"
RUNTIME_FACTOR = 2.5


def main():
    if C.MANIFEST_D.exists():
        raise FileExistsError(C.MANIFEST_D)
    v3 = json.load(open(C.MANIFEST_D_V3))
    folder = C.RUNS / OLD
    inc = json.load(open(folder / "incident.json"))
    if (folder / "summary.json").exists() or "runtime above" not in inc.get("error", ""):
        raise RuntimeError("unexpected state of the interrupted run")
    runs = []
    for e in v3["runs"]:
        e = dict(e)
        if e["run_id"] == OLD:
            e["run_id"] = NEW
            e["restart_of"] = OLD
            e["config_hash"] = C.config_hash(e)
        runs.append(e)
    assert sum(e["run_id"] == NEW for e in runs) == 1 and len(runs) == 67
    m = dict(v3)
    interrupted = dict(v3["interrupted_runs"])
    interrupted[OLD] = {
        "files": {p.name: C.sha256_file(p) for p in sorted(folder.iterdir()) if p.is_file()},
        "error": inc.get("error"), "cause": "1.5x runtime guard; about 4x slower than normal for the first 28 min (likely GPU contention from another application)",
        "stage": inc.get("stage"), "optimizer_steps_completed": inc.get("optimizer_steps_completed"),
        "preserved": "never overwritten or reused"}
    m.update({"version": 4, "created": time.time(), "runs": runs, "runtime_factor": RUNTIME_FACTOR,
              "previous_manifest_sha256": C.sha256_file(C.MANIFEST_D_V3),
              "completed_before_v4": [e["run_id"] for e in v3["runs"] if (C.RUNS / e["run_id"] / "summary.json").exists()],
              "authorization_v4": "Approved by the user 2026-11-11 after the runtime stop: 'yeah start again will please increase the limit'. "
                                  "Restart p3d_RAND3d09_s9000 as p3d_RAND3d09_s9000_r1, raise the runtime limit to 2.5x, resume.",
              "code_hash": C.code_hash(), "interrupted_runs": interrupted})
    m["limits"] = dict(m["limits"], runtime=f"{RUNTIME_FACTOR} x est_seconds (training); 1.5x up to v3")
    C.write_json_atomic(C.MANIFEST_D, m)
    print("Stage D manifest v4", C.sha256_file(C.MANIFEST_D), len(m["completed_before_v4"]), "completed")


if __name__ == "__main__":
    main()
