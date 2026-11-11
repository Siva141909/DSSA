"""Resume r1 of the single Potsdam test opening (approved by the user 2026-11-12: "go ahead with
your plan"). The first launch stopped when test tile 7_7 of p3d_UNIF1_s4000 passed the 400 s
watchdog during a GPU slowdown (97/700 tiles complete). This launcher runs the unchanged, hashed
run_test.py with only the per-tile watchdog raised to 900 s; every other guard, the scoring code
and the test manifest are untouched. Completed tiles are skipped by run_test.py."""
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "phase3"))
import run_sequence as RS  # noqa: E402
import run_test  # noqa: E402

RS.EVAL_HANG_S = 900

if __name__ == "__main__":
    run_test.main()
