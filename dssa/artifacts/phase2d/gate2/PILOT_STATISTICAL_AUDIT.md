# Phase 2D pilot: statistical audit (Gate 2, pre-training)

Date: 2026-11-03. Source: `gate2/pilot_statistical_audit.json`, produced by
`phase2d/pilot_stats_audit.py`. The original pilot report and
`pilot_analysis.json` are preserved unchanged; this document records corrections.

## 1. Recalculation from raw confusion matrices
- Every pilot mIoU was recomputed from the five per-tile validation confusion
  matrices at step 2000. The recomputation matches the frozen evaluator's stored
  value, the run's validation history and `pilot_analysis.json` exactly
  (maximum absolute difference 0.0 across all 12 runs, 6-class and 5-class).
- The paired utilities in the pilot report are confirmed.

## 2. Metric definitions (verified)
- **6-class mIoU:** the five tile matrices are summed into one pooled matrix, then
  per-class IoU = TP / (TP + FP + FN) is averaged over all six classes. The
  frozen evaluator uses a nan-mean, but no class had a zero denominator in any run,
  so it is a plain six-class mean.
- **5-class mIoU:** the same pooled matrix, averaged over classes 0–4. It excludes
  clutter (index 5).
- Clutter is present in the ground truth (444,163 validation pixels) but is rarely
  predicted, so its IoU is between 0.000 and 0.092 across the 12 runs. This lowers the 6-class figure and makes
  the clutter column fragile.

## 3. Seed-level utility (step 2000, 6-class, versus same-seed K0)
| Layer | Seeds 1000 / 2000 / 3000 | Mean | SD (df 2) | 95% CI, t df 2 | 95% CI, pooled t df 6 |
|---|---|---|---|---|---|
| L0 | −0.0130 / −0.0134 / +0.0045 | −0.0073 | 0.0102 | [−0.0327, +0.0181] | [−0.0179, +0.0033] |
| L12 | +0.0182 / +0.0304 / +0.0302 | +0.0263 | 0.0070 | [+0.0089, +0.0437] | [+0.0157, +0.0369] |
| L23 | +0.0083 / +0.0166 / +0.0188 | +0.0146 | 0.0055 | [+0.0009, +0.0283] | [+0.0040, +0.0252] |

| Contrast | Mean | 95% CI, t df 2 | 95% CI, pooled t df 6 |
|---|---|---|---|
| L12 − L23 | +0.0117 | [+0.0067, +0.0167] | [+0.0011, +0.0223] |
| L23 − L0 | +0.0219 | [+0.0023, +0.0414] | [+0.0113, +0.0325] |
| L12 − L0 | +0.0336 | [+0.0104, +0.0567] | [+0.0230, +0.0442] |

- **Per-contrast (df 2):** uses only the three differences for that contrast,
  with t(0.975, 2) = 4.303. It makes no assumption about other arms.
- **Pooled (df 6):** uses the two-way arm + seed residual,
  σ_e = 0.0053, so σ_c = √2·σ_e = 0.0075, with t(0.975, 6) = 2.447. It assumes that every arm
  has the same residual variance.
- σ_c has a 95% interval of [0.0048, 0.0165] (χ², df 6). The noise estimate itself
  is imprecise.

## 4. Corrections to the pilot report
**C1. The 95% half-width of 0.0085 used the normal quantile 1.96.** The value is
reproduced as 1.96 × 0.0075 / √3. With three paired seeds a t quantile is
required:

| Basis | Half-width for one contrast with 3 seeds |
|---|---|
| Reported (z = 1.96) | 0.0085 |
| Pooled pilot σ, t df 6 | **0.0106** |
| Per-contrast, t df 2 (L0 / L12 / L23 vs K0) | 0.0254 / 0.0174 / 0.0137 |
| Pooled t df 6 at the upper 95% limit of σ_c | 0.0233 |

**C2. The claim that three seeds resolve the 0.010 effect of interest is not
supported.** The corrected half-width is above 0.010 on every basis.

A half-width of δ is also a weak standard: it gives only about 50% power to detect a
true effect of exactly δ. The estimated power to detect δ = 0.010 with 3 seeds, two-sided α = 0.05, at the point σ_c, is:
- 27% per contrast (df 2)
- 49% with the pooled pilot residual (df 6)
- 62% if Gate 2's pooled residual (df 48) holds, which requires equal variance across all 25 arms

**C3. Seeds required (corrected):**

| | z method (reported) | t, per contrast (df r−1) | t, σ from pilot (df 6) | t, Gate 2 pooled (df 24(r−1)) |
|---|---|---|---|---|
| Half-width ≤ 0.010, point σ_c | 3 | 5 | 4 | 3 |
| 80% power at 0.010, point σ_c | 5 | 7 | — | 5 |
| Half-width ≤ 0.010, upper σ_c | 11 | 13 | 17 | 11 |
| 80% power at 0.010, upper σ_c | 22 | 24 | — | 22 |

**C4. Decision-aid band.** The frozen addendum defines r_prec with 1.96, which gives 3,
in the "add seeds" band (2–4). A t-based version gives 4 with the pilot's df 6
(still "add seeds") or 5 per contrast, which would fall in the "stop or redesign"
band (above 4). The frozen rule is not redefined here; this is reported so the
research lead can weigh it.

**C5. Tile half-width.** The reported median tile half-width, 0.0104, pooled the nine
layer-versus-K0 intervals with three L23-versus-L0 intervals. For the nine
layer-versus-K0 intervals alone, the median is 0.0092. The individual intervals are reproduced
exactly.

## 5. Seed and tile uncertainty kept separate
- **Seed uncertainty** (Section 3) covers retraining with a different decoder initialization,
  crop stream, augmentation and LoRA A. It is the relevant uncertainty for the
  question "does adapting layer ℓ help?"
- **Tile uncertainty** resamples the five validation tiles (all 3,125 ordered
  resamples) for a fixed trained model. It is conditional on the trained model and
  answers a different question: how much the score depends on which tiles are evaluated. With only
  five tiles, percentile intervals are coarse and probably too narrow. They are
  descriptive.
- The two are not added or combined anywhere. No significance claims are made.

## 6. Statements in the pilot report that stand
- The utilities, their signs and the per-seed ordering L12 > L23 > L0 hold at every seed.
- L0's utility interval includes zero on both bases.
- L12's and L23's seed intervals exclude zero, but only just for L23 at df 2,
  where the lower limit is +0.0009.
- L12 cannot be said to exceed δ: its lower t(df 2) limit is 0.0089.
- The L12 − L23 difference is positive at all three seeds, but its df-6 interval
  nearly reaches zero (lower limit +0.0011).

## 7. Consequence for Gate 2
At three seeds, Gate 2 can separate layers whose utilities differ by well over
about 0.02. It cannot reliably resolve differences of 0.010 between individual layers.
The pooled df-48 half-width of 0.0087 holds only if the residual variance is equal
across layers. Gate 2 reports the per-layer residual SDs so that this can be checked. δ = 0.010 is
unchanged.
