"""
DSSA Phase 1B, Steps 1-3: Strategy C fitting (Potsdam-only), real-data input
construction, and the seven pre-registered sanity checks - executed on the
real, staged ISPRS Potsdam (source) / Vaihingen (target) imagery.

Frozen, not modified: dataset pair, checkpoint/revision, band mapping,
Strategy C's mathematical definition, T=1, normalization contract, DSS
definition, sanity thresholds.

Memory/compute note: source tiles are up to 6000x6000 px. A full-resolution
forward pass is computationally infeasible on this hardware regardless of
memory (ViT self-attention is O(tokens^2); 6000x6000 at patch=16 is ~140,625
tokens per frame - not a memory limit, an intractable compute cost on any
single machine of this class). The seven checks were already specified
(DSSA_PREIMPLEMENTATION_CALIBRATION.md Sec 7) to run on "a small batch (order
8-16 tiles)" - so this script extracts one deterministic 224x224 CROP (native
pixels, no resizing/interpolation) per selected source file, chosen by a
fixed rule decided before running anything (top-left corner) - not a
results-based selection. Cropping is not "altering imagery to fit memory" in
the sense the instructions warn against (which is about resizing/warping
pixel content) - it is the same tiling geometry the model's own official
inference.py uses (fixed-size windows at native resolution).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import torch
import tifffile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import model as dssa_model          # noqa: E402
import preprocessing as dssa_prep   # noqa: E402
import diagnostics as diag          # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
POTSDAM_DIR = ROOT / "data" / "potsdam_irrg"
VAIHINGEN_DIR = ROOT / "data" / "vaihingen_irrg"
ARTIFACTS = ROOT / "artifacts"
ARTIFACTS.mkdir(exist_ok=True)

CROP = 224  # checkpoint's native img_size - matches DSSA_IMPLEMENTATION_FREEZE.md Sec 3
CROP_ORIGIN = (0, 0)  # fixed, deterministic top-left crop, decided before running anything

N_SOURCE = 16   # Potsdam files used as the "source" set for the real DSS (Sec Check 5)
N_TARGET = 16   # Vaihingen files used as the "target" set
N_NULL_A = 8    # disjoint Potsdam files, null-baseline split A
N_NULL_B = 8    # disjoint Potsdam files, null-baseline split B (source-vs-source control)


def list_files(d: Path) -> list[Path]:
    return sorted(d.glob("*.tif"))


def load_irrg_crop(path: Path) -> np.ndarray:
    """Reads one file and returns a single deterministic (CROP, CROP, 3) IRRG crop, native pixels."""
    arr = tifffile.imread(str(path))  # (H, W, 3), uint8, order = IR, R, G per ISPRS spec
    y0, x0 = CROP_ORIGIN
    crop = arr[y0:y0 + CROP, x0:x0 + CROP, :]
    if crop.shape[:2] != (CROP, CROP):
        raise ValueError(f"{path.name}: crop shape {crop.shape[:2]} != expected ({CROP},{CROP}) "
                          f"- source image too small for the fixed crop origin/size.")
    return crop


def pool_patch_tokens(layer_feat: torch.Tensor) -> torch.Tensor:
    """(1, tokens_incl_cls, embed_dim) -> (embed_dim,), mean over patch tokens only (excludes cls, index 0),
    per the frozen DSS pooling definition (DSSA_PROJECT_FREEZE.md Sec O-A)."""
    return layer_feat[0, 1:, :].mean(dim=0)


def main():
    log = []

    def LOG(msg):
        print(msg)
        log.append(msg)

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    LOG(f"[env] device={device}")

    # ---------------- Step 1: model ----------------
    LOG("[model] loading frozen Prithvi-EO-2.0-300M encoder (num_frames=1)...")
    encoder = dssa_model.load_frozen_encoder(num_frames=1, device=device)
    n_trainable = sum(p.numel() for p in encoder.parameters() if p.requires_grad)
    LOG(f"[model] loaded. trainable_params={n_trainable} (must be 0)")
    assert n_trainable == 0

    potsdam_files = list_files(POTSDAM_DIR)
    vaihingen_files = list_files(VAIHINGEN_DIR)
    LOG(f"[data] Potsdam files found: {len(potsdam_files)}")
    LOG(f"[data] Vaihingen files found: {len(vaihingen_files)}")
    assert len(potsdam_files) == 38, f"expected 38 Potsdam files, found {len(potsdam_files)}"
    assert len(vaihingen_files) == 33, f"expected 33 Vaihingen files, found {len(vaihingen_files)}"

    # ---------------- Step 1: Strategy C, Potsdam-only ----------------
    LOG("\n[strategyC] fitting source-only affine transform on ALL 38 Potsdam files (full-resolution pixel stats)...")
    LOG("[strategyC] Vaihingen files referenced in this step: 0 (verified by construction - "
        "the generator below iterates potsdam_files exclusively)")

    def potsdam_array_stream():
        # Yields one full-resolution array at a time - never holds more than one
        # 6000x6000x3 image in memory simultaneously (memory-safe streaming fit).
        for f in potsdam_files:
            arr = tifffile.imread(str(f))
            assert arr.shape[-1] == 3 and arr.dtype == np.uint8
            yield arr

    coeffs = dssa_prep.fit_source_affine(potsdam_array_stream())

    transform_artifact = {
        "strategy": "Strategy C - source-fit-only affine (DSSA_PREIMPLEMENTATION_CALIBRATION.md Sec 3)",
        "fit_on": "potsdam_source_only",
        "n_potsdam_files_used": len(potsdam_files),
        "n_vaihingen_files_used": 0,
        "offset_IR_R_G": list(coeffs.offset),
        "scale_IR_R_G": list(coeffs.scale),
        "frozen": True,
        "applied_to": ["potsdam", "vaihingen"],
        "refit_per_dataset": False,
    }
    with open(ARTIFACTS / "radiometric_transform.json", "w") as fjson:
        json.dump(transform_artifact, fjson, indent=2)
    LOG(f"[strategyC] fitted. offset(IR,R,G)={coeffs.offset} scale(IR,R,G)={coeffs.scale}")
    LOG(f"[strategyC] wrote {ARTIFACTS / 'radiometric_transform.json'}")

    # ---------------- Step 2: deterministic sample selection ----------------
    source_files = potsdam_files[:N_SOURCE]
    null_a_files = potsdam_files[N_SOURCE:N_SOURCE + N_NULL_A]
    null_b_files = potsdam_files[N_SOURCE + N_NULL_A:N_SOURCE + N_NULL_A + N_NULL_B]
    target_files = vaihingen_files[:N_TARGET]
    LOG(f"\n[samples] source (Potsdam) = {[f.name for f in source_files]}")
    LOG(f"[samples] null_a (Potsdam, disjoint) = {[f.name for f in null_a_files]}")
    LOG(f"[samples] null_b (Potsdam, disjoint) = {[f.name for f in null_b_files]}")
    LOG(f"[samples] target (Vaihingen) = {[f.name for f in target_files]}")
    assert set(source_files).isdisjoint(null_a_files) and set(source_files).isdisjoint(null_b_files) \
        and set(null_a_files).isdisjoint(null_b_files), "sample groups must be disjoint"

    def build_input_for_file(path: Path) -> torch.Tensor:
        crop = load_irrg_crop(path)                 # (224,224,3) uint8, native pixels
        calibrated = coeffs.apply(crop)              # frozen Strategy C, same formula for both datasets
        return dssa_prep.build_prithvi_input(calibrated)  # (1,6,1,224,224)

    def run_group(files: list[Path], label: str):
        """Returns list of per-layer lists of representations (one entry per file)."""
        per_file_layers = []
        for f in files:
            x = build_input_for_file(f).to(device)
            feats = dssa_model.extract_layer_representations(encoder, x)
            per_file_layers.append([t.cpu() for t in feats])
            LOG(f"[forward] {label}: {f.name} OK ({len(feats)} layers)")
        return per_file_layers

    # ---------------- Step 3: Check 1 - forward pass ----------------
    LOG("\n[check1] forward pass on real Potsdam(source) and Vaihingen(target) crops...")
    try:
        source_layers = run_group(source_files, "Potsdam-source")
        check1_source = diag.CheckResult("check1_forward_pass", True, f"Potsdam-source: {len(source_files)}/{len(source_files)} crops passed")
    except Exception as e:
        check1_source = diag.CheckResult("check1_forward_pass", False, f"Potsdam-source FAILED: {type(e).__name__}: {e}")
        LOG(f"[check1] FAILED on Potsdam-source: {e}")
        source_layers = None

    try:
        target_layers = run_group(target_files, "Vaihingen-target")
        check1_target = diag.CheckResult("check1_forward_pass", True, f"Vaihingen-target: {len(target_files)}/{len(target_files)} crops passed")
    except Exception as e:
        check1_target = diag.CheckResult("check1_forward_pass", False, f"Vaihingen-target FAILED: {type(e).__name__}: {e}")
        LOG(f"[check1] FAILED on Vaihingen-target: {e}")
        target_layers = None

    results = {"check1": {"source": check1_source.__dict__, "target": check1_target.__dict__}}

    if source_layers is None or target_layers is None:
        LOG("\n[STOP] Check 1 failed - per the frozen failure rule, stopping before any further check.")
        finalize(results, log, verdict="RED", reason="Check 1 (forward pass) failed on real data.")
        return

    # null groups (Potsdam only, for Check 5's source-vs-source baseline)
    null_a_layers = run_group(null_a_files, "Potsdam-null_a")
    null_b_layers = run_group(null_b_files, "Potsdam-null_b")

    # ---------------- Check 2: finite ----------------
    LOG("\n[check2] finiteness...")
    all_bad = {}
    for label, group in [("source", source_layers), ("target", target_layers),
                          ("null_a", null_a_layers), ("null_b", null_b_layers)]:
        for i, feats in enumerate(group):
            r = diag.check2_finite(feats, f"{label}[{i}]")
            if not r.passed:
                all_bad[f"{label}[{i}]"] = r.detail
    check2 = diag.CheckResult("check2_finite", len(all_bad) == 0,
                               "all finite" if not all_bad else f"non-finite in: {all_bad}")
    LOG(f"[check2] passed={check2.passed} :: {check2.detail}")
    results["check2"] = check2.__dict__

    # ---------------- Check 6: block coverage (one representative sample) ----------------
    LOG("\n[check6] block coverage...")
    check6 = diag.check6_block_coverage(source_layers[0], expected_depth=24, expected_embed_dim=1024, label="Potsdam-source[0]")
    LOG(f"[check6] passed={check6.passed} :: {check6.detail}")
    results["check6"] = check6.__dict__

    # ---------------- Check 3: activation magnitude vs HLS reference ----------------
    LOG("\n[check3] activation magnitude vs. HLS reference baseline...")
    ref_path = ARTIFACTS / "hls_reference_layer_norms.json"
    if not ref_path.exists():
        LOG("[check3] BLOCKED: hls_reference_layer_norms.json not found (expected from Phase 1).")
        check3 = diag.CheckResult("check3_activation_magnitude", None, "reference baseline artifact missing")
    else:
        ref_norms = json.load(open(ref_path))["per_layer_mean_token_l2_norm"]
        # Compare norms directly (not via check3_activation_magnitude's tensor-pair signature),
        # since the reference was saved as norms only (Phase 1), not raw tensors.
        def norms_of(layers): return [feat.norm(dim=-1).mean().item() for feat in layers]

        bad = []
        details_by_group = {}
        for label, group in [("source", source_layers), ("target", target_layers)]:
            group_bad = []
            group_ratios_all = []
            for i, feats in enumerate(group):
                cand_norms = norms_of(feats)
                ratios = []
                for li, (r, c) in enumerate(zip(ref_norms, cand_norms)):
                    ratio = c / r if r != 0 else float("inf")
                    ratios.append(ratio)
                    if not (10 ** -diag.CHECK3_TOLERANCE_ORDERS_OF_MAGNITUDE <= ratio <= 10 ** diag.CHECK3_TOLERANCE_ORDERS_OF_MAGNITUDE):
                        group_bad.append((i, li, ratio))
                group_ratios_all.append(ratios)
            details_by_group[label] = {"ratios_per_sample": group_ratios_all, "out_of_tolerance": group_bad}
            bad.extend([(label, *b) for b in group_bad])
        check3 = diag.CheckResult("check3_activation_magnitude", len(bad) == 0,
                                   "all samples within 2 orders of magnitude of HLS reference" if not bad
                                   else f"out-of-tolerance entries: {bad}",
                                   numbers=details_by_group)
    LOG(f"[check3] passed={check3.passed} :: {check3.detail}")
    results["check3"] = check3.__dict__

    # ---------------- Check 4: cross-sample variance ----------------
    LOG("\n[check4] cross-sample pooled-representation variance...")
    check4_results = {}
    for label, group in [("source", source_layers), ("target", target_layers)]:
        n_layers = len(group[0])
        pooled_per_layer = []
        for li in range(n_layers):
            pooled = torch.stack([pool_patch_tokens(sample[li]) for sample in group])  # (N_samples, embed_dim)
            pooled_per_layer.append(pooled)
        r = diag.check4_cross_sample_variance(pooled_per_layer, label)
        check4_results[label] = r.__dict__
        LOG(f"[check4] {label}: passed={r.passed} :: {r.detail}")
    check4_passed = all(v["passed"] for v in check4_results.values())
    results["check4"] = {"passed": check4_passed, "by_group": check4_results}

    # ---------------- Check 5: DSS diagnostic ----------------
    LOG("\n[check5] DSS diagnostic (cosine, frozen definition, diagnostic only - no ranking/selection)...")
    n_layers = len(source_layers[0])
    layerwise_diag = []
    for li in range(n_layers):
        src_pooled = torch.stack([pool_patch_tokens(s[li]) for s in source_layers])
        tgt_pooled = torch.stack([pool_patch_tokens(s[li]) for s in target_layers])
        na_pooled = torch.stack([pool_patch_tokens(s[li]) for s in null_a_layers])
        nb_pooled = torch.stack([pool_patch_tokens(s[li]) for s in null_b_layers])
        d = diag.dss_cosine_diagnostic(src_pooled, tgt_pooled, na_pooled, nb_pooled)
        d["layer"] = li
        layerwise_diag.append(d)
    check5 = diag.check5_dss_diagnostic(layerwise_diag, "Potsdam-vs-Vaihingen")
    LOG(f"[check5] passed={check5.passed} :: {check5.detail}")
    results["check5"] = check5.__dict__

    # ---------------- Check 7: procedural audit ----------------
    LOG("\n[check7] procedural/leakage audit...")
    check7 = diag.check7_procedural_audit(
        labels_loaded=False,               # no *_label.tif / gts_for_participants path ever opened in this script
        optimization_performed=False,      # no torch.optim constructed anywhere
        gradients_computed=False,          # extract_layer_representations runs under torch.no_grad()
        target_stats_used_in_preprocessing=False,  # Strategy C fit exclusively on potsdam_full_arrays
    )
    LOG(f"[check7] passed={check7.passed} :: {check7.detail}")
    results["check7"] = check7.__dict__

    # ---------------- verdict ----------------
    all_checks = [check1_source.passed, check1_target.passed, check2.passed, check6.passed,
                  check3.passed if check3.passed is not None else False,
                  check4_passed, check5.passed, check7.passed]
    if all(c is True for c in all_checks):
        verdict = "GREEN"
        reason = "All seven registered checks passed on the real Potsdam/Vaihingen data."
    elif any(c is False for c in [check1_source.passed, check1_target.passed, check2.passed, check6.passed,
                                    check4_passed, check5.passed, check7.passed]) or check3.passed is False:
        verdict = "RED"
        reason = "One or more registered checks failed."
    else:
        verdict = "YELLOW"
        reason = "Execution incomplete (e.g. Check 3 reference artifact missing)."

    finalize(results, log, verdict=verdict, reason=reason)


def finalize(results, log, verdict, reason):
    out = {"results": results, "verdict": verdict, "reason": reason}
    with open(ARTIFACTS / "real_data_sanity_metrics.json", "w") as f:
        json.dump(out, f, indent=2, default=str)
    with open(ARTIFACTS / "real_data_sanity_run.log", "w") as f:
        f.write("\n".join(log))
    print(f"\n[VERDICT] {verdict} — {reason}")
    print(f"[artifacts] wrote {ARTIFACTS / 'real_data_sanity_metrics.json'} and real_data_sanity_run.log")


if __name__ == "__main__":
    main()
