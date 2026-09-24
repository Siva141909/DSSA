"""
Phase 2B-A, Part 10: non-training repeatability check.

Re-runs Probe A's EXACT configuration from Phase 2A (same files, same crop
rule, same Strategy C coefficients, same checkpoint, same DSS definition,
same bootstrap seed) and compares the freshly-computed numbers against the
stored Phase 2A artifact. No methodology change. No training. No new split.
No new K grid. This only answers: does the existing, frozen DSS computation
reproduce the same numbers when run twice on identical inputs?
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_phase2a_dss as p2a  # noqa: E402
import torch

ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS = ROOT / "artifacts" / "dss"


def main():
    with open(ARTIFACTS / "phase2a_dss_results.json") as f:
        prior = json.load(f)
    prior_A = prior["probes"]["A"]

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"[env] device={device}")
    encoder = p2a.dssa_model.load_frozen_encoder(num_frames=1, device=device)

    with open(ROOT / "artifacts" / "radiometric_transform.json") as f:
        saved = json.load(f)
    coeffs = p2a.dssa_prep.SourceFitAffine(offset=tuple(saved["offset_IR_R_G"]), scale=tuple(saved["scale_IR_R_G"]))

    source_files = [p2a.POTSDAM_DIR / n for n in prior_A["source_files"]]
    target_files = [p2a.VAIHINGEN_DIR / n for n in prior_A["target_files"]]
    null_files = [p2a.POTSDAM_DIR / n for n in prior_A["null_files"]]

    def log(m): print(m)

    fresh = p2a.run_probe("A_repeat", encoder, coeffs, source_files, target_files, null_files, "top_left", device, log)

    raw_match_exact = fresh["raw_dss"] == prior_A["raw_dss"]
    norm_match_exact = fresh["normalized_dss"] == prior_A["normalized_dss"]
    max_raw_diff = max(abs(a - b) for a, b in zip(fresh["raw_dss"], prior_A["raw_dss"]))
    max_norm_diff = max(abs(a - b) for a, b in zip(fresh["normalized_dss"], prior_A["normalized_dss"]))
    ranking_match = fresh["ranking_desc"] == prior_A["ranking_desc"]

    result = {
        "raw_dss_bitexact_match": raw_match_exact,
        "normalized_dss_bitexact_match": norm_match_exact,
        "max_abs_diff_raw_dss": max_raw_diff,
        "max_abs_diff_normalized_dss": max_norm_diff,
        "ranking_bitexact_match": ranking_match,
        "fresh_ranking": fresh["ranking_desc"],
        "prior_ranking": prior_A["ranking_desc"],
    }
    print(json.dumps(result, indent=2))
    with open(ARTIFACTS / "phase2b_a_repeatability_check.json", "w") as f:
        json.dump(result, f, indent=2, default=str)


if __name__ == "__main__":
    main()
