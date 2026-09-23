"""
DSSA sanity phase - the seven pre-registered checks from
DSSA_PREIMPLEMENTATION_CALIBRATION.md Section 7 / DSSA_IMPLEMENTATION_FREEZE.md
Section 12. Thresholds are hardcoded and must not be changed based on results.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import torch

CHECK3_TOLERANCE_ORDERS_OF_MAGNITUDE = 2       # DO NOT CHANGE
CHECK4_MIN_CROSS_SAMPLE_VARIANCE = 1e-6        # DO NOT CHANGE


@dataclass
class CheckResult:
    name: str
    passed: bool | None   # None = not executed
    detail: str
    numbers: dict = field(default_factory=dict)


def check1_forward_pass(model, x: torch.Tensor, label: str) -> CheckResult:
    try:
        with torch.no_grad():
            feats = model.forward_features(x, temporal_coords=None, location_coords=None)
        return CheckResult("check1_forward_pass", True, f"{label}: forward pass succeeded, {len(feats)} layers returned.")
    except Exception as e:
        return CheckResult("check1_forward_pass", False, f"{label}: forward pass raised {type(e).__name__}: {e}")


def check2_finite(layer_feats: list[torch.Tensor], label: str) -> CheckResult:
    bad_layers = []
    for i, t in enumerate(layer_feats):
        if not torch.isfinite(t).all():
            bad_layers.append(i)
    passed = len(bad_layers) == 0
    return CheckResult(
        "check2_finite", passed,
        f"{label}: {'all finite' if passed else f'non-finite values at layers {bad_layers}'}",
        numbers={"num_layers_checked": len(layer_feats), "bad_layers": bad_layers},
    )


def _mean_token_l2_norm(layer_feat: torch.Tensor) -> float:
    # layer_feat: (B, tokens, embed_dim) -> mean over batch and tokens of the per-token L2 norm
    return layer_feat.norm(dim=-1).mean().item()


def check3_activation_magnitude(reference_feats: list[torch.Tensor], candidate_feats: list[torch.Tensor], label: str) -> CheckResult:
    if len(reference_feats) != len(candidate_feats):
        return CheckResult("check3_activation_magnitude", False,
                            f"{label}: layer count mismatch ({len(reference_feats)} vs {len(candidate_feats)})")
    ref_norms = [_mean_token_l2_norm(t) for t in reference_feats]
    cand_norms = [_mean_token_l2_norm(t) for t in candidate_feats]
    ratios = []
    failed_layers = []
    for i, (r, c) in enumerate(zip(ref_norms, cand_norms)):
        if r == 0:
            ratios.append(float("inf"))
            failed_layers.append(i)
            continue
        ratio = c / r
        ratios.append(ratio)
        # within two orders of magnitude both directions: 10^-2 <= ratio <= 10^2
        if not (10 ** (-CHECK3_TOLERANCE_ORDERS_OF_MAGNITUDE) <= ratio <= 10 ** CHECK3_TOLERANCE_ORDERS_OF_MAGNITUDE):
            failed_layers.append(i)
    passed = len(failed_layers) == 0
    return CheckResult(
        "check3_activation_magnitude", passed,
        f"{label}: {'all layers within tolerance' if passed else f'layers out of tolerance: {failed_layers}'}",
        numbers={"reference_norms": ref_norms, "candidate_norms": cand_norms, "ratios": ratios},
    )


def check4_cross_sample_variance(pooled_reps_per_layer: list[torch.Tensor], label: str) -> CheckResult:
    """pooled_reps_per_layer: list (per layer) of (N_samples, embed_dim) pooled representations."""
    variances = []
    failed_layers = []
    for i, reps in enumerate(pooled_reps_per_layer):
        var = reps.var(dim=0).mean().item()
        variances.append(var)
        if var <= CHECK4_MIN_CROSS_SAMPLE_VARIANCE:
            failed_layers.append(i)
    passed = len(failed_layers) == 0
    return CheckResult(
        "check4_cross_sample_variance", passed,
        f"{label}: {'all layers above noise floor' if passed else f'collapsed/near-constant layers: {failed_layers}'}",
        numbers={"variances": variances},
    )


def dss_cosine_diagnostic(source_pooled: torch.Tensor, target_pooled: torch.Tensor,
                           null_pooled_a: torch.Tensor, null_pooled_b: torch.Tensor) -> dict:
    """
    FROZEN DSS definition (DSSA_PROJECT_FREEZE.md Sec F/O-C/O-D), used here ONLY
    as a diagnostic - no ranking, no layer selection, no K choice performed.

    source_pooled:  (N_source, embed_dim) pooled per-image representations at one layer
    target_pooled:  (N_target, embed_dim)
    null_pooled_a/b: two disjoint source-only splits, for the null-baseline check

    Returns raw cosine DSS and null-normalized DSS for this layer. Does not
    impose or check any "meaningful magnitude" threshold - deliberately.
    """
    eps = 1e-8

    def cosine_dss(src: torch.Tensor, tgt: torch.Tensor) -> float:
        centroid = src.mean(dim=0, keepdim=True)  # (1, D)
        centroid_n = centroid / (centroid.norm(dim=-1, keepdim=True) + eps)
        tgt_n = tgt / (tgt.norm(dim=-1, keepdim=True) + eps)
        cos_sim = (tgt_n * centroid_n).sum(dim=-1)  # (N_tgt,)
        cos_dist = 1.0 - cos_sim
        return cos_dist.mean().item()

    raw_dss = cosine_dss(source_pooled, target_pooled)
    null_value = cosine_dss(null_pooled_a, null_pooled_b)
    # bootstrap-style null spread would need many resamples; with only one
    # null draw available we report the single null value and its magnitude,
    # not a z-score - a full bootstrap requires more source data than a tiny
    # sanity batch provides. This is recorded as a limitation, not hidden.
    return {
        "raw_dss": raw_dss,
        "null_dss_single_draw": null_value,
        "null_normalized_dss_approx": (raw_dss - null_value),
    }


def check5_dss_diagnostic(layerwise_diag: list[dict], label: str) -> CheckResult:
    bad = []
    for i, d in enumerate(layerwise_diag):
        raw = d["raw_dss"]
        norm = d["null_normalized_dss_approx"]
        ok = (raw == raw) and raw != 0.0 and (raw not in (float("inf"), float("-inf"))) and (norm == norm) and (norm not in (float("inf"), float("-inf")))
        if not ok:
            bad.append(i)
    passed = len(bad) == 0
    return CheckResult(
        "check5_dss_diagnostic", passed,
        f"{label}: {'all layers produced finite, non-zero raw DSS and finite normalized DSS' if passed else f'problem at layers {bad}'}",
        numbers={"layerwise": layerwise_diag},
    )


def check6_block_coverage(layer_feats: list[torch.Tensor], expected_depth: int, expected_embed_dim: int, label: str) -> CheckResult:
    problems = []
    if len(layer_feats) != expected_depth:
        problems.append(f"expected {expected_depth} blocks, got {len(layer_feats)}")
    shapes = []
    for i, t in enumerate(layer_feats):
        shapes.append(tuple(t.shape))
        if t.shape[-1] != expected_embed_dim:
            problems.append(f"layer {i}: embed_dim {t.shape[-1]} != expected {expected_embed_dim}")
    passed = len(problems) == 0
    return CheckResult(
        "check6_block_coverage", passed,
        f"{label}: {'all blocks present with expected shape' if passed else '; '.join(problems)}",
        numbers={"shapes": shapes},
    )


def check7_procedural_audit(labels_loaded: bool, optimization_performed: bool,
                             gradients_computed: bool, target_stats_used_in_preprocessing: bool) -> CheckResult:
    violations = []
    if labels_loaded:
        violations.append("labels were loaded")
    if optimization_performed:
        violations.append("optimization was performed")
    if gradients_computed:
        violations.append("gradients were computed")
    if target_stats_used_in_preprocessing:
        violations.append("target statistics were used in preprocessing")
    passed = len(violations) == 0
    return CheckResult(
        "check7_procedural_audit", passed,
        "no violations" if passed else "; ".join(violations),
    )
