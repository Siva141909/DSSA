"""Recovery manifest v6 entry point: the approved run_one_v2 runner, pointed at manifest v6."""
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_one_v2 as R  # noqa: E402

R.MANIFEST_V2 = R.C.ART / "manifest_gate2_recovery_v6.json"
R.main()
