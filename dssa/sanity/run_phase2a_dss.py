"""
DSSA Phase 2A: DSS extraction and layer-selection validation.

Uses the FROZEN DSS definition exactly (pooling, source centroid, cosine
distance, source-vs-source null, normalization, layer set, checkpoint,
preprocessing, deterministic tie-breaking). Nothing here trains anything,
uses labels, computes gradients, or runs LoRA. This script only computes
diagnostic numbers and definitions of layer sets - it does not select,
rank-and-commit-to, or act on any of them.

Reuses the ALREADY-FITTED, FROZEN Strategy C coefficients from Phase 1B
(dssa/artifacts/radiometric_transform.json) - does NOT refit.

One addition beyond Phase 1B: Phase 1B's DSS diagnostic used a single
source-vs-source null draw (explicitly flagged there as a simplification
due to a "tiny sanity batch"). The frozen DSS definition
(DSSA_PROJECT_FREEZE.md Sec O-C) specifies a *bootstrap-estimated* null
distribution. Now that real data volume is available, this script
implements that properly: many resampled splits of a null-designated file
pool, building an actual distribution per layer, and z-scoring the real
raw DSS against its mean/std. This is not a new criterion - it is the
already-frozen definition, executed to its full specification for the
first time now that it's practical to do so.
"""
from __future__ import annotations

import json
import random
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import torch
import tifffile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import model as dssa_model          # noqa: E402
import preprocessing as dssa_prep   # noqa: E402
import mmd as dssa_mmd              # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
POTSDAM_DIR = ROOT / "data" / "potsdam_irrg"
VAIHINGEN_DIR = ROOT / "data" / "vaihingen_irrg"
ARTIFACTS = ROOT / "artifacts" / "dss"
ARTIFACTS.mkdir(parents=True, exist_ok=True)

CROP = 224
N_LAYERS = 24
K_ILLUSTRATIVE = 6           # for defining control layer SETS only - not a final K decision
BOOTSTRAP_RESAMPLES = 40     # fixed, decided before running, not tuned on results
BOOTSTRAP_SEED = 1234
RANDOM_K_SEED = 42
TIE_TOLERANCE = 1e-6         # frozen, DSSA_PROJECT_FREEZE.md Sec O-H


def list_files(d: Path) -> list[Path]:
    return sorted(d.glob("*.tif"))


def crop_origin_for(shape_hw, mode: str) -> tuple[int, int]:
    h, w = shape_hw
    if mode == "top_left":
        return (0, 0)
    if mode == "bottom_right":
        return (h - CROP, w - CROP)
    raise ValueError(mode)


def load_irrg_crop_at(path: Path, mode: str) -> np.ndarray:
    arr = tifffile.imread(str(path))
    y0, x0 = crop_origin_for(arr.shape[:2], mode)
    crop = arr[y0:y0 + CROP, x0:x0 + CROP, :]
    if crop.shape[:2] != (CROP, CROP):
        raise ValueError(f"{path.name}: bad crop shape {crop.shape[:2]} for mode={mode}")
    return crop


def pool_patch_tokens(layer_feat: torch.Tensor) -> torch.Tensor:
    return layer_feat[0, 1:, :].mean(dim=0)


def forward_pooled(encoder, coeffs, path: Path, crop_mode: str, device) -> list[torch.Tensor]:
    """Returns list of N_LAYERS pooled (embed_dim,) vectors for one file."""
    crop = load_irrg_crop_at(path, crop_mode)
    calibrated = coeffs.apply(crop)
    x = dssa_prep.build_prithvi_input(calibrated).to(device)
    with torch.no_grad():
        feats = dssa_model.extract_layer_representations(encoder, x)
    return [pool_patch_tokens(f.cpu()) for f in feats]


def cosine_dss_per_layer(group_a: list[list[torch.Tensor]], group_b: list[list[torch.Tensor]]) -> list[float]:
    """group_a is the 'source' role (centroid); group_b is the 'target' role (per-image distance to centroid).
    Returns one raw cosine DSS value per layer, using the exact frozen formula (DSSA_PROJECT_FREEZE.md Sec O-D)."""
    eps = 1e-8
    out = []
    for li in range(N_LAYERS):
        a_stack = torch.stack([sample[li] for sample in group_a])  # (Na, D)
        b_stack = torch.stack([sample[li] for sample in group_b])  # (Nb, D)
        centroid = a_stack.mean(dim=0, keepdim=True)
        centroid_n = centroid / (centroid.norm(dim=-1, keepdim=True) + eps)
        b_n = b_stack / (b_stack.norm(dim=-1, keepdim=True) + eps)
        cos_sim = (b_n * centroid_n).sum(dim=-1)
        cos_dist = (1.0 - cos_sim).mean().item()
        out.append(cos_dist)
    return out


def bootstrap_null(null_pool: list[list[torch.Tensor]], n_resamples: int, seed: int) -> list[list[float]]:
    """null_pool: pooled reps for a set of source-only files disjoint from the 'source' set used
    for the real DSS. Repeatedly splits this pool into two disjoint halves and computes
    cosine_dss(half_a, half_b) per layer - the same frozen formula, roles both source-only.
    Returns: per-layer list of n_resamples null draws."""
    rng = random.Random(seed)
    n = len(null_pool)
    half = n // 2
    per_layer_draws = [[] for _ in range(N_LAYERS)]
    idx = list(range(n))
    for _ in range(n_resamples):
        rng.shuffle(idx)
        a_idx, b_idx = idx[:half], idx[half:half * 2]
        group_a = [null_pool[i] for i in a_idx]
        group_b = [null_pool[i] for i in b_idx]
        draw = cosine_dss_per_layer(group_a, group_b)
        for li in range(N_LAYERS):
            per_layer_draws[li].append(draw[li])
    return per_layer_draws


def rank_layers(normalized_dss: list[float]) -> list[int]:
    """Descending normalized DSS; ties (within TIE_TOLERANCE) broken by lower layer index
    (DSSA_PROJECT_FREEZE.md Sec O-H)."""
    indices = list(range(len(normalized_dss)))
    def keyfn(i):
        return (-round(normalized_dss[i] / TIE_TOLERANCE), i)
    return sorted(indices, key=keyfn)


def run_probe(name: str, encoder, coeffs, source_files, target_files, null_files, crop_mode, device, log):
    log(f"\n=== Probe {name}: crop_mode={crop_mode} ===")
    log(f"  source ({len(source_files)}): {[f.name for f in source_files]}")
    log(f"  target ({len(target_files)}): {[f.name for f in target_files]}")
    log(f"  null_pool ({len(null_files)}): {[f.name for f in null_files]}")

    source_pooled = [forward_pooled(encoder, coeffs, f, crop_mode, device) for f in source_files]
    target_pooled = [forward_pooled(encoder, coeffs, f, crop_mode, device) for f in target_files]
    null_pooled = [forward_pooled(encoder, coeffs, f, crop_mode, device) for f in null_files]
    log(f"  forward passes complete: {len(source_files)+len(target_files)+len(null_files)}")

    raw_dss = cosine_dss_per_layer(source_pooled, target_pooled)
    null_draws = bootstrap_null(null_pooled, BOOTSTRAP_RESAMPLES, BOOTSTRAP_SEED)
    null_mean = [float(np.mean(d)) for d in null_draws]
    null_std = [float(np.std(d)) for d in null_draws]
    normalized = [(raw_dss[li] - null_mean[li]) / (null_std[li] + 1e-8) for li in range(N_LAYERS)]
    ranking = rank_layers(normalized)

    return {
        "name": name,
        "crop_mode": crop_mode,
        "source_files": [f.name for f in source_files],
        "target_files": [f.name for f in target_files],
        "null_files": [f.name for f in null_files],
        "raw_dss": raw_dss,
        "null_mean": null_mean,
        "null_std": null_std,
        "null_n_resamples": BOOTSTRAP_RESAMPLES,
        "normalized_dss": normalized,
        "ranking_desc": ranking,   # layer indices, most-sensitive-first
        "_source_pooled": source_pooled,
        "_target_pooled": target_pooled,
    }


def main():
    log_lines = []
    def LOG(msg):
        print(msg)
        log_lines.append(str(msg))

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    LOG(f"[env] device={device}")

    LOG("[model] loading frozen Prithvi-EO-2.0-300M encoder (num_frames=1)...")
    encoder = dssa_model.load_frozen_encoder(num_frames=1, device=device)
    n_trainable = sum(p.numel() for p in encoder.parameters() if p.requires_grad)
    assert n_trainable == 0
    LOG(f"[model] loaded, trainable_params={n_trainable}")

    LOG("[strategyC] reusing ALREADY-FITTED Phase 1B coefficients (not refitting).")
    with open(ROOT / "artifacts" / "radiometric_transform.json") as f:
        saved = json.load(f)
    coeffs = dssa_prep.SourceFitAffine(offset=tuple(saved["offset_IR_R_G"]), scale=tuple(saved["scale_IR_R_G"]))
    LOG(f"[strategyC] offset={coeffs.offset} scale={coeffs.scale}")

    potsdam_files = list_files(POTSDAM_DIR)
    vaihingen_files = list_files(VAIHINGEN_DIR)
    assert len(potsdam_files) == 38 and len(vaihingen_files) == 33

    # ---- Probe definitions (fixed before running, not results-based) ----
    probe_A = dict(source=potsdam_files[0:16], null=potsdam_files[16:32], target=vaihingen_files[0:16], crop="top_left")
    probe_B = dict(source=potsdam_files[0:16], null=potsdam_files[16:32], target=vaihingen_files[0:16], crop="bottom_right")
    probe_C = dict(source=potsdam_files[6:22], null=potsdam_files[22:38], target=vaihingen_files[6:22], crop="top_left")

    results = {}
    for name, cfg in [("A", probe_A), ("B", probe_B), ("C", probe_C)]:
        results[name] = run_probe(name, encoder, coeffs, cfg["source"], cfg["target"], cfg["null"], cfg["crop"], device, LOG)

    # ---- Stability analysis across probes ----
    LOG("\n=== Stability analysis ===")
    norm_matrix = np.array([results[k]["normalized_dss"] for k in ["A", "B", "C"]])  # (3, 24)
    per_layer_std = norm_matrix.std(axis=0).tolist()
    per_layer_mean = norm_matrix.mean(axis=0).tolist()

    rank_positions = {}  # layer -> [rank_in_A, rank_in_B, rank_in_C]
    for k in ["A", "B", "C"]:
        ranking = results[k]["ranking_desc"]
        for pos, layer in enumerate(ranking):
            rank_positions.setdefault(layer, []).append(pos)
    rank_variability = {str(layer): {"positions": pos, "range": max(pos) - min(pos), "std": float(np.std(pos))}
                         for layer, pos in rank_positions.items()}

    topk_sets = {k: set(results[k]["ranking_desc"][:K_ILLUSTRATIVE]) for k in ["A", "B", "C"]}
    topk_overlaps = {}
    for a, b in combinations(["A", "B", "C"], 2):
        inter = topk_sets[a] & topk_sets[b]
        union = topk_sets[a] | topk_sets[b]
        topk_overlaps[f"{a}-{b}"] = {"intersection": sorted(inter), "n_intersection": len(inter),
                                      "jaccard": len(inter) / len(union)}

    all_top6 = set.union(*topk_sets.values())
    repeated_in_all_three = set.intersection(*topk_sets.values())
    LOG(f"  per-layer normalized-DSS std across probes A/B/C: min={min(per_layer_std):.4f} max={max(per_layer_std):.4f}")
    LOG(f"  Top-{K_ILLUSTRATIVE} sets: A={sorted(topk_sets['A'])} B={sorted(topk_sets['B'])} C={sorted(topk_sets['C'])}")
    LOG(f"  layers in ALL THREE probes' Top-{K_ILLUSTRATIVE}: {sorted(repeated_in_all_three)}")
    jaccard_summary = {k: round(v["jaccard"], 3) for k, v in topk_overlaps.items()}
    LOG(f"  pairwise Top-{K_ILLUSTRATIVE} Jaccard overlap: {jaccard_summary}")

    stability = {
        "per_layer_normalized_dss_mean_across_probes": per_layer_mean,
        "per_layer_normalized_dss_std_across_probes": per_layer_std,
        "rank_variability_per_layer": rank_variability,
        "topk_sets": {k: sorted(v) for k, v in topk_sets.items()},
        "topk_pairwise_overlap": topk_overlaps,
        "layers_in_all_three_topk": sorted(repeated_in_all_three),
        "layers_in_any_topk": sorted(all_top6),
    }

    # ---- MMD ablation (Probe A only) ----
    LOG("\n=== MMD ablation (Probe A, comparison only) ===")
    mmd_per_layer = []
    for li in range(N_LAYERS):
        x = torch.stack([s[li] for s in results["A"]["_source_pooled"]])
        y = torch.stack([s[li] for s in results["A"]["_target_pooled"]])
        mmd_per_layer.append(dssa_mmd.mmd2_biased(x, y))
    mmd_ranking = sorted(range(N_LAYERS), key=lambda i: (-mmd_per_layer[i], i))
    cosine_ranking_A = results["A"]["ranking_desc"]
    mmd_top6 = set(mmd_ranking[:K_ILLUSTRATIVE])
    cosine_top6_A = set(cosine_ranking_A[:K_ILLUSTRATIVE])
    spearman = float(np.corrcoef(
        [cosine_ranking_A.index(i) for i in range(N_LAYERS)],
        [mmd_ranking.index(i) for i in range(N_LAYERS)]
    )[0, 1])
    LOG(f"  MMD per-layer (Probe A): {[round(v,5) for v in mmd_per_layer]}")
    LOG(f"  cosine Top-{K_ILLUSTRATIVE}: {sorted(cosine_top6_A)}  |  MMD Top-{K_ILLUSTRATIVE}: {sorted(mmd_top6)}")
    LOG(f"  Top-{K_ILLUSTRATIVE} overlap: {sorted(cosine_top6_A & mmd_top6)}  |  rank-order Spearman-like corr: {spearman:.3f}")

    mmd_result = {
        "per_layer_mmd2": mmd_per_layer,
        "mmd_ranking_desc": mmd_ranking,
        "cosine_ranking_A": cosine_ranking_A,
        "topk_overlap_with_cosine": sorted(cosine_top6_A & mmd_top6),
        "rank_correlation": spearman,
    }

    # ---- Controls (definitions only, based on Probe A ranking) ----
    LOG("\n=== Controls (layer-set DEFINITIONS only - no training) ===")
    rng = random.Random(RANDOM_K_SEED)
    random_k_layers = sorted(rng.sample(range(N_LAYERS), K_ILLUSTRATIVE))
    lowest_dss_layers = sorted(cosine_ranking_A[-K_ILLUSTRATIVE:])
    early_layers = list(range(0, K_ILLUSTRATIVE))
    middle_start = (N_LAYERS - K_ILLUSTRATIVE) // 2
    middle_layers = list(range(middle_start, middle_start + K_ILLUSTRATIVE))
    late_layers = list(range(N_LAYERS - K_ILLUSTRATIVE, N_LAYERS))
    controls = {
        "K_illustrative": K_ILLUSTRATIVE,
        "note": "Layer-set DEFINITIONS for later adaptation experiments. No LoRA trained. K is illustrative, not a final choice (final K selection is validation-only, per frozen protocol).",
        "topK_by_normalized_DSS_ProbeA": sorted(cosine_top6_A),
        "random_K": {"seed": RANDOM_K_SEED, "layers": random_k_layers},
        "lowest_DSS": {"layers": lowest_dss_layers},
        "early": {"layers": early_layers},
        "middle": {"layers": middle_layers},
        "late": {"layers": late_layers},
        "K_zero": {"layers": []},
        "K_all": {"layers": list(range(N_LAYERS))},
    }
    for k, v in controls.items():
        if isinstance(v, dict) and "layers" in v:
            LOG(f"  {k}: {v['layers']}")

    # ---- save artifacts ----
    def strip_private(r):
        return {k: v for k, v in r.items() if not k.startswith("_")}

    full_output = {
        "config": {
            "N_LAYERS": N_LAYERS, "K_ILLUSTRATIVE": K_ILLUSTRATIVE,
            "BOOTSTRAP_RESAMPLES": BOOTSTRAP_RESAMPLES, "BOOTSTRAP_SEED": BOOTSTRAP_SEED,
            "RANDOM_K_SEED": RANDOM_K_SEED, "TIE_TOLERANCE": TIE_TOLERANCE,
            "checkpoint": "ibm-nasa-geospatial/Prithvi-EO-2.0-300M",
            "checkpoint_revision": "9eb1b1102806593963daa333bcc491b1c6f8562f",
        },
        "probes": {k: strip_private(v) for k, v in results.items()},
        "stability": stability,
        "mmd_ablation": mmd_result,
        "controls": controls,
    }
    with open(ARTIFACTS / "phase2a_dss_results.json", "w") as f:
        json.dump(full_output, f, indent=2, default=str)
    with open(ARTIFACTS / "phase2a_run.log", "w") as f:
        f.write("\n".join(log_lines))
    LOG(f"\n[done] wrote {ARTIFACTS / 'phase2a_dss_results.json'}")


if __name__ == "__main__":
    main()
