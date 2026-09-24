"""
DSSA Phase 2B-A: FINAL DSS computation on the formally locked target-probe
split, plus the authorized Top-K sweep {2,4,6,8,12}.

Reuses the exact frozen/verified mechanism from Phase 2A
(run_phase2a_dss.py) unchanged: cosine_dss_per_layer, bootstrap_null,
pool_patch_tokens, rank_layers, the Strategy C coefficients already fit in
Phase 1B. Nothing about the DSS definition is modified. The only new input
is the target side, which now uses the formally locked 5-file target-probe
(dssa/artifacts/splits/vaihingen_target_split_manifest.json) instead of
Phase 2A's ad hoc exploratory file selection.

No LoRA. No training. No optimizer. No gradients beyond the frozen,
no_grad() forward pass. No target-validation or target-test file is
referenced anywhere in this script.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_phase2a_dss as p2a  # noqa: E402  (reused unchanged: cosine_dss_per_layer, bootstrap_null, etc.)

ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS = ROOT / "artifacts" / "dss"
ARTIFACTS.mkdir(parents=True, exist_ok=True)
SPLITS_DIR = ROOT / "artifacts" / "splits"

N_LAYERS = 24
K_SWEEP = [2, 4, 6, 8, 12]  # newly authorized this phase - NOT part of the original freeze


def early_middle_late(K: int) -> dict:
    early = list(range(0, K))
    late = list(range(N_LAYERS - K, N_LAYERS))
    mid_start = (N_LAYERS - K) // 2
    middle = list(range(mid_start, mid_start + K))
    return {"early": early, "middle": middle, "late": late}


def jaccard(a: set, b: set) -> float:
    if not (a | b):
        return 1.0
    return len(a & b) / len(a | b)


def main():
    log = []
    def LOG(m):
        print(m); log.append(str(m))

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    LOG(f"[env] device={device}")

    LOG("[split] loading LOCKED manifest (created this phase, not modified here)...")
    with open(SPLITS_DIR / "vaihingen_target_split_manifest.json") as f:
        manifest = json.load(f)
    probe_names = manifest["partitions"]["target_probe"]
    LOG(f"[split] target-probe (5 files, locked): {probe_names}")
    LOG(f"[split] target-validation NOT referenced: {manifest['partitions']['target_validation']}")
    LOG(f"[split] target-test NOT referenced: {manifest['partitions']['target_test']}")

    LOG("[model] loading frozen Prithvi-EO-2.0-300M encoder (num_frames=1)...")
    encoder = p2a.dssa_model.load_frozen_encoder(num_frames=1, device=device)
    n_trainable = sum(p.numel() for p in encoder.parameters() if p.requires_grad)
    assert n_trainable == 0
    LOG(f"[model] loaded, trainable_params={n_trainable}")

    LOG("[strategyC] reusing ALREADY-FITTED Phase 1B coefficients (not refitting).")
    with open(ROOT / "artifacts" / "radiometric_transform.json") as f:
        saved = json.load(f)
    coeffs = p2a.dssa_prep.SourceFitAffine(offset=tuple(saved["offset_IR_R_G"]), scale=tuple(saved["scale_IR_R_G"]))

    potsdam_files = p2a.list_files(p2a.POTSDAM_DIR)
    assert len(potsdam_files) == 38
    # Reuse the EXACT frozen Potsdam source/null mechanism from Phase 2A Probe A - unchanged.
    source_files = potsdam_files[0:16]
    null_files = potsdam_files[16:32]
    target_probe_files = [p2a.VAIHINGEN_DIR / n for n in probe_names]

    LOG(f"[final-dss] source (Potsdam, {len(source_files)}): {[f.name for f in source_files]}")
    LOG(f"[final-dss] null pool (Potsdam, {len(null_files)}): {[f.name for f in null_files]}")
    LOG(f"[final-dss] target-probe (Vaihingen, {len(target_probe_files)}): {[f.name for f in target_probe_files]}")

    source_pooled = [p2a.forward_pooled(encoder, coeffs, f, "top_left", device) for f in source_files]
    null_pooled = [p2a.forward_pooled(encoder, coeffs, f, "top_left", device) for f in null_files]
    target_pooled = [p2a.forward_pooled(encoder, coeffs, f, "top_left", device) for f in target_probe_files]
    LOG(f"[final-dss] forward passes complete: {len(source_files)+len(null_files)+len(target_probe_files)}")

    raw_dss = p2a.cosine_dss_per_layer(source_pooled, target_pooled)
    null_draws = p2a.bootstrap_null(null_pooled, p2a.BOOTSTRAP_RESAMPLES, p2a.BOOTSTRAP_SEED)
    import numpy as np
    null_mean = [float(np.mean(d)) for d in null_draws]
    null_std = [float(np.std(d)) for d in null_draws]
    normalized = [(raw_dss[li] - null_mean[li]) / (null_std[li] + 1e-8) for li in range(N_LAYERS)]
    ranking = p2a.rank_layers(normalized)

    LOG("\n=== 24-layer final DSS table ===")
    for li in range(N_LAYERS):
        LOG(f"  L{li:2d}: raw={raw_dss[li]:.5f}  null_mean={null_mean[li]:.5f}  null_std={null_std[li]:.5f}  norm={normalized[li]:+.4f}")
    LOG(f"  ranking (most-to-least sensitive): {ranking}")

    # ---- Top-K sweep ----
    LOG("\n=== Top-K sweep: K in {2,4,6,8,12} (newly authorized this phase) ===")
    sweep_results = {}
    for K in K_SWEEP:
        dssa_layers = set(ranking[:K])
        controls = early_middle_late(K)
        early, middle, late = set(controls["early"]), set(controls["middle"]), set(controls["late"])
        entry = {
            "K": K,
            "dssa_layers": sorted(dssa_layers),
            "early_layers": sorted(early),
            "middle_layers": sorted(middle),
            "late_layers": sorted(late),
            "dssa_intersect_early": sorted(dssa_layers & early),
            "dssa_intersect_middle": sorted(dssa_layers & middle),
            "dssa_intersect_late": sorted(dssa_layers & late),
            "jaccard_dssa_early": jaccard(dssa_layers, early),
            "jaccard_dssa_middle": jaccard(dssa_layers, middle),
            "jaccard_dssa_late": jaccard(dssa_layers, late),
            "dssa_equals_early": dssa_layers == early,
            "dssa_equals_middle": dssa_layers == middle,
            "dssa_equals_late": dssa_layers == late,
        }
        sweep_results[str(K)] = entry
        LOG(f"  K={K}: DSSA={entry['dssa_layers']}  Early={entry['early_layers']}  Middle={entry['middle_layers']}  Late={entry['late_layers']}")
        LOG(f"        Jaccard(DSSA,Early)={entry['jaccard_dssa_early']:.3f}  Jaccard(DSSA,Middle)={entry['jaccard_dssa_middle']:.3f}  Jaccard(DSSA,Late)={entry['jaccard_dssa_late']:.3f}")
        LOG(f"        DSSA==Early:{entry['dssa_equals_early']}  DSSA==Middle:{entry['dssa_equals_middle']}  DSSA==Late:{entry['dssa_equals_late']}")

    k6_collision = sweep_results["6"]["dssa_equals_late"]
    LOG(f"\n=== K=6 collision check: DSSA@K=6 == Late@K=6 ? {k6_collision} ===")

    output = {
        "config": {
            "N_LAYERS": N_LAYERS, "K_SWEEP": K_SWEEP,
            "bootstrap_resamples": p2a.BOOTSTRAP_RESAMPLES, "bootstrap_seed": p2a.BOOTSTRAP_SEED,
            "checkpoint": "ibm-nasa-geospatial/Prithvi-EO-2.0-300M",
            "checkpoint_revision": "9eb1b1102806593963daa333bcc491b1c6f8562f",
            "split_manifest": "dssa/artifacts/splits/vaihingen_target_split_manifest.json",
        },
        "source_files": [f.name for f in source_files],
        "null_files": [f.name for f in null_files],
        "target_probe_files": [f.name for f in target_probe_files],
        "raw_dss": raw_dss,
        "null_mean": null_mean,
        "null_std": null_std,
        "normalized_dss": normalized,
        "ranking_desc": ranking,
        "k_sweep": sweep_results,
        "k6_dssa_equals_late": k6_collision,
    }
    with open(ARTIFACTS / "phase2b_final_dss_results.json", "w") as f:
        json.dump(output, f, indent=2, default=str)
    with open(ARTIFACTS / "phase2b_final_dss_run.log", "w") as f:
        f.write("\n".join(log))
    LOG(f"\n[done] wrote {ARTIFACTS / 'phase2b_final_dss_results.json'}")


if __name__ == "__main__":
    main()
