"""Recovery manifest v11 entry point: the approved run_one_v2 runner, pointed at manifest v11.
Signal handling is restored first (sigsafe), so SIGINT and SIGTERM raise inside
run_one_v2.main and its existing handler writes incident.json (INCIDENT_006)."""
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import sigsafe  # noqa: E402

sigsafe.restore()
print("[signals]", json.dumps(sigsafe.report()), flush=True)
import run_one_v2 as R  # noqa: E402

R.MANIFEST_V2 = R.C.ART / "manifest_gate2_recovery_v11.json"
R.main()
