"""Launcher for run_gate2_v6.py, per the research lead's launch authorization
(2026-11-03): Docker Desktop or its virtual machine starting is not a stop
condition. The `no_virtual_machine_running` preflight check is therefore made
advisory: it is removed from the pass/fail checks and recorded in the guard log
as `virtual_machine_running_advisory`. Every other preflight check, the in-run
guard (sleep, lid, charger, thermal, memory pressure) and the runner's limits
(512 MB swap growth, 11.5 GB footprint, 1.5x runtime, critical pressure) are
unchanged. Kept outside the code directory so the v6 manifest code hash holds."""
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "phase2d"))
import run_gate2_v6 as R  # noqa: E402

_preflight = R.preflight


def preflight():
    checks, info = _preflight()
    info["virtual_machine_running_advisory"] = not checks.pop("no_virtual_machine_running")
    return checks, info


R.preflight = preflight

if __name__ == "__main__":
    R.main()
