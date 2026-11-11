"""Writes Stage D manifest v2. Never overwrites. Approved by the user 2026-11-09.

p3d_PRIOR3_s1000 was stopped at optimizer step 1556 by the sleep guard (Clamshell Sleep on
battery at 22:35:43, 577 s suspended). Its folder is preserved untouched and recorded under
interrupted_runs; the run is redone from scratch as p3d_PRIOR3_s1000_r1 with the identical
configuration, in the same position. Every other entry is copied from v1 unchanged. System sleep
is disabled for the remainder (sudo pmset -a disablesleep 1, run by the user) so the lid can be
closed on battery; all guards are unchanged, including the sleep guard."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import p3common as C  # noqa: E402

C.install_guards()

OLD, NEW = "p3d_PRIOR3_s1000", "p3d_PRIOR3_s1000_r1"


def main():
    if C.MANIFEST_D.exists():
        raise FileExistsError(C.MANIFEST_D)
    v1 = json.load(open(C.MANIFEST_D_V1))
    folder = C.RUNS / OLD
    inc = json.load(open(folder / "incident.json"))
    if (folder / "summary.json").exists() or "sleep" not in json.dumps(inc).lower() and inc.get("error") != "KeyboardInterrupt()":
        raise RuntimeError("unexpected state of the interrupted run")
    runs = []
    for e in v1["runs"]:
        e = dict(e)
        if e["run_id"] == OLD:
            e["run_id"] = NEW
            e["restart_of"] = OLD
            e["config_hash"] = C.config_hash(e)
        runs.append(e)
    assert sum(e["run_id"] == NEW for e in runs) == 1 and len(runs) == 67
    m = dict(v1)
    m.update({"version": 2, "created": time.time(), "runs": runs,
              "previous_manifest_sha256": C.sha256_file(C.MANIFEST_D_V1),
              "completed_before_v2": [e["run_id"] for e in v1["runs"] if (C.RUNS / e["run_id"] / "summary.json").exists()],
              "authorization_v2": "Approved by the user 2026-11-09 after the sleep stop: 'yeah even lid was closed it should run'. "
                                  "Restart p3d_PRIOR3_s1000 as p3d_PRIOR3_s1000_r1 and resume; system sleep disabled by the user for the remainder.",
              "code_hash": C.code_hash(),
              "interrupted_runs": {OLD: {
                  "files": {p.name: C.sha256_file(p) for p in sorted(folder.iterdir()) if p.is_file()},
                  "error": inc.get("error"), "cause": "system sleep (Clamshell Sleep on battery, lid closed), 577 s suspended; sequence sleep guard",
                  "stage": inc.get("stage"), "optimizer_steps_completed": inc.get("optimizer_steps_completed"),
                  "preserved": "never overwritten or reused"}}})
    C.write_json_atomic(C.MANIFEST_D, m)
    print("Stage D manifest v2", C.sha256_file(C.MANIFEST_D), m["completed_before_v2"])


if __name__ == "__main__":
    main()
