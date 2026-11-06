"""Gate 0 integrity checks. `baseline` runs before code is frozen; `manifest`
writes the 12-run manifest after all code and the addendum are final."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

C.install_guards()
sys.path.insert(0, str(C.ROOT / "train"))
import numpy as np  # noqa: E402
import torch  # noqa: E402
import torch.nn as nn  # noqa: E402
import dataset as ds_mod  # noqa: E402
import train as T  # noqa: E402
import lora as lora_mod  # noqa: E402
import tiling  # noqa: E402
from checkpoint import load_checkpoint  # noqa: E402
import models as M  # noqa: E402
import evaluation as E  # noqa: E402

PREFIXES = {"run000_K0_K0_decoder_only": ("122dd9100d893b01", "82d4b91e1c128540"), "run001_K2_DSSA": ("46c3b50b87e9f1ff", "21a3148324cc0471"),
            "run002_K2_Early": ("33ac709ef4149c69", "63798f91efd399f1"), "run003_K2_Late": ("c62046331b76c21c", "653f652cb8210e67"),
            "run004_K2_LowestDSS": ("efc16d94f778b216", "65a490483d2c8f03")}


def git(*a):
    return subprocess.run(["git", *a], cwd=C.PROJECT, capture_output=True, text=True).stdout.strip()


def baseline():
    fro = C.frozen_hashes()
    for r, (ck, rs) in PREFIXES.items():
        base = f"dssa/artifacts/phase2c/runs/{r}/"
        assert fro[base + f"{r}_best.pt"].startswith(ck) and fro[base + "result.json"].startswith(rs), r
    run0 = json.load(open(C.P2C / C.P2C_RUNS[0] / "result.json"))
    expected, common = {}, {}
    for seed in C.PILOT_SEEDS:
        T.set_all_seeds(seed)
        model, _ = T.build_model([], device="mps")
        rng_after_build = M.tensor_hash([torch.get_rng_state()])  # captured before the dummy modules below draw from it
        dq = nn.Linear(1024, 3072)
        import math
        q = lora_mod.LoRAQKV(dq)
        g = torch.Generator().manual_seed(seed + C.LORA_SEED_OFFSET)
        nn.init.kaiming_uniform_(q.lora_A_q, a=math.sqrt(5), generator=g)
        nn.init.kaiming_uniform_(q.lora_A_v, a=math.sqrt(5), generator=g)
        expected[str(seed)] = {"decoder_hash": M.decoder_hash(model.decoder), "torch_rng_hash": rng_after_build,
                               "lora_A_hash": M.tensor_hash([q.lora_A_q, q.lora_A_v]), "data_stream_final": C.simulate_data_stream(seed)}
        common = {"backbone_fp": M.backbone_fingerprint(model), "probe_hash": M.probe_output_hash(model, "mps")}
        del model
    if common["backbone_fp"] != run0["backbone_fingerprint_after_training"]:
        raise RuntimeError("backbone fingerprint differs from run000")

    # K0_s1000 versus run000: the training configuration, compared field by field
    tr = run0["train_result"]
    code_same = {f: git("rev-parse", f"HEAD:dssa/train/{f}") == subprocess.run(["git", "hash-object", str(C.ROOT / "train" / f)], capture_output=True, text=True).stdout.strip()
                 for f in ("train.py", "dataset.py", "decoder.py", "losses.py", "metrics.py", "tiling.py", "model_wrapper.py", "checkpoint.py", "lora.py")}
    cfg = {"code_identical_to_HEAD": code_same, "training_seed": tr["training_seed"] == 1000, "steps": tr["total_steps_executed"] == T.TOTAL_STEPS,
           "checkpoint_every": tr["checkpoint_every"] == T.CHECKPOINT_EVERY, "trainable_params": tr["parameter_counts"]["trainable_params"] == 2766726,
           "optimizer": {"lr": T.LR, "betas": T.BETAS, "wd": T.WEIGHT_DECAY, "warmup": T.WARMUP_STEPS, "batch": T.BATCH_SIZE, "clip": T.GRAD_CLIP_NORM},
           "torch_version_same": run0["hardware"]["torch_version"] == torch.__version__, "python_version_same": run0["hardware"]["python_version"] == sys.version.split()[0],
           "run000_platform": run0["hardware"]["platform"], "now_platform": T.hardware_info()["platform"],
           "training_code_path": "train.run_training called unchanged; K=0 uses model_wrapper.build_model unchanged"}
    if not all(code_same.values()) or not all(cfg[k] for k in ("training_seed", "steps", "checkpoint_every", "trainable_params", "torch_version_same", "python_version_same")):
        raise RuntimeError(f"K0 configuration differs from run000: {cfg}")

    # the per-tile evaluator must match the Phase 2C predictor pixel for pixel
    m, mods = T.build_model([], device="mps")
    load_checkpoint(C.P2C / C.P2C_RUNS[0] / f"{C.P2C_RUNS[0]}_best.pt", m, mods, [])
    C.install_tile_allowlist(ds_mod, set())
    cal, lab, fn = ds_mod.TargetSegDataset([C.VAL[-1]], mode="eval")[0]
    a = tiling.sliding_window_predict(m, cal, "mps")
    b, _, ce = E.eval_tile(m, cal, lab, "mps")
    if not np.array_equal(a, b):
        raise RuntimeError("evaluator replica differs from tiling.py")
    C.write_json_atomic(C.BASELINE, {"frozen": fro, "expected": expected, "expected_common": common, "k0_vs_run000": cfg, "evaluator_replica_identical_on": fn, "git_head": git("rev-parse", "HEAD")})
    print("baseline ok", json.dumps(common), {k: v["decoder_hash"][:12] for k, v in expected.items()}, cfg["run000_platform"], cfg["now_platform"])


def manifest():
    proto, add, frz = C.sha256_file(C.ROOT / "config" / "phase2b_training_protocol.json"), C.sha256_file(C.CODE / "PHASE2D_ADDENDUM.md"), C.sha256_file(C.GATE0 / "frozen_rankings.json")
    est = lambda l: 1467 if l is None else round(1472 + 34.6 * (24 - l))
    runs = []
    for s in C.PILOT_SEEDS:
        for l in (None, 0, 12, 23):
            rid = f"p2d_ctrl_K0_s{s}" if l is None else f"p2d_oracle_L{l:02d}_s{s}"
            e = {"run_id": rid, "K": 0 if l is None else 1, "layer_indices": [] if l is None else [l], "training_seed": s, "lora_init_seed": s + C.LORA_SEED_OFFSET,
                 "condition_labels": ["K0_control"] if l is None else [f"Oracle_L{l:02d}"], "protocol_file_hash": proto, "addendum_sha256": add, "frozen_rankings_sha256": frz, "phase": "2D-pilot", "est_seconds": est(l)}
            e["config_hash"] = C.config_hash(e)
            runs.append(e)
    C.write_json_atomic(C.MANIFEST, {"authorization": "Research lead conditional authorization: 12 pilot runs only", "code_hash": C.code_hash(), "git_head": git("rev-parse", "HEAD"), "git_dirty_paths_expected": [".gitignore", "dssa/phase2d/", "dssa/artifacts/phase2d/"], "runs": runs})
    print("manifest", len(runs), "est h", sum(r["est_seconds"] for r in runs) / 3600)


if __name__ == "__main__":
    {"baseline": baseline, "manifest": manifest}[sys.argv[1]]()
