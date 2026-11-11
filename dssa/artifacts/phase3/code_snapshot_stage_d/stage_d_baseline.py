"""Stage D reference initialisation, computed once before any Stage D run and then frozen.

For every Stage D training seed (1000-10000) it seeds the global RNG exactly as
train.run_training does and records, as phase2d/gate0/baseline_hashes.json does for 1000-3000:
the decoder hash and torch RNG hash after the build (K0, rank-8 and rank-1 builds must agree),
and the LoRA A hash at rank 8 and rank 1. Seeds 1000-3000 must reproduce the Phase 2D values
exactly or nothing is written. No tile or label is read."""
from __future__ import annotations

import gc
import json
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import p3common as C  # noqa: E402

C.install_guards()
C.setup_paths()
import torch  # noqa: E402
import train as T  # noqa: E402
import models as M  # noqa: E402
import p3models as P  # noqa: E402

SEEDS_D = tuple(range(1000, 10001, 1000))


def one(seed, layers, rank):
    T.set_all_seeds(seed)
    model, mods = P.build(layers, "mps", seed + C.LORA_SEED_OFFSET, rank)
    rec = {"decoder_hash": M.decoder_hash(model.decoder), "torch_rng_hash": M.tensor_hash([torch.get_rng_state()]),
           "backbone_fp": M.backbone_fingerprint(model)}
    if mods:
        rec["lora_A_hash"] = M.tensor_hash([mods[0].lora_A_q, mods[0].lora_A_v])
        rec["lora_params"] = sum(m.lora_param_count() for m in mods)
    del model, mods
    gc.collect()
    torch.mps.empty_cache()
    return rec


def main():
    out = C.STAGE_D_BASELINE
    if out.exists():
        raise FileExistsError(out)
    p2d = json.load(open(C.P2D_BASELINE))
    common = p2d["expected_common"]["backbone_fp"]
    expected = {}
    for s in SEEDS_D:
        k0, r8, r1 = one(s, [], 8), one(s, [0], 8), one(s, [0], 1)
        for k in ("decoder_hash", "torch_rng_hash"):
            if not (k0[k] == r8[k] == r1[k]):
                raise RuntimeError(f"seed {s}: {k} differs between K0, rank-8 and rank-1 builds")
        for r in (k0, r8, r1):
            if r["backbone_fp"] != common:
                raise RuntimeError(f"seed {s}: backbone fingerprint changed")
        if r8["lora_params"] != 32768 or r1["lora_params"] != 4096:
            raise RuntimeError(f"seed {s}: LoRA parameter count")
        e = {"decoder_hash": k0["decoder_hash"], "torch_rng_hash": k0["torch_rng_hash"],
             "lora_A_hash_r8": r8["lora_A_hash"], "lora_A_hash_r1": r1["lora_A_hash"]}
        if str(s) in p2d["expected"]:
            ref = p2d["expected"][str(s)]
            for k, k2 in (("decoder_hash", "decoder_hash"), ("torch_rng_hash", "torch_rng_hash"), ("lora_A_hash_r8", "lora_A_hash")):
                if e[k] != ref[k2]:
                    raise RuntimeError(f"seed {s}: {k} does not reproduce the Phase 2D value")
            e["matches_phase2d"] = True
        expected[str(s)] = e
        print(f"[baseline] seed {s} ok{' (= Phase 2D)' if e.get('matches_phase2d') else ''}", flush=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    C.write_json_atomic(out, {"created": time.time(), "seeds": list(SEEDS_D), "expected": expected,
                              "expected_common": p2d["expected_common"], "phase2d_baseline_sha256": C.sha256_file(C.P2D_BASELINE),
                              "rank1_alpha": P.alpha_for(1), "rank8_alpha": P.alpha_for(8)})
    C.STAGE_D_BASELINE_HASH.write_text(C.sha256_file(out) + "  stage_d_baseline.json\n")
    print("[baseline] frozen", C.sha256_file(out), flush=True)


if __name__ == "__main__":
    main()
