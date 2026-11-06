"""Reload verification entry point for manifest v8: verify_reload.main, unchanged,
with SIGINT and SIGTERM handling restored first (sigsafe)."""
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import sigsafe  # noqa: E402

sigsafe.restore()
print("[signals]", json.dumps(sigsafe.report()), flush=True)
import verify_reload as V  # noqa: E402

V.main()
