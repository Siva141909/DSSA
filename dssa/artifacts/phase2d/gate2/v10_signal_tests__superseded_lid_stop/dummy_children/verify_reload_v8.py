"""Dummy reload process: real sigsafe.restore(); sleeps when the reload-stage guard test is armed."""
import json, os, sys, time
from pathlib import Path
sys.path.insert(0, "/Users/siva/Documents/Major project/dssa/phase2d")
import sigsafe
print("[dummy reload] inherited signals", json.dumps(sigsafe.report()), flush=True)
sigsafe.restore()
print("[dummy reload] after restore", json.dumps(sigsafe.report()), flush=True)
if os.environ["TEST_MODE"] == "reload_guard":
    (Path(os.environ["DUMMY_RUNS"]) / "RELOAD_STARTED").write_text(str(os.getpid()))
    try:
        time.sleep(600)
    except BaseException as ex:
        print("[dummy reload] interrupted", repr(ex), flush=True); raise
print("[reload ok] dummy", flush=True)
