"""Writes Stage D manifest v3. Never overwrites. Approved by the user 2026-11-10.

p3d_UNIF1_s7000 was stopped at optimizer step 3 by the swap guard (swap growth 596 MB, memory
pressure warning) while other applications were open. Its folder is preserved untouched and
recorded under interrupted_runs; the run is redone from scratch as p3d_UNIF1_s7000_r1 with the
identical configuration, in the same position. Every other entry is copied from v2 unchanged.
The heavy applications were closed before the restart; all guards are unchanged."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import p3common as C  # noqa: E402

C.install_guards()

OLD, NEW = "p3d_UNIF1_s7000", "p3d_UNIF1_s7000_r1"


def main():
    if C.MANIFEST_D.exists():
        raise FileExistsError(C.MANIFEST_D)
    v2 = json.load(open(C.MANIFEST_D_V2))
    folder = C.RUNS / OLD
    inc = json.load(open(folder / "incident.json"))
    if (folder / "summary.json").exists() or "swap growth" not in inc.get("error", ""):
        raise RuntimeError("unexpected state of the interrupted run")
    runs = []
    for e in v2["runs"]:
        e = dict(e)
        if e["run_id"] == OLD:
            e["run_id"] = NEW
            e["restart_of"] = OLD
            e["config_hash"] = C.config_hash(e)
        runs.append(e)
    assert sum(e["run_id"] == NEW for e in runs) == 1 and len(runs) == 67
    m = dict(v2)
    interrupted = dict(v2["interrupted_runs"])
    interrupted[OLD] = {
        "files": {p.name: C.sha256_file(p) for p in sorted(folder.iterdir()) if p.is_file()},
        "error": inc.get("error"), "cause": "swap guard while other applications (browser, messenger) were open",
        "stage": inc.get("stage"), "optimizer_steps_completed": inc.get("optimizer_steps_completed"),
        "preserved": "never overwritten or reused"}
    m.update({"version": 3, "created": time.time(), "runs": runs,
              "previous_manifest_sha256": C.sha256_file(C.MANIFEST_D_V2),
              "completed_before_v3": [e["run_id"] for e in v2["runs"] if (C.RUNS / e["run_id"] / "summary.json").exists()],
              "authorization_v3": "Approved by the user 2026-11-10 after the swap stop: 'okay go ahead'. "
                                  "Restart p3d_UNIF1_s7000 as p3d_UNIF1_s7000_r1 and resume; heavy applications closed.",
              "code_hash": C.code_hash(), "interrupted_runs": interrupted})
    C.write_json_atomic(C.MANIFEST_D, m)
    print("Stage D manifest v3", C.sha256_file(C.MANIFEST_D), len(m["completed_before_v3"]), "completed")


if __name__ == "__main__":
    main()
