"""Gate checks for the 8-bit cache. `equiv` compares old and new pipelines; any
inexact result stops. `manifest` writes manifest v2 after equivalence passes."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

C.install_guards()
sys.path.insert(0, str(C.ROOT / "train"))
import numpy as np  # noqa: E402
import torch  # noqa: E402
import dataset as ds_mod  # noqa: E402
import train as T  # noqa: E402
from checkpoint import load_checkpoint  # noqa: E402
import models as M  # noqa: E402
from dataset_u8 import TargetSegDatasetU8  # noqa: E402

OUT = C.GATE0 / "equivalence_v2.json"


def spy(ds, rec):
    orig = ds._augment

    def f(i, l):
        pre = (i.copy(), l.copy())
        a, b = orig(i, l)
        rec[:] = [pre[0], pre[1], a, b]
        return a, b
    ds._augment = f


def exact(a, b, what, n):
    if a.dtype != b.dtype or a.shape != b.shape or not np.array_equal(a, b):
        raise RuntimeError(f"EQUIVALENCE FAILED at sample {n}: {what} ({a.dtype} vs {b.dtype})")


def compare(seed, n):
    C_old, C_new = ds_mod.TargetSegDataset(C.TRAIN, mode="train", seed=seed), TargetSegDatasetU8(C.TRAIN, mode="train", seed=seed)
    ro, rn = [], []
    spy(C_old, ro)
    spy(C_new, rn)
    order = []
    batches = []
    for i in range(n):
        xo, yo, fo = C_old[0]
        xn, yn, fn = C_new[0]
        if fo != fn:
            raise RuntimeError(f"EQUIVALENCE FAILED at sample {i}: file order")
        exact(ro[0], rn[0], "calibrated crop", i)
        exact(ro[1], rn[1], "label crop", i)
        exact(ro[2], rn[2], "augmented image", i)
        exact(ro[3], rn[3], "augmented label", i)
        if xo.dtype != xn.dtype or yo.dtype != yn.dtype or not torch.equal(xo, xn) or not torch.equal(yo, yn):
            raise RuntimeError(f"EQUIVALENCE FAILED at sample {i}: model input or label tensor")
        if C_old._rng.getstate() != C_new._rng.getstate():
            raise RuntimeError(f"EQUIVALENCE FAILED at sample {i}: RNG state")
        order.append(fo)
        if i < 64:
            batches.append((xn, yn))
    raw = sum(a.nbytes + b.nbytes for a, b in C_new._cache.values())
    old = sum(a.nbytes + b.nbytes for a, b in C_old._cache.values())
    final = C.rng_state_hash(C_new._rng)
    return {"seed": seed, "samples": n, "mismatches": 0, "final_rng_hash": final, "order_hash": C.canon_hash(order), "cache_bytes_old": old, "cache_bytes_new": raw}, batches


def equiv():
    t0 = time.time()
    expected = json.load(open(C.BASELINE))["expected"]
    res, first = [], None
    for s in C.PILOT_SEEDS:
        r, b = compare(s, 16000)
        r["final_matches_replay"] = r["final_rng_hash"] == expected[str(s)]["data_stream_final"]
        if not r["final_matches_replay"]:
            raise RuntimeError("EQUIVALENCE FAILED: final RNG differs from replay")
        res.append(r)
        first = first or b
        print(r, round(time.time() - t0), flush=True)
    # fixed probe batches through saved models, old-pipeline tensors versus new
    old_ds = ds_mod.TargetSegDataset(C.TRAIN, mode="train", seed=1000)
    probes = []
    for name in ("run000_K0_K0_decoder_only", "run001_K2_DSSA", "run002_K2_Early"):
        rd = C.P2C / name
        L = json.load(open(rd / "result.json"))["train_result"]["layer_indices"]
        m, mods = T.build_model(L, device="mps")
        load_checkpoint(rd / f"{name}_best.pt", m, mods, L)
        old_ds._rng.seed(1000)
        batch_equal = 0
        for b in range(8):
            xo = torch.stack([old_ds[0][0] for _ in range(8)]).to("mps")
            xn = torch.stack([first[b * 8 + j][0] for j in range(8)]).to("mps")
            for mode in ("eval", "train"):
                getattr(m, mode)()
                with torch.no_grad():
                    a, c = m(xo).cpu(), m(xn).cpu()
                if not torch.equal(a, c):
                    raise RuntimeError(f"EQUIVALENCE FAILED: model output differs, {name}, batch {b}, {mode}")
            batch_equal += 1
        probes.append({"checkpoint": name, "layers": L, "batches_identical": batch_equal, "modes": ["eval", "train"]})
        print(probes[-1], flush=True)
        del m, mods
        torch.mps.empty_cache()
    C.write_json_atomic(OUT, {"result": "PASS, bit-identical", "streams": res, "model_output_probes": probes, "seconds": time.time() - t0})
    print("EQUIVALENCE PASS", round(time.time() - t0))


def manifest():
    add, frz, eq = C.sha256_file(C.CODE / "PHASE2D_ADDENDUM_V2.md"), C.sha256_file(C.GATE0 / "frozen_rankings.json"), C.sha256_file(OUT)
    v1 = json.load(open(C.MANIFEST))
    changed = [k for k, v in v1["code_hash"].items() if C.sha256_file(C.CODE / k) != v]
    if changed:
        raise RuntimeError(f"version 1 files changed: {changed}")
    e = {"run_id": "p2d_oracle_L00_s1000_a3", "K": 1, "layer_indices": [0], "training_seed": 1000, "lora_init_seed": 1000 + C.LORA_SEED_OFFSET, "condition_labels": ["Oracle_L00"],
         "protocol_file_hash": C.sha256_file(C.ROOT / "config" / "phase2b_training_protocol.json"), "addendum_sha256": add, "frozen_rankings_sha256": frz, "equivalence_sha256": eq,
         "cache": "TargetSegDatasetU8", "phase": "2D-pilot-v2", "est_seconds": round(1472 + 34.6 * 24)}
    e["config_hash"] = C.config_hash(e)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=C.PROJECT, capture_output=True, text=True).stdout.strip()
    C.write_json_atomic(C.ART / "manifest_pilot_v2.json", {"authorization": "One Layer 0 attempt only", "version": 2, "supersedes_for_this_run": "manifest_pilot.json (preserved unchanged)", "manifest_v1_sha256": C.sha256_file(C.MANIFEST),
                                                           "code_hash": C.code_hash(), "git_head": head, "runs": [e]})
    print("manifest v2 written", e["config_hash"][:12])


if __name__ == "__main__":
    {"equiv": equiv, "manifest": manifest}[sys.argv[1]]()
