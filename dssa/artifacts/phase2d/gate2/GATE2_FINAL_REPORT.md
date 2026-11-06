# DSSA Phase 2D, Gate 2: final report (oracle layer-utility sweep)

Date: 2026-11-05.
- Analysis: `gate2/gate2_analysis.json`, produced by the frozen `gate2_analysis.py` through
  `gate2_analysis_v12.py`. That wrapper only maps eight interrupted runs to their `_a2` reruns.
- Additional exploratory contrasts (§6) were computed afterwards from the same matrix and are
  labelled as such.

## 1. Run status and integrity
- **63 of 63 Gate 2 runs are complete**: 21 layers (1–11, 13–22) × seeds 1000, 2000, 3000.
  - Together with the 12 pilot runs (K0, L0, L12, L23 × 3 seeds), the analysis reads **75 runs**.
  - Eight runs were interrupted by safety guards (INCIDENT_004 to 010). Their partial folders are
    preserved unchanged, and each was rerun under a new `_a2` ID through manifests v5 to v12.
  - No run was retried or skipped automatically.
- **Integrity checks applied by the frozen analysis to all 75 runs: 0 problems.** For each run:
  - status completed
  - 2,000 steps, with the last evaluation at step 2000
  - correct layer and seed
  - decoder and RNG hashes match the baseline
  - the backbone is unchanged after training
  - the data-stream replay matches
  - only allowed tiles were opened
  - result hash and best/final checkpoint hashes match
  - reload confusion-matrix difference = 0
- **Recomputed mIoU:** recomputed from the raw confusion matrices, it equals the stored value
  exactly (maximum difference 0.0).
- **Locked test set:** 82 result and incident records list only approved tiles. **0 of 8 locked test
  tiles were ever opened.**
- **Frozen artifacts:** frozen artifacts, frozen rankings and manifests v4–v12 are unchanged.
- **Compute:** 38.8 h of compute for the 75 runs.
  - The worst runtime was 1.27× its estimate; the limit is 1.5×.
  - Peak footprint was 8.3 GB; the limit is 11.5 GB.
  - The maximum swap growth in a completed run was 209 MB; the limit is 512 MB.
  - The maximum memory pressure level was 2 (warning), in 18 runs.

## 2. What is confirmatory and what is exploratory
| Element | Status |
|---|---|
| Frozen rankings (F, R1, R2, S20, RAW_R2, MMD_R2) and analysis scripts | Hashed before any Gate 2 training; the oracle evaluation of them is **prospective** |
| R2 as the primary selector | **Exploratory choice**, made after inspecting preliminary DSS variants (Addendum §3). Its evaluation here is prospective, but R2 was not pre-registered as *the* DSS before Phase 2D |
| Falsification criterion used for the verdict | From `DSSA_PROJECT_FREEZE.md` §B: "fails if DSS-selected layers perform no better than randomly-selected layers of the same count". No numeric Gate 2 decision threshold was frozen, so the verdict in §8 is an application of that sentence, not a pre-computed pass/fail |
| Effect of interest δ = 0.010 | Frozen before the pilot |
| Middle-layer contrasts, inverted-U fit, per-class and seed-3000 observations, top-k mean contrasts (§6) | **Exploratory**, post hoc |

## 3. Per-layer utility
Utility (U6) is pooled 6-class validation mIoU at step 2000 minus the same-seed K0. Intervals are
95%.

| Layer | s1000 / s2000 / s3000 | Mean U6 | Mean U5 | CI, t df 2 | CI, pooled t df 48 | Tile 95% (seed mean) |
|---|---|---|---|---|---|---|
| 0 | −0.0130 / −0.0134 / +0.0045 | −0.0073 | −0.0113 | [−0.033, +0.018] | [−0.019, +0.004] | [−0.021, +0.007] |
| 1 | −0.0058 / +0.0075 / +0.0215 | +0.0077 | −0.0013 | [−0.026, +0.042] | [−0.004, +0.019] | [−0.002, +0.022] |
| 2 | −0.0066 / +0.0239 / +0.0273 | +0.0149 | +0.0037 | [−0.032, +0.061] | [+0.003, +0.026] | [−0.002, +0.036] |
| 3 | −0.0059 / +0.0042 / +0.0177 | +0.0053 | −0.0019 | [−0.024, +0.035] | [−0.006, +0.017] | [−0.012, +0.025] |
| 4 | +0.0064 / +0.0249 / +0.0425 | +0.0246 | +0.0141 | [−0.020, +0.069] | [+0.013, +0.036] | [+0.010, +0.042] |
| 5 | +0.0067 / +0.0358 / +0.0341 | +0.0255 | +0.0195 | [−0.015, +0.066] | [+0.014, +0.037] | [+0.016, +0.035] |
| 6 | +0.0024 / +0.0260 / +0.0404 | +0.0230 | +0.0148 | [−0.025, +0.071] | [+0.012, +0.034] | [+0.016, +0.030] |
| 7 | +0.0020 / +0.0172 / +0.0438 | +0.0210 | +0.0119 | [−0.032, +0.074] | [+0.010, +0.033] | [+0.008, +0.033] |
| 8 | +0.0147 / +0.0277 / +0.0505 | +0.0310 | +0.0209 | [−0.014, +0.076] | [+0.020, +0.043] | [+0.020, +0.040] |
| 9 | +0.0068 / +0.0230 / +0.0367 | +0.0222 | +0.0139 | [−0.015, +0.059] | [+0.011, +0.034] | [+0.009, +0.033] |
| 10 | +0.0152 / +0.0314 / +0.0430 | +0.0299 | +0.0251 | [−0.005, +0.065] | [+0.018, +0.041] | [+0.024, +0.034] |
| 11 | +0.0207 / +0.0477 / +0.0377 | +0.0354 | +0.0318 | [+0.001, +0.069] | [+0.024, +0.047] | [+0.028, +0.042] |
| 12 | +0.0182 / +0.0304 / +0.0302 | +0.0263 | +0.0259 | [+0.009, +0.044] | [+0.015, +0.038] | [+0.019, +0.031] |
| 13 | +0.0267 / +0.0292 / +0.0512 | +0.0357 | +0.0334 | [+0.002, +0.069] | [+0.024, +0.047] | [+0.030, +0.040] |
| 14 | +0.0187 / +0.0271 / +0.0444 | +0.0301 | +0.0238 | [−0.003, +0.063] | [+0.019, +0.042] | [+0.018, +0.037] |
| 15 | +0.0243 / +0.0361 / +0.0362 | +0.0322 | +0.0298 | [+0.015, +0.049] | [+0.021, +0.044] | [+0.025, +0.039] |
| **16** | +0.0233 / +0.0391 / +0.0493 | **+0.0372** | +0.0309 | [+0.005, +0.070] | [+0.026, +0.049] | [+0.030, +0.044] |
| 17 | +0.0184 / +0.0290 / +0.0549 | +0.0341 | +0.0253 | [−0.013, +0.081] | [+0.023, +0.046] | [+0.026, +0.040] |
| 18 | +0.0184 / +0.0274 / +0.0472 | +0.0310 | +0.0308 | [−0.006, +0.068] | [+0.020, +0.043] | [+0.023, +0.036] |
| 19 | +0.0178 / +0.0405 / +0.0344 | +0.0309 | +0.0299 | [+0.002, +0.060] | [+0.019, +0.042] | [+0.021, +0.036] |
| 20 | +0.0149 / +0.0344 / +0.0295 | +0.0263 | +0.0257 | [+0.001, +0.052] | [+0.015, +0.038] | [+0.020, +0.031] |
| 21 | +0.0080 / +0.0256 / +0.0295 | +0.0210 | +0.0211 | [−0.008, +0.050] | [+0.010, +0.033] | [+0.018, +0.024] |
| 22 | +0.0167 / +0.0255 / +0.0247 | +0.0223 | +0.0250 | [+0.010, +0.034] | [+0.011, +0.034] | [+0.016, +0.027] |
| 23 | +0.0083 / +0.0166 / +0.0188 | +0.0146 | +0.0163 | [+0.001, +0.028] | [+0.003, +0.026] | [+0.011, +0.017] |

**Oracle order (mean U6):** 16, 13, 11, 17, 15, 18, 8, 19, 14, 10, 20, 12, 5, 4, 6, 22, 9, 21, 7, 2, 23, 1, 3, 0.

**Uncertainty.** Seed and tile uncertainty are reported separately and never combined.
- **Seed, per-layer t (df 2):** 9 of 24 layers have a CI that excludes 0. The median half-width is
  0.034.
- **Seed, pooled two-way:** σ_c = 0.0099, df 48, half-width 0.0115. The equal-variance assumption is
  doubtful: per-arm residual SD ranges from 0.0011 to 0.0119.
- **Tile:** the median half-width is 0.0113 for a single seed and 0.0072 for the seed mean. These
  intervals are conditional on the trained models and are descriptive.
- **Seed agreement:** Kendall's W across the three seeds is 0.73. Spearman correlations between the
  seed utility vectors are 0.75, 0.58 and 0.47. The layer ordering is moderately reproducible.
- **Higher utilities at seed 3000:** this comes from that seed's K0 being the lowest of the three
  (0.508 vs 0.526 and 0.519). The arms themselves are not higher. Utility is a same-seed difference,
  so this is handled correctly, but it inflates seed-3000 utilities uniformly.

## 4. DSS and other selectors versus the oracle (point estimates on mean U6)
| Selector | Spearman | Kendall b | Partial ρ given depth | Top-1 regret | Top-3 sum regret | Top-5 sum regret | Overlap @3 / @5 |
|---|---|---|---|---|---|---|---|
| **R2 (primary DSS)** | 0.420 | 0.312 | **0.076** | 0.015 | 0.029 | 0.059 | 0 / 0 |
| F (Phase 2B-A DSS) | 0.440 | 0.312 | 0.139 | 0.023 | 0.040 | 0.049 | 0 / 0 |
| R1 | 0.545 | 0.377 | 0.414 | 0.006 | 0.024 | 0.030 | 0 / 0.2 |
| S20 | 0.378 | 0.283 | −0.054 | 0.015 | 0.040 | 0.059 | 0 / 0 |
| Raw DSS (RAW_R2) | 0.414 | 0.304 | 0.494 | 0.045 | 0.050 | 0.058 | 0.33 / 0.4 |
| MMD (MMD_R2) | −0.077 | −0.043 | 0.079 | 0.013 | 0.053 | 0.075 | 0 / 0 |
| Lowest-DSS (reverse R2) | −0.420 | −0.312 | −0.076 | 0.045 | 0.086 | 0.129 | 0 / 0 |
| Early (shallowest first) | −0.422 | −0.304 | 0 | 0.045 | 0.093 | 0.129 | 0 / 0 |
| Late (deepest first) | 0.422 | 0.304 | 0 | 0.023 | 0.050 | 0.059 | 0 / 0 |
| Middle | **0.632** | **0.435** | **0.728** | **0.002** | **0.017** | **0.025** | 0.33 / 0.4 |
| Random (20,000 permutations) | median 0.003, 95% [−0.40, +0.40] | | | median 0.011 | median 0.034, 95% [0.009, 0.076] | median 0.053 | |
| Oracle (benchmark) | 1 | 1 | 1 | 0 | 0 | 0 | 1 / 1 |

**Where R2's regret falls in the random-selector distribution** (tile-resampled, fraction of random
picks with regret at or below R2's):
- top-1: 0.67
- top-3: 0.37
- top-5: 0.61

R2's top-k layers are therefore **not better than a random choice of the same count**. At k = 1 and
k = 5 they are slightly worse than the random median.

**Uncertainty on Spearman (95%):**

| Selector | Seed resampling (27 resamples, 10 distinct) | Tile resampling (3,125 resamples) |
|---|---|---|
| R2 | [0.23, 0.56] | [−0.15, 0.69] |
| Late | [0.21, 0.61] | [−0.15, 0.66] |
| Middle | [0.54, 0.70] | [0.43, 0.88] |
| MMD | [−0.27, 0.14] | [−0.18, 0.28] |

**R2 Spearman by seed:**
- s1000: 0.59
- s2000: 0.45
- s3000: 0.17

**Leave-one-seed-out Spearman:**

| Seed left out | R2 | Late | Middle |
|---|---|---|---|
| s1000 | 0.34 | 0.29 | 0.64 |
| s2000 | 0.36 | 0.38 | 0.67 |
| s3000 | 0.54 | 0.55 | 0.58 |

## 5. Depth confound
- **Utility and depth:** Spearman(U, depth) = 0.42.
- **Selector rankings and depth:** the frozen rankings are almost pure depth orderings. Their
  Spearman correlations with depth are:
  - F 0.95, R2 0.94, S20 0.94, R1 0.89
  - RAW −0.08, MMD −0.34
- **R2 minus Late:** the difference in Spearman is **−0.002**, with a tile 95% interval of
  [−0.029, +0.044]. Its partial correlation given depth is 0.076, and its correlation with the
  residual of utility after a linear or quadratic depth fit is 0.009 and 0.002.
- **What this means:** R2's entire association with utility is explained by depth. It adds no
  information beyond "prefer deeper layers".
- **The shape of utility over depth is an inverted U, not monotone:**
  - A quadratic in depth explains R² = 0.82; a linear fit explains 0.26.
  - Utility rises from L0 (−0.007) to a plateau at L11–L17 (+0.030 to +0.037), then falls to
    L23 (+0.015).
  - The DSS family ranks L19–L23 highest. That is exactly the declining side of the curve.
  - L23, R2's fourth choice, is 21st of 24 by utility.

## 6. Exploratory contrasts (post hoc; seed-level t, df 2)
- **R2 top-1 (L22) vs oracle top-1 (L16):** 0.0149 lower. The difference is positive at all three
  seeds (+0.007, +0.014, +0.025), but the CI is [−0.008, +0.037].
- **L23 vs L16:** 0.0226 lower, CI [+0.003, +0.042]. This interval excludes 0.
- **Mean U of R2's top-k minus the mean U of all 24 layers:**

  | k | Difference | CI |
  |---|---|---|
  | 1 | −0.002 | [−0.023, +0.019] |
  | 3 | +0.003 | [−0.016, +0.021] |
  | 5 | −0.001 | [−0.016, +0.014] |

  These are indistinguishable from the average layer.
- **Middle top-5 minus the all-layer mean:** +0.006, CI [+0.003, +0.009]. It is positive at every
  seed, but it is an unregistered heuristic chosen after seeing the inverted-U shape, so it is not
  evidence for any pre-registered claim.
- **Raw DSS:** it has the largest depth-adjusted partial correlation (0.49). However, it ranks L0, the
  worst layer, first. This is noted, not interpreted.
- **Per class (mean over layers):** clutter gains the most (+0.048 IoU) and is the fragile class
  (Pilot audit §2). That is why U6 exceeds U5 for most layers.

## 7. Limitations
1. **Single-layer oracle only (K = 1).** Each arm adapts one layer. "Top-k" sets combine
   *independently trained* single-layer utilities; joint k-layer adaptation (the K2 interactions)
   was not run.
2. **The second half of the frozen hypothesis was not tested.** No uniform-LoRA or full fine-tuning
   comparison, and no parameter-efficiency comparison, was part of Gate 2.
3. **Three seeds.** Per-layer seed CIs have a median half-width of 0.034, so neighbouring layers
   cannot be distinguished at δ = 0.010. The pooled df-48 interval assumes equal residual variance,
   which the per-arm SDs (0.001–0.012) contradict.
4. **Five validation tiles.** Tile intervals are coarse and conditional on the trained models. The
   test set was not used, so there is no held-out confirmation.
5. **Scope.** Results apply only to the L23-only decoder, LoRA r = 8 on Q/V, Prithvi-EO-2.0-300M, this
   split, step 2000, and pooled 6-class mIoU with a fragile clutter class.
6. **R2 status.** R2 was an exploratory signal choice (Addendum §3). F, the original Phase 2B-A DSS,
   behaves the same, so the conclusion does not depend on that choice.
7. **Operational.** Eight interruptions led to `_a2` reruns. The reruns are bit-exact replays of the
   same seed and data stream, as verified by the data-stream and RNG hashes, so they are not a source
   of bias. Wall-clock execution spanned several days.

## 8. Conclusion
**The original DSSA hypothesis is not supported by Gate 2.** The part Gate 2 can test is rejected
for this setup. The rest is untested.

- **What the frozen falsification criterion asks:** whether DSS-selected layers perform better than
  randomly selected layers of the same count.
- **What happened:**
  - The primary DSS ranking (R2), and the original DSS (F), chose layers whose utility is no better
    than random at k = 1, 3 and 5. R2's regret sits at the 37th to 67th percentile of random choices.
  - R2's mean top-k utility is indistinguishable from the average layer.
- **Why the positive rank correlation is not evidence for DSS:** the correlation (0.42) exists, but it
  is entirely a depth effect. R2 equals the "deepest first" rule (difference −0.002) and has
  essentially zero partial correlation once depth is controlled.
- **Where DSS points the wrong way:** it prefers the deepest layers, but utility peaks in the middle
  layers (L11–L17) and declines toward L23.
- **MMD** carries no useful signal (Spearman −0.08).
- **What does hold, and is not attributable to DSS:**
  - Layers are clearly **not** equally useful to adapt. Utility ranges from −0.007 (L0) to +0.037
    (L16), and the ordering is moderately reproducible across seeds (Kendall W 0.73).
  - This is consistent with the premise of selective adaptation. It does not show that an unlabeled
    drift score can find the useful layers.
- **Untested:** the "competitive with uniform LoRA or full fine-tuning at fewer parameters" claim.
  Gate 2 neither confirms nor refutes it.

**Confidence.** The headline (DSS ≈ depth and not better than random at top-k) is consistent across
seeds, leave-one-seed-out, tile resampling and two DSS variants. The inverted-U pattern and the
Middle-layer advantage are exploratory and need prospective confirmation before they are used as a
selection rule.

## Recommendation (for the research lead)
- Do not take DSS (R2 or F) forward as a layer selector in its current form.
- If the project continues, the options are:
  - (a) Pre-register a depth-adjusted DSS, or a middle-layer prior, and test it on new seeds or a held-out split.
  - (b) Run the K2 and uniform-LoRA comparisons before any efficiency claim.
- Both require new authorization. The final off-machine backup of these artifacts (GitHub draft
  release 431538319, private) is still pending and was not done in this step.
