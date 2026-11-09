"""Writes the Stage D manifest (scenario S2, protocol v2 section 6 and v3 section 6) and locks
the Phase 3 code hash. Never overwrites. Approved by the user 2026-11-09 after Stage C.

Arms (S2 column of protocol v3 section 6), 67 new runs; the 3 Stage C K0 runs are reused:
  K0 seeds 4-10 (7), Prior-3 {13,14,15} x10, Uniform r1 (all 24) x10, Middle-3 {10,11,12} x5,
  Late-3 {21,22,23} x5, DSS-R2-3, Fisher-3, LogME-3 (frozen Stage B top-3) x5 each,
  Random-3 10 draws x 1 seed (draw j uses seed j), Uniform r8 (all 24) x5.
Seeds: seed j = 1000 j (seeds 1-3 = the Stage C seeds 1000-3000; new seeds 4-10 = 4000-10000);
LoRA A seed = seed + 7,000,000 as in Phase 2D and Stage C.
Order: Uniform r8 seed 1000 first (the highest-memory arm, as a memory canary under the same
10.5 GB stop rule), then the primary arms seed by seed (K0, Prior-3, Uniform r1), then the
secondary arms, the random draws and the remaining Uniform r8 seeds.
est_seconds (training only; the 1.5x runtime guard applies) = measured Stage C mean training
time of the earliest adapted block x (1 + 2 x 0.0044) + 150 s, as in the compute audit; uniform
LoRA = the screening estimate T_uniform_est + 150 s; K0 = measured Stage C K0 + 150 s."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import p3common as C  # noqa: E402

C.install_guards()

RANDOM_DRAW_SEED = 20261109   # fixed here, before any Stage D run; draws are not chosen by hand
EPS = 0.0044


def main():
    if C.MANIFEST_D.exists():
        raise FileExistsError(C.MANIFEST_D)
    an_path = C.ART / "stage_c_analysis.json"
    an = json.load(open(an_path))
    if an["scenario"] != "S2" or an["candidate"] is not None:
        raise RuntimeError(f"Stage C scenario is {an['scenario']}, not S2")
    frozen = json.load(open(C.SCORES_FILE))
    if C.sha256_file(C.SCORES_FILE) != C.SCORES_HASH_FILE.read_text().split()[0]:
        raise RuntimeError("frozen Stage B scores hash mismatch")
    meas = an["budget"]["measured"]
    T_l = {int(k): float(v) for k, v in meas["T_l"].items()}
    t_k0, t_unif = float(meas["T_K0"]), float(meas["T_uniform_est"])
    top3 = frozen["top3"]

    rng = np.random.default_rng(RANDOM_DRAW_SEED)
    draws = [sorted(int(x) for x in rng.choice(24, 3, replace=False)) for _ in range(10)]

    def est(layers):
        if not layers:
            return round(t_k0 + 150)
        if len(layers) == 24:
            return round(t_unif + 150)
        return round(T_l[min(layers)] * (1 + 2 * EPS) + 150)

    def entry(arm, layers, seed, rank=8, rid=None):
        layers = sorted(int(x) for x in layers)
        e = {"run_id": rid or f"p3d_{arm}_s{seed}", "K": len(layers), "layer_indices": layers, "rank": rank,
             "alpha": 2 * rank, "training_seed": seed, "lora_init_seed": seed + C.LORA_SEED_OFFSET,
             "condition_labels": [arm], "steps": 2000, "batch": 8, "crop": 224,
             "eval": "step 2000 only, final checkpoint, 8 Potsdam validation tiles, one process per tile",
             "est_seconds": est(layers)}
        e["config_hash"] = C.config_hash(e)
        return e

    S = lambda j: 1000 * j  # noqa: E731
    ALL = list(range(24))
    arms = {"PRIOR3": [13, 14, 15], "MID3": [10, 11, 12], "LATE3": [21, 22, 23],
            "DSS3": top3["DSS_R2"], "FISH3": top3["FISHER"], "LOGME3": top3["LOGME"]}
    runs = [entry("UNIF8", ALL, S(1), 8)]
    for j in range(1, 11):
        if j >= 4:
            runs.append(entry("K0", [], S(j)))
        runs.append(entry("PRIOR3", arms["PRIOR3"], S(j)))
        runs.append(entry("UNIF1", ALL, S(j), 1))
    for arm in ("MID3", "LATE3", "DSS3", "FISH3", "LOGME3"):
        for j in range(1, 6):
            runs.append(entry(arm, arms[arm], S(j)))
    for j, d in enumerate(draws, 1):
        runs.append(entry("RAND3", d, S(j), 8, rid=f"p3d_RAND3d{j:02d}_s{S(j)}"))
    for j in range(2, 6):
        runs.append(entry("UNIF8", ALL, S(j), 8))
    ids = [e["run_id"] for e in runs]
    assert len(runs) == 67 and len(set(ids)) == 67, (len(runs), len(set(ids)))
    counts = {}
    for e in runs:
        counts[e["condition_labels"][0]] = counts.get(e["condition_labels"][0], 0) + 1
    assert counts == {"UNIF8": 5, "K0": 7, "PRIOR3": 10, "UNIF1": 10, "MID3": 5, "LATE3": 5, "DSS3": 5, "FISH3": 5, "LOGME3": 5, "RAND3": 10}, counts

    m = {"stage": "D", "scenario": "S2", "version": 1, "created": time.time(),
         "authorization": "Stage D (scenario S2), approved by the user 2026-11-09 after Stage C: 'okay start but don't interrupt when the charger is unplugged'. "
                          "Measured budget 67 runs, about 43.1 h. No test opening, no LoveDA, no commit or push.",
         "primary_analysis_note": "Protocol v3 section 6, S2: C3 = Prior-3 non-inferior to Uniform-r1 (margin 0.010) on the Potsdam test, paired by seed, "
                                  "n = 10; everything else descriptive. The test opening itself needs separate approval.",
         "runs": runs, "arm_counts": counts, "reused_stage_c_runs": ["p3_K0_s1000", "p3_K0_s2000", "p3_K0_s3000"],
         "random_draws": {"rng": f"numpy.random.default_rng({RANDOM_DRAW_SEED}).choice(24, 3, replace=False), 10 times, sorted", "draws": draws,
                          "seed_rule": "draw j trains with seed 1000 j"},
         "implementation_decisions": [
             "Uniform rank 1 uses alpha = 2 (alpha = 2 x rank, the frozen Phase 2B-B convention; alpha/r = 2.0 as for rank 8 with alpha 16). "
             "Rank 1 on all 24 blocks = 98,304 LoRA parameters = K = 3 at rank 8 (exact budget match).",
             "New seeds 4-10 are 4000-10000 (seed j = 1000 j, matching seeds 1-3 = 1000-3000). LoRA A seed = seed + 7,000,000.",
             f"Random-3 draws fixed by numpy default_rng({RANDOM_DRAW_SEED}) before any Stage D run.",
             "Pre-run initialisation checks use stage_d_baseline.json (seeds 1000-3000 verified identical to Phase 2D; "
             "K0, rank-8 and rank-1 builds give the same decoder and RNG state for each seed).",
             "Uniform r8 seed 1000 runs first as the memory canary for the highest-memory arm.",
             "Charger guard replaced at the user's request: unplugging no longer stops a run; a run is stopped only if the battery "
             "falls to 25% on battery power, and a run starts on battery only at 50% or more. All other guards and limits unchanged."],
         "code_hash": C.code_hash(), "stage_c_code_snapshot_sha256sums": C.sha256_file(C.ART / "code_snapshot_stage_c" / "SHA256SUMS"),
         "split_sha256": C.sha256_file(C.SPLIT_FILE), "transform_sha256": C.sha256_file(C.TRANSFORM_FILE),
         "frozen_scores_sha256": C.sha256_file(C.SCORES_FILE), "stage_c_analysis_sha256": C.sha256_file(an_path),
         "stage_c_manifest_v5_sha256": C.sha256_file(C.MANIFEST), "stage_d_baseline_sha256": C.sha256_file(C.STAGE_D_BASELINE),
         "limits": {"stop_rule_mb": C.STOP_RULE_MB, "early_abort_mb": C.ABORT_MB, "hard_guard_mb": C.MEM_LIMIT_MB, "swap_growth_mb": C.SWAP_GROWTH_LIMIT_MB,
                    "runtime": "1.5 x est_seconds (training)", "eval_watchdog_s": 400, "reload_watchdog_s": 300,
                    "guards": "sleep 30 s, battery floor 25% on battery (2 polls), start on battery >= 50%, thermal, critical pressure, "
                              "telemetry stale 60 s, no optimizer step 300 s; no retry"},
         "budget_hours": {"stage_d": an["budget"]["scenarios"]["S2"]["stage_d_hours"]},
         "interrupted_runs": {}}
    C.write_json_atomic(C.MANIFEST_D, m)
    print("Stage D manifest", C.sha256_file(C.MANIFEST_D), len(runs), "runs", counts)
    print("random draws", draws)


if __name__ == "__main__":
    main()
