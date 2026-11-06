"""Sequence-process harness: the real run_gate2_v8.main(), with artifacts, run folders
and child scripts redirected to this scratch directory, and hazards injected into
env_state for the guard tests. Launched exactly like production (nohup caffeinate ... &)."""
import json, os, sys, time
from pathlib import Path
T = Path(sys.argv[1]); mode = sys.argv[2]
PH = "/Users/siva/Documents/Major project/dssa/phase2d"
sys.path.insert(0, PH)
import run_gate2_v8 as G
C = G.C
art = T / mode
(art / "runs").mkdir(parents=True); (art / "logs").mkdir()
C.ALLOWED_WRITE = C.ALLOWED_WRITE + (T,)
C.ART, C.RUNS, C.CODE = art, art / "runs", T / "code"
G.STATUS, G.GUARD_LOG, G.INTERRUPTIONS = art / "status.json", art / "logs" / "guard.jsonl", art / "logs" / "interruptions.jsonl"
G.POLL_S, G.SLOW_POLL_S = 1, 1
os.environ.update(DUMMY_RUNS=str(art / "runs"), TEST_MODE=mode, TEST_DIR=str(T))
marker = art / "runs" / "TRAINING_STARTED"
reload_marker = art / "runs" / "RELOAD_STARTED"
orig_env, real_clock = G.env_state, G.time.clock_gettime
def armed():
    return (mode.startswith("guard_") and marker.exists()) or (mode == "reload_guard" and reload_marker.exists())
def env(full=True):
    s = orig_env(full)
    if armed():
        if mode in ("guard_charger", "reload_guard"): s["ac"] = False
        if mode == "guard_lid" and full: s["lid_open"] = False
        if mode == "guard_thermal" and full: s["thermal_ok"] = False
    return s
def clock(c):
    v = real_clock(c)
    return v - 100 if (mode == "guard_sleep" and armed() and c == G.time.CLOCK_UPTIME_RAW) else v
G.env_state, G.time.clock_gettime = env, clock
print("[harness] sequence pid", os.getpid(), flush=True)
try:
    G.main()
except SystemExit as e:
    print("[harness] sequence exited", e.code, flush=True)
