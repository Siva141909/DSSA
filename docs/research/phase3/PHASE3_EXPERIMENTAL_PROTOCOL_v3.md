# Phase 3: experimental protocol, v3

Revision history:
- v1: the first draft.
- v2: the red-team corrections.
- **v3 (2026-11-06):**
  - the GSD operator corrected;
  - the three Stage D scenarios reconciled;
  - the independence assumption removed;
  - the measured memory and timing included (`PHASE3_MEASUREMENTS_2026-11-06.md`).

v1 and v2 are kept unchanged. **v3 supersedes v2 only in the sections below.** Every other section of
v2 (§1–§3, §5 except the gate wording, and §8) applies unchanged.

## §4 (replaces the v2 GSD-perturbation definition): GSD-perturbation sensitivity
**Purpose.** Simulate, on *source* images only, the change in ground sampling distance (GSD) that the
model meets in the target. No target data and no labels are used.

**The physical fact.** With a fixed 224 × 224 model input:
- a GSD change alters the **ground footprint per crop** and the **size of objects in pixels**;
- for coarsening, it also alters the **high-frequency content**.

A crop with GSD g covers 224·g on the ground. To make a source crop (GSD g_s) look like a target crop
(GSD g_t), take a source window of n = round(224·g_t / g_s) pixels, which covers the same ground as a
224-pixel target crop, and resample it to 224 × 224. The effective GSD becomes g_s·n/224 ≈ g_t.

| Direction | Role | g_s → g_t | Source window n | Output | Effective GSD | Ground footprint | Interpolation |
|---|---|---|---|---|---|---|---|
| **Vaihingen → Potsdam** | Primary | 9 → 5 cm | round(224·5/9) = **124 px** | 224 × 224 | 9·124/224 = **4.98 cm** | 11.16 m (a native Potsdam crop covers 11.20 m; −0.4%) | **Bilinear up-sampling**, `align_corners=False`, no antialias (it is up-sampling) |
| Potsdam → Vaihingen | Development only | 5 → 9 cm | round(224·9/5) = **403 px** | 224 × 224 | 5·403/224 = **9.00 cm** | 20.15 m (native Vaihingen crop 20.16 m) | **Antialiased bilinear down-sampling** (`antialias=True`) |

- **Score.** For each source image x and each of the 9 Gate 0 crop centres c:
  - x_c = the native 224² crop at c;
  - g(x)_c = the n² window at c resampled to 224².
  - s_ℓ = mean over x and c of ‖f_ℓ(g(x)_c) − f_ℓ(x_c)‖₂ / ‖f_ℓ(x_c)‖₂, where f_ℓ is the pooled token
    output of block ℓ (the Gate 0 representation).
  - Both inputs pass through the identical fixed preprocessing.
  - If a 403-pixel window (development direction) at a Gate 0 crop centre would cross a tile border,
    the window is shifted inwards by the minimum amount, and that shift is applied to the native crop
    too. The crop positions themselves must be re-read from `gate0_dss.py` when this is implemented.
- **What v2 got wrong.** v2 specified "down-sample by 9/5 and up-sample back" for the primary direction.
  - That **coarsens an image that is already the coarser one**. Vaihingen is 9 cm; the target is the
    finer 5 cm.
  - The round trip **restores the original pixel scale**, so it simulates blur only, not the change of
    object scale that a fixed-size crop sees.
  - The corrected operator matches the **scale and footprint** in both directions, and also the
    **information loss** in the down-sampling direction.
- **Limitation.** In the up-sampling direction (9 → 5 cm) the operator cannot create the fine detail
  that real Potsdam pixels contain. It models the scale change but not the gain in sharpness. This is
  stated in any paper; no further operators are added (to avoid metric fishing).

## §5 gate wording (replaces the v2 statement)
- The Stage C screening gate is **non-inferential**. Under the Phase 2D noise model, an uninformative
  selector passes in about 7–8% of simulations per setting.
- **LoveDA is a replication requirement, not a statistical correction.** A method claim needs the
  candidate to pass the gate on Potsdam **and**, separately, on LoveDA, plus contrast C1 on the Potsdam
  test.
- **No joint false-positive probability is claimed.** The two settings share the backbone, the recipe,
  the candidate definitions and the investigators' choices, so their errors are not known to be
  independent and the per-setting rates must not be multiplied.

## §6 (replaces v2 §6 totals): Stage D in three pre-registered scenarios
The scenario is fixed by Stage C outcomes using v2's rules: a candidate passes the gate; or
Spearman(p, Ū) ≥ 0.3 (the depth prior transfers).

The per-run cost uses measured rates:
- **training:** the Phase 2D training time of the earliest adapted block (uniform LoRA: **1,673 s,
  measured**);
- **evaluation:** in a **separate process**, 8 validation tiles × 116 s (**measured**) = 928 s;
- **overhead:** 90 s.

Arms are as in v2 §6.

| Arm | S1: candidate passes | S2: no candidate, prior transfers | S3: no candidate, prior fails |
|---|---|---|---|
| 1 K0 (seeds 4–10 new; 1–3 reused from Stage C) | 7 | 7 | 7 |
| 2 Prior-3 {14, 13, 15} | 10 | 10 | 10 |
| 3 Candidate-3 | 10 | — | — |
| 4 Uniform r1 (all 24, 98,304) | 10 | 10 | 10 |
| 5 Middle-3 {11, 12, 10} | 5 | 5 | 5 |
| 6 Late-3 | 5 | 5 | — |
| 7 DSS-R2-3 | 5 | 5 | — |
| 8 Fisher-3 | 5 | 5 | — |
| 9 LogME-3 | 5 | 5 | — |
| 10 Random-3 (10 draws × 1 seed) | 10 | 10 | 10 |
| 11 Uniform r8 (all 24, 786,432) | 5 | 5 | — |
| **New Stage D runs** | **77** | **67** | **42** |
| Reused K0 runs (from Stage C) | 3 | 3 | 3 |
| **Models in the Potsdam test opening** | **80** | **70** | **45** |
| **Stage D compute** | **47.4 h** | **41.4 h** | **26.5 h** |
| **Potsdam test compute** (10 tiles × 116 s + 90 s per model) | **27.8 h** | **24.3 h** | **15.6 h** |

**Primary analyses by scenario** (S2 and S3 are proposed and need approval, D23):
- **S1:** C1 (Candidate-3 − Prior-3 ≥ δ) and C2 (Candidate-3 non-inferior to Uniform-r1, margin δ),
  with Holm correction.
- **S2:** C3 (Prior-3 non-inferior to Uniform-r1, margin δ), a single primary contrast. This tests
  whether a frozen depth prior is as good as uniform LoRA at a matched budget. Everything else is
  descriptive.
- **S3:** no confirmatory claim. All arms are descriptive, and hypotheses F and G are reported.

## §9 (amends v2 §9): test-opening counts
- The Potsdam test opening evaluates **all** Stage D models of the realised scenario (80, 70 or 45), in
  a separate evaluation process, one opening.
- The Vaihingen locked-test opening is unchanged: 75 Phase 2D final checkpoints, ≈ 2.7 h.
- The forbidden uses are unchanged.

## §10 (replaces v2 §10): compute by scenario (measured rates)
| Item | S1 | S2 | S3 |
|---|---|---|---|
| Stage A (done in part) + Stage B | ≈ 2 h | ≈ 2 h | ≈ 2 h |
| Stage C: 75 runs (training from Phase 2D; evaluation in a separate process at 928 s + 90 s) | 44.7 h | 44.7 h | 44.7 h |
| Stage D | 47.4 h | 41.4 h | 26.5 h |
| Potsdam test | 27.8 h | 24.3 h | 15.6 h |
| Vaihingen test | 2.7 h | 2.7 h | 2.7 h |
| **ISPRS total** | **≈ 125 h** | **≈ 115 h** | **≈ 92 h** |
| LoveDA (mandatory for generalisation and method claims): Stage C + held-out evaluation | +40–65 h (unmeasured) | +40–65 h | +40–65 h |

**Remaining compute uncertainties:**
- the multi-tile evaluation-process memory, and whether one-tile-per-process is needed (adding about
  0.5 min per tile per run, unmeasured);
- the exact Stage D blocks for Candidate, Fisher, LogME and DSS-R2 (they set the training cost; the
  single-block mean was used);
- LoveDA's pipeline;
- operational interruptions.

## §11 (new): engineering requirements established by the measurements
1. **Potsdam evaluation never runs inside a training process.** The projected peak would be about
   13.2 GB. Evaluation runs in a fresh process loading the step-2,000 checkpoint.
2. **Before Stage C:** one bounded 2-tile sequential evaluation measurement (training tiles, forward
   only), **or** adopt one-tile-per-process evaluation.
3. **Training-process projection:** ≤ 9.1 GB worst case (uniform r8). The existing 11.5 GB footprint
   guard stays.
