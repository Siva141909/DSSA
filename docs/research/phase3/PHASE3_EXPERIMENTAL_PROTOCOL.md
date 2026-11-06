# Phase 3: experimental protocol (draft for approval; nothing here is authorised to run)

Labels: **[V]** verified; **[R]** recommendation; **[E]** estimate.

## 1. Settings
| Role | Setting | Status | Why |
|---|---|---|---|
| Development (already used) | Potsdam → **Vaihingen**, existing split | [V] Phase 2D complete | All selector development may use the Phase 2D oracle. **Its validation tiles are not independent evidence any more** |
| **Primary independent** | Vaihingen → **Potsdam** (target = Potsdam IRRG, 5 cm) | [V] Potsdam labels exist locally and have **never been opened**. [R] new split frozen before any label access | Uses a fresh target with fresh labels and fresh validation and test tiles, and the existing IRRG pipeline (no new band mapping). It tests generalisation to a **new target** with **opposite resolution direction** (9 → 5 cm). **Limitation:** same dataset pair, so it is not a new shift *type* |
| **Secondary independent** | **LoveDA** Urban ↔ Rural (0.3 m, RGB, 7 classes) | [V] licence CC BY-NC-SA 4.0, academic only; Google Earth terms also apply. Not downloaded | A different geography, shift type and taxonomy. **Caveats:** RGB only (no NIR), so a new band mapping (B, G, R; NIR zero) is needed; 7 classes; the official test labels are withheld (evaluation server), so a local held-out split from the official train/val must be defined |
| Optional | A second backbone (another ViT-L with 24 blocks, e.g. a DINOv2-L-class model) on the primary setting | [R] only after Stages B–D | Tests whether depth effects are backbone-specific. A second Prithvi size changes the block count and needs a depth normalisation |

[R] **The datasets do support a valid independent study,** but the primary setting is only *partly*
independent (same pair, reversed). The paper must state this. LoveDA is what makes the claim broader.
If LoveDA cannot be obtained or adapted, claims must be limited to "a new target within the ISPRS pair".

## 2. Leakage controls
1. **Freeze before labels.**
   - Define the Potsdam target split (train / probe / val / test) by a deterministic, documented rule
     **before opening any Potsdam label**. Write it to a new split manifest and record its hash.
   - Proposed rule, to be confirmed in Stage A: 38 tiles sorted, then train 20 (probe = the first 5
     of those) / val 8 / test 10.
   - Validation and test should be larger than in Phase 2D, because tile-level noise was the dominant
     uncertainty.
2. **Selectors are frozen before oracles.** Compute all candidate scores (Stage B) from images (and,
   for label-using signals, **target-train labels only**). Hash them, then run Stage C.
3. **Development vs confirmation.**
   - Phase 2D data may be used to choose candidate definitions and to fit the frozen quadratic depth
     prior.
   - Nothing fitted on the Potsdam validation tiles may be reported as confirmation.
4. **Tests.**
   - **Vaihingen locked test (8 tiles):** may be opened **once**, after Stage D's configurations are
     frozen, for a pre-registered list of configurations, by a script whose hash is recorded first.
     All results are reported whatever the outcome.
   - **Potsdam test:** the same rule.
   - Nobody tunes anything after a test is opened.
5. **Imagery-use note.** The fixed radiometric transform was fit on Potsdam *images*. Reusing it with
   Potsdam as the target is unsupervised and allowed, but must be stated. Alternatively, refit on
   Vaihingen (the new source); decide in Stage A and pre-register.

## 3. Stage A: data and protocol audit (mandatory; no training)
- Verify the Potsdam label archive integrity and class taxonomy (same 6 classes); tile sizes are
  6000×6000.
- Define and freeze the Potsdam split.
- Confirm the preprocessing and the decision about the radiometric transform.
- LoveDA: confirm licence acceptance, download, taxonomy, band mapping and local split.
- Freeze the training recipe (identical to Phase 2D):
  - LoRA r8 on Q/V; L23 decoder
  - 2,000 steps, batch 8, crop 224
  - AdamW settings from `phase2b_training_protocol.json`
  - decoder initialisation: seeded
  - LoRA A seeded independently of the global RNG (as in `models.py`)
  - deterministic data stream per seed
  - checkpoint and reload verification as in Phase 2D.
- Output: a Phase 3 manifest draft (new versioned files in a **new** code directory, so that the
  `dssa/phase2d` hash lock is not touched).

## 4. Stage B: cheap selector screening (mandatory)
- Compute candidate scores #1–#9 (see `PHASE3_RESEARCH_DIRECTION.md` §3) per setting:
  - label-free signals use source images + target-**probe** images;
  - label-using signals (#8 Fisher, #9 LogME) use **target-train labels only**;
  - Fisher uses the K0 decoder trained on the target in a decoder-only warm-up. For the primary
    setting this requires one new K0 run per seed (counted below).
- Freeze and hash all rankings **before** any Stage C run.
- [E] Compute: label-free, minutes; Fisher and LogME, under 1–2 h total.

## 5. Stage C: independent single-block oracle (mandatory, primary setting)
- **Arms:** K0 + all 24 single blocks.
  - All 24 are needed because the primary endpoints are rank associations over blocks; sampling only
    the selectors' picks cannot test them.
  - Random, Early, Middle and Late selections are *evaluations* of this oracle, not separate runs.
- **Seeds:** 3. The rank endpoint's unit is the block, and Phase 2D shows layer-level means are stable
  enough for ranking (W = 0.73).
- **Validation:** step 2,000 only (the primary metric), on 8 Potsdam validation tiles.
  - Report pooled 6-class mIoU (primary) and per-tile mIoU (for tile resampling).
  - 5-class and per-class mIoU are secondary.
- [E] Compute: 75 runs.
  - Training loop ≈ 25–37 min per run (Phase 2D).
  - Validation on 8 Potsdam tiles ≈ 8 × 36 MP ≈ 288 MP per eval; Phase 2D took ≈ 73 s per eval for
    ≈ 25 MP, so ≈ **14 min**, evaluating at step 2,000 only.
  - **≈ 45–55 h total.**
  - Uncertainty: ±30%, due to the larger tiles and evaluation-memory risk with 6000² tiles. Stage A
    must test one evaluation.

## 6. Stage D: joint adaptation (mandatory for any practical or efficiency claim)
- **K = 3** at rank 8. Exact budget match: 3 × 32,768 = **98,304** = uniform LoRA **rank 1** on all
  24 blocks (24 × 4 × 1 × 1024).
- **Arms** (primary setting):
  1. decoder-only (K0)
  2. Middle-3
  3. Late-3
  4. Random-3 (5 fixed draws)
  5. DSS-R2-3
  6. the best label-free candidate's top-3 (chosen by the pre-registered Stage C rule, §8)
  7. Fisher-3 (label-using reference)
  8. uniform rank 1 on all 24 blocks (matched budget)
  9. uniform rank 8 on all 24 blocks (786,432 LoRA parameters)
  10. *optional:* full fine-tuning, only if the 11.5 GB footprint limit allows; otherwise report it as
      not feasible on this hardware.
- **Seeds.** 10 for the confirmatory contrasts (arms 2, 6, 8 vs 1), 5 for the others. See §7 for the
  precision reasoning.
- **Cost metrics** (measured, not inferred from parameter counts):
  - wall-clock training time per 2,000 steps
  - peak process footprint and MPS driver memory
  - inference latency per 224² crop and per tile
  - trainable and total parameters.
- [E] Compute: ≈ (3 × 10 + 7 × 5 + 4 extra random draws × 5) ≈ 85 runs × ≈ 45 min ≈ **60–70 h**.
  The bigger uniform-r8 runs may be slower; measure first.

## 7. Statistics
- **Paired design.** Every comparison is within seed against same-seed K0 or a named comparator. The
  seed controls the crop stream, augmentation, decoder initialisation and LoRA A, as in Phase 2D.
- **Units.**
  - The seed is the replication unit for training-noise uncertainty.
  - Tiles are **not** independent replicates of training. Tile uncertainty is reported separately by
    resampling validation tiles conditional on the trained models, never pooled with seed variance.
- **Rank endpoints (Stage C).**
  - Spearman and Kendall-b between selector scores and mean utility over 24 blocks.
  - **Depth-controlled association:** partial Spearman controlling for **depth and depth²**, plus
    rank association with the residuals of a **frozen** quadratic prior. This fixes discrepancy D4,
    where linear partial correlation was not enough.
  - Top-k regret (k = 1, 3, 5) and percentiles against 20,000 random selections.
  - 95% intervals by seed resampling, and separately by tile resampling.
- **Precision.**
  - Phase 2D pooled σ_c = 0.0099 for a same-seed difference.
  - Half-width of a paired contrast: n = 5 seeds gives t(4)·σ_c/√5 ≈ 0.012, which exceeds δ.
    n = 10 gives t(9)·σ_c/√10 ≈ 0.0071 ≤ δ.
  - Power at δ = 0.010, α = 0.05 two-sided: ≈ 0.8 at n ≈ 10.
  - **So confirmatory joint contrasts need about 10 seeds.**
  - For rank endpoints over 24 blocks, Spearman's SE ≈ 0.21, so one setting has about 0.7 power to
    detect ρ = 0.5. **Selector conclusions must pool two settings** with a pre-registered fixed-effect
    combination of Fisher-z values, and report each setting separately.
- **Effect size and threshold.** The minimum meaningful improvement is δ = **0.010** pooled mIoU,
  already frozen in the Phase 2D addendum and not changed.
- **Multiple comparisons.** Holm correction across the confirmatory selector-vs-Middle contrasts, at
  most 3 label-free candidates plus 1 label-using reference.

## 8. Pre-registered decision rules
- **Screening pass (Stage C, per candidate).** Partial Spearman given depth and depth² ≥ **0.30**, with
  the seed-resampled 95% interval excluding 0, **and** top-3 regret ≤ the Middle rule's.
  - The **single** best passing label-free candidate (ties broken by partial ρ) goes to Stage D.
  - If none passes, Stage D runs without arm 6, and the paper is Path 2.
- **Confirmatory claim (Stage D, then the locked tests).** The candidate-3 minus Middle-3 paired
  difference must be ≥ δ, with the Holm-adjusted 95% CI above 0, in the primary setting. Its sign must
  be confirmed on the Potsdam test and on the Vaihingen locked test (if opened for this). Only then may
  "beats a depth prior" be claimed.
- **Efficiency claim.** Candidate-3 must be ≥ uniform-r1 minus δ in quality, *and* better in at least
  one measured cost. If not, no efficiency claim.
- **Stop or continue.**
  - Stop Stage C after the first 3 blocks × 1 seed if the K0 mIoU on Potsdam is below an agreed floor
    (pipeline failure), or if the evaluation exceeds the memory limits.
  - Do **not** add seeds or arms after seeing results except through a new versioned manifest with a
    stated reason.
  - If Stage C shows no candidate passing and the depth prior also fails (ρ < 0.3), stop and report
    hypothesis F/G (a setting-dependent utility) before spending Stage D compute.

## 9. Compute summary [E]
| Stage | Runs | Hours (on this Mac, from Phase 2D rates) | Mandatory? |
|---|---|---|---|
| A | 0 (+ 1 evaluation memory test) | < 2 | Yes |
| B | 3 K0 warm-ups (reused as Stage C K0) | < 3 | Yes |
| C | 75 | 45–55 | Yes |
| D | ≈ 85 | 60–70 | Yes for practical claims; the fallback paper can stop after C |
| E: LoveDA replication (C only) | 75 | 40–60 (RGB, smaller images; unknown) | Strongly recommended |
| E: second backbone | 75 + | unknown | Optional |

**Totals:** about **105–125 h** for A–D, or about **150–185 h** with the LoveDA oracle. That's 1–2
weeks of continuous running, given the power and sleep incidents seen in Phase 2D (see the risk
register).
