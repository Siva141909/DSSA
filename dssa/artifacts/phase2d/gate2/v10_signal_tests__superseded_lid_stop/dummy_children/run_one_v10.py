"""Dummy run process. Run 1 completes immediately. Run 2 executes the REAL
phase2d/run_one_v10.py (real sigsafe.restore, real run_one_v2.main with its real
manifest/code/config checks, telemetry, tick() and incident handler) with only
train.run_training replaced by a model-free loop: no model, no data, no training."""
import json, os, runpy, sys, time
from pathlib import Path
PH = "/Users/siva/Documents/Major project/dssa/phase2d"
sys.path.insert(0, PH)
import sigsafe
print("[dummy] inherited signals", json.dumps(sigsafe.report()), flush=True)
rid, runs, mode = sys.argv[1], Path(os.environ["DUMMY_RUNS"]), os.environ["TEST_MODE"]
if rid.endswith("_a2"):
    sigsafe.restore()
    d = runs / rid; d.mkdir()
    json.dump({"status": "completed_unverified"}, open(d / "result.json", "w"))
    print("[done] dummy", rid, flush=True)
    sys.exit(0)
if mode == "early_signal":
    time.sleep(30)  # signal arrives here, before the real entry point runs
import common as C
C.ALLOWED_WRITE = C.ALLOWED_WRITE + (Path(os.environ["TEST_DIR"]),)
C.RUNS = runs
import run_one_v2 as R
import torch
R.T.make_batch = lambda dataset, batch_size, device: None   # becomes orig_batch inside main
def dummy_training(spec, device, out_dir, log, **kw):
    w = torch.nn.Parameter(torch.zeros(4))
    opt = torch.optim.SGD([w], lr=0.0)
    (runs / "TRAINING_STARTED").write_text(str(os.getpid()))
    for step in range(1_000_000):
        R.T.make_batch(object(), 8, "cpu")        # real p_batch: stage=train, real tick()
        x = torch.randn(384, 384) @ torch.randn(384, 384)   # busy native compute
        opt.step()                                # real optimizer hook counts the step
        if step == 3:
            torch.save({"step": step, "w": w.detach()}, out_dir / f"{spec['run_id']}_best.pt")
        time.sleep(0.05)
R.T.run_training = dummy_training
sys.argv = [str(Path(PH) / "run_one_v10.py"), rid]
runpy.run_path(str(Path(PH) / "run_one_v10.py"), run_name="__main__")
