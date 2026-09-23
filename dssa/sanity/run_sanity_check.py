"""
DSSA sanity phase orchestrator.

Executes, in order:
  1. Model loading (real, always attempted).
  2. Potsdam/Vaihingen data loading (real attempt; expected to report missing
     data in this environment rather than substitute anything).
  3. IF AND ONLY IF Potsdam/Vaihingen data is present: runs the seven
     pre-registered checks for real, on real data, per
     DSSA_PREIMPLEMENTATION_CALIBRATION.md Sec 7.
  4. A clearly separate, clearly labeled INFRASTRUCTURE SMOKE TEST using the
     official HLS reference sample only. This is NOT any of the seven
     pre-registered checks and must never be reported as satisfying them -
     its only purpose is to prove the model-loading and representation-
     extraction code itself is not broken, using data that is actually
     available, and to collect Check 3's reference-side baseline ahead of
     time.

No labels are ever loaded by this script. No optimizer is constructed. No
gradients are computed (torch.no_grad() throughout). No LoRA code exists here.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import model as dssa_model  # noqa: E402
import preprocessing as dssa_prep  # noqa: E402
import diagnostics as diag  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
POTSDAM_DIR = ROOT / "data" / "potsdam_irrg"
VAIHINGEN_DIR = ROOT / "data" / "vaihingen_irrg"
REFERENCE_TIFF = ROOT / "reference_sample" / "examples" / "Mexico_HLS.S30.T13REM.2018026T173609.v2.0_cropped.tif"
ARTIFACTS = ROOT / "artifacts"
ARTIFACTS.mkdir(exist_ok=True)


def main():
    results = {"official_checks": {}, "infra_smoke_test": {}, "blockers": []}

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"[env] device = {device}")

    # --- Step 1: real model load ---
    print("[step1] loading frozen Prithvi-EO-2.0-300M encoder (num_frames=1)...")
    encoder = dssa_model.load_frozen_encoder(num_frames=1, device=device)
    n_params = sum(p.numel() for p in encoder.parameters())
    n_trainable = sum(p.numel() for p in encoder.parameters() if p.requires_grad)
    print(f"[step1] loaded. total params={n_params:,} trainable={n_trainable:,} (must be 0 - backbone frozen)")
    results["model_load"] = {"total_params": n_params, "trainable_params": n_trainable, "device": device}
    assert n_trainable == 0, "FROZEN-BACKBONE VIOLATION: encoder has trainable parameters."

    # --- Step 2: attempt Potsdam/Vaihingen ---
    potsdam_files = sorted(POTSDAM_DIR.glob("*.tif")) if POTSDAM_DIR.exists() else []
    vaihingen_files = sorted(VAIHINGEN_DIR.glob("*.tif")) if VAIHINGEN_DIR.exists() else []
    print(f"[step2] Potsdam IRRG files found: {len(potsdam_files)} (dir exists: {POTSDAM_DIR.exists()})")
    print(f"[step2] Vaihingen IRRG files found: {len(vaihingen_files)} (dir exists: {VAIHINGEN_DIR.exists()})")

    if not potsdam_files or not vaihingen_files:
        blocker = (
            "Potsdam and/or Vaihingen IRRG data not present at "
            f"{POTSDAM_DIR} / {VAIHINGEN_DIR}. The seven official pre-registered "
            "checks CANNOT be executed. No substitute dataset was used. Stopping "
            "official-check execution per instruction."
        )
        print(f"[step2] BLOCKED: {blocker}")
        results["blockers"].append(blocker)
        for i in range(1, 8):
            results["official_checks"][f"check{i}"] = None  # not executed
    else:
        # This branch is the real thing - intentionally NOT implemented with any
        # fallback/substitute logic. If data appears, this must be filled in
        # against real files, not left to silently do something else.
        raise NotImplementedError(
            "Potsdam/Vaihingen data detected but the real per-dataset checks 1-7 "
            "pipeline (radiometric fit -> input construction -> checks) is not yet "
            "wired to real files in this script. This is intentional: writing that "
            "wiring blind, without real files to validate it against, risks silent "
            "bugs. Extend this branch once real IRRG files are confirmed present."
        )

    # --- Step 4: infrastructure smoke test on the HLS reference sample only ---
    print("\n[smoke-test] INFRASTRUCTURE SMOKE TEST (HLS reference only - NOT an official check)")
    if not REFERENCE_TIFF.exists():
        msg = f"HLS reference sample not found at {REFERENCE_TIFF}"
        print(f"[smoke-test] BLOCKED: {msg}")
        results["blockers"].append(msg)
    else:
        hls = dssa_prep.load_hls_reference_tiff(str(REFERENCE_TIFF))
        x_ref = dssa_prep.build_prithvi_input_from_hls(hls).to(device)

        smoke = diag.check1_forward_pass(encoder, x_ref, "HLS-reference")
        print(f"[smoke-test] forward pass: passed={smoke.passed} :: {smoke.detail}")
        results["infra_smoke_test"]["forward_pass"] = smoke.__dict__

        if smoke.passed:
            feats = dssa_model.extract_layer_representations(encoder, x_ref)
            finite = diag.check2_finite(feats, "HLS-reference")
            print(f"[smoke-test] finite check: passed={finite.passed} :: {finite.detail}")
            results["infra_smoke_test"]["finite"] = {k: v for k, v in finite.__dict__.items() if k != "numbers"}

            coverage = diag.check6_block_coverage(feats, expected_depth=24, expected_embed_dim=1024, label="HLS-reference")
            print(f"[smoke-test] block coverage: passed={coverage.passed} :: {coverage.detail}")
            results["infra_smoke_test"]["block_coverage"] = coverage.__dict__

            ref_norms = [feat.norm(dim=-1).mean().item() for feat in feats]
            print(f"[smoke-test] reference per-layer mean token L2 norms (first 5): {[round(n, 3) for n in ref_norms[:5]]} ...")
            results["infra_smoke_test"]["reference_layer_norms"] = ref_norms

            with open(ARTIFACTS / "hls_reference_layer_norms.json", "w") as f:
                json.dump({
                    "reference_file": str(REFERENCE_TIFF),
                    "purpose": "Check 3 reference-side baseline, pre-collected ahead of Potsdam/Vaihingen comparison",
                    "per_layer_mean_token_l2_norm": ref_norms,
                }, f, indent=2)
            print(f"[smoke-test] wrote {ARTIFACTS / 'hls_reference_layer_norms.json'}")

    with open(ARTIFACTS / "sanity_metrics.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n[done] wrote {ARTIFACTS / 'sanity_metrics.json'}")
    return results


if __name__ == "__main__":
    main()
