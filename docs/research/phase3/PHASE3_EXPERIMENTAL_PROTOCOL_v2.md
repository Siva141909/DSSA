# Phase 3: experimental protocol, v2 (supersedes v1 for planning; v1 is kept unchanged)

Revision history:
- v1 (2026-11-06): `PHASE3_EXPERIMENTAL_PROTOCOL.md`.
- v2 (2026-11-06): red-team corrections, see `PHASE3_PROTOCOL_REDTEAM.md` (issues 1–5, evidence
  E1–E6).

**Status: a draft for approval.** Nothing here is authorised to run.

## 1. Settings and what each can establish
| Role | Setting | What is new | What is not new | What it can support |
|---|---|---|---|---|
| Development | Potsdam → Vaihingen (Phase 2D) | — | Everything (already analysed) | Candidate definitions and the frozen depth prior. **Never confirmation** |
| Primary | Vaihingen → **Potsdam** | Potsdam labels (never opened), the target role, the utility oracle, new validation and test tiles, the 9 → 5 cm direction | Potsdam images (used in Gate 0 DSS and the radiometric fit), the domain pair, investigator knowledge | "A new-target, new-label replication within the ISPRS pair". The confirmatory Stage D contrasts on the Potsdam test |
| **Mandatory for generalisation and method claims** | **LoveDA** Urban ↔ Rural (0.3 m, RGB, 7 classes; CC BY-NC-SA 4.0) | Images, labels, geography, shift type, taxonomy | Backbone and recipe | The second independent gate for any selector. Any claim beyond the ISPRS pair |
| Optional | A second backbone | Architecture | — | Backbone generality |

## 2. Leakage controls (all checked by hashes recorded before use)
1. **Potsdam split, frozen before any label is read.** Rule: sort the 38 tile names
   lexicographically, then assign by position (no shuffle, as for Vaihingen):
   - the first 20 are **train**, and the first 5 of those are **probe** (a subset of train, as in
     Phase 2D);
   - the next 8 are **validation**;
   - the last 10 are **test**.

   Write the split manifest and record its hash. A label-loading guard refuses any tile not in the
   split's allowed set for the current stage.
2. **Labels per stage:**
   - selectors use **training labels only** (Fisher, LogME);
   - Stage C and D training uses training labels;
   - validation labels are used only at the step-2,000 evaluation;
   - test labels are used only at the single test opening (§9).
3. **Radiometric transform for Vaihingen → Potsdam: refit on Vaihingen training images only**
   (source-fit-only principle). This needs approval, as D4.
4. **The source pool for label-free signals is the Vaihingen training tiles (20).**
   - Centroid: the first 16 sorted tiles, mirroring Phase 2D.
   - Null: matched 16-vs-5 draws from those 20.
   - Target: the 5 Potsdam probe tiles.
   - Vaihingen validation and test tiles are never used.
5. **Evaluation at step 2,000 only,** using the final checkpoint. No best-checkpoint selection.

## 3. Stage A: audit (no training, no labels)
- Integrity of the Potsdam image and label archives: checksums only, no label decoding.
- Freeze the split manifest.
- Refit and freeze the radiometric transform.
- **Memory and throughput probe:** a forward-only sliding-window pass over one 6000² **training** image
  with no labels. Measure evaluation time per MP and the peak footprint.
- Measure the footprint of the 20-tile uint8 cache (≈ 2.2 GB) against the 11.5 GB limit (risk R22).
- **Stop if** the projected training plus evaluation peak exceeds 11.5 GB. Then a tiling or caching
  change is required first, under a new approval.

## 4. Stage B: selector screening (scores frozen and hashed before any Stage C arm other than K0)
Run order:
1. Run **K0 × 3 seeds** on Potsdam. These are also the Stage C baselines.
2. Compute the scores below.
3. Hash them.
4. Only then start the 72 single-block arms of Stage C.

**Label-free signals** (Vaihingen source and Potsdam probe images; frozen backbone; no decoder):
- **DSS-R2.** The original definition with the pools from §2.4.
- **GSD-perturbation sensitivity (new).** For each source image x, resample it to the target ground
  sampling distance and back. Here g = bilinear down-sampling by 9/5 then up-sampling to the original
  size; one operator only, fixed in advance. The score is s_ℓ = mean over x of
  ‖f_ℓ(g(x)) − f_ℓ(x)‖ / ‖f_ℓ(x)‖, where f_ℓ is the pooled block output, using the same 9-crop pooling
  as Gate 0. *(For Potsdam as the target the direction reverses: 5/9.)*
- **Literature baselines** (eligible for Stage D, no novelty claim):
  - input-output similarity 1 − mean cos(h_ℓ^in, h_ℓ^out) over probe-image tokens;
  - activation norm, the mean ‖h_ℓ^out‖ over probe-image tokens.
- **Reported descriptively only:** RAW_R2 and MMD. These are dropped as candidates (evidence E4).

**Label-using references** (target **training** labels only):
- **Fisher.**
  - Model: the frozen backbone + the **final (step-2,000) decoder of Potsdam K0 seed s**, with LoRA in
    all 24 blocks (A initialised with seed s's LoRA seed, B = 0).
  - Loss: the training cross-entropy as in the protocol.
  - Data: 64 batches × 8 crops from seed s's deterministic training stream (all 20 training tiles,
    probe included).
  - Score: F_ℓ = mean over batches of Σ (∂L/∂B_q,ℓ)² + (∂L/∂B_v,ℓ)², averaged over the 3 seeds.
- **LogME.**
  - Features: frozen backbone **patch tokens** of block ℓ (no LoRA, no decoder) on 2,000 random 224²
    crops from the training tiles (fixed seed).
  - Labels: the majority class of each 16×16 patch, keeping patches with purity ≥ 0.8.
  - Sampling: up to 20,000 patches, class-stratified with a cap of 4,000 per class.
  - Score: LogME for multi-class classification as in You et al. (2021), using the one-vs-rest mean.
  - **On the development setting (Vaihingen),** the same definitions are computed with the Phase 2D K0
    **final** checkpoints. This is used only to sanity-check the implementation, never to tune
    thresholds.

## 5. Stage C: single-block oracle (Potsdam)
- **Arms and seeds:** K0 + 24 single blocks × **3 seeds** = **75 runs**, using the Phase 2D recipe:
  - LoRA r8 on Q/V; L23 decoder
  - 2,000 steps, batch 8, crop 224
  - seeded decoder initialisation and LoRA A
  - deterministic data stream
  - checkpoint and reload integrity checks.
- **Metric:** the step-2,000 pooled 6-class mIoU on the 8 validation tiles. Utility = arm − same-seed
  K0.
- **Screening (a non-inferential gate; known ~7% false pass per candidate under the null, E5):**
  - the frozen prior is p(ℓ) = −1.8386e-4·ℓ² + 4.9992e-3·ℓ − 4.1343e-4 (from Phase 2D, never refitted);
  - r_res = Spearman(s, z(Ū) − z(p));
  - **a candidate passes if ALL of the following hold:**
    - r_res ≥ 0.30;
    - every leave-one-seed-out r_res ≥ 0.15;
    - the 2.5th percentile of the tile-bootstrap r_res (8 validation tiles, 10,000 resamples) is ≥ 0;
    - top-3 regret ≤ the prior's top-3 {14, 13, 15} regret.
  - At most **one** label-free candidate enters Stage D: the best r_res among those passing.
- **Descriptive, required:** Spearman and Kendall of every signal and of the prior with Ū; top-k regret
  (k = 1, 3, 5) against 20,000 random selections; the seed and tile uncertainty components reported
  separately; and the transfer test of the depth prior itself, Spearman(p, Ū).

## 6. Stage D: joint adaptation (Potsdam), explicit accounting
K = 3 at rank 8 = 98,304 LoRA parameters, which equals uniform rank 1 on all 24 blocks (exact budget
match). Seeds 1–3 are the Stage C seeds; new seeds are 4–10.
- **Per-run cost:**
  - **training** is the Phase 2D mean training time of the earliest adapted block (E1);
  - **validation** is 922 s (8 Potsdam tiles × 36 MP × 3.2 s/MP);
  - **overhead** is 90 s;
  - **uniform LoRA** is assumed to cost 1.15 × the L0 training time (an unmeasured assumption).

| # | Arm | Role | Seeds | New runs | Reuse | Training s/run (basis) | Hours |
|---|---|---|---|---|---|---|---|
| 1 | K0 decoder-only | Reference | 10 | **7** | Seeds 1–3 from Stage C | 761 (K0) | 3.4 |
| 2 | **Prior-3** {14, 13, 15} | **Primary comparator** | 10 | 10 | — | 1,100 (L13) | 5.9 |
| 3 | **Candidate-3** | **Primary**, only if a candidate passes | 10 | 10 | — | ≈ 1,145 (unknown blocks; single-block mean) | 6.0 |
| 4 | **Uniform r1, all 24** | **Matched-budget comparator** | 10 | 10 | — | 1,750 (1.15 × L0) | 7.7 |
| 5 | Middle-3 {11, 12, 10} | Secondary (pre-registered rule) | 5 | 5 | — | 1,184 (L10) | 3.1 |
| 6 | Late-3 {23, 22, 21} | Secondary | 5 | 5 | — | 829 (L21) | 2.6 |
| 7 | DSS-R2-3 (Potsdam scores) | Secondary | 5 | 5 | — | Blocks unknown until Stage B; Phase 2D's top-3 {22, 19, 20} gives ≈ 900 | 2.7 |
| 8 | Fisher-3 | Label-using reference | 5 | 5 | — | ≈ 1,145 | 3.0 |
| 9 | LogME-3 | Label-using reference | 5 | 5 | — | ≈ 1,145 | 3.0 |
| 10 | Random-3 | Random baseline | 10 draws × 1 seed (draw j uses seed j) | 10 | — | 1,353 (expected earliest block) | 6.6 |
| 11 | Uniform r8, all 24 (786,432) | Cost/quality reference | 5 | 5 | — | 1,750 | 3.8 |
| 12 | Full fine-tuning | Optional | — | 0 | — | Not counted; run only if memory permits | — |
| | **Total** | | | **77** (67 if no candidate passes) | 3 reused | | **≈ 47.7 h** (≈ 41.7 h without arm 3) |

- **Not double-counted:** the 3 reused K0 runs are counted in Stage C only.
- **Previously omitted:** LogME-3, the reuse of K0, and the test-evaluation cost (§9).
- **Cost metrics per run** (measured, not inferred): training wall-clock, peak footprint and MPS
  driver memory, inference latency per 224² crop and per tile, and trainable and total parameters.

## 7. Statistics
- **Units.** The seed is the replication unit for training noise. Validation and test tiles are
  evaluation units, resampled **conditional on the trained models** and never pooled with seed
  variance. The 24 blocks are a fixed, depth-structured set, so there is no block-level inference.
- **Primary confirmatory contrasts, on the Potsdam test (§9), paired by seed, n = 10:**
  - **C1:** Candidate-3 − Prior-3 ≥ **δ = 0.010** (superiority).
  - **C2:** Candidate-3 vs Uniform-r1, non-inferiority with margin δ.
  - Holm correction across C1 and C2.
  - Effect sizes as mean differences in pooled mIoU, with 95% t-intervals (df 9). A separate tile
    bootstrap is reported as a robustness check.
- **Precision.** For paired arm differences σ_c ≈ 0.0099 (Phase 2D), so 10 seeds give a half-width
  t(9)·σ_c/√10 ≈ 0.0071 and power ≈ 0.8 at δ. The per-block utility SD is larger (0.014), but the
  contrasts are paired arm-vs-arm.
- **If no candidate passes,** C1 and C2 are not tested. Report Prior-3, Middle-3, Uniform-r1,
  Fisher-3, LogME-3, Random-3 and K0 descriptively, with the same intervals (Path 2).
- **Method claim (Path 1):** C1 holds on the Potsdam test **and** the candidate passes the Stage C gate
  on LoveDA.

## 8. Decision and stop rules
- **During Stage C:** stop and review if K0 mIoU after the first seed is below 0.30 (a pipeline-failure
  floor), or if any run exceeds the memory limits.
- **After Stage C:** if no candidate passes **and** Spearman(p, Ū) < 0.3 (the depth prior does not
  transfer), Stage D may be reduced to arms 1, 2, 4, 5 and 10 (≈ 27 h). Report hypotheses F and G.
- **No new arms, seeds or thresholds after any result** except through a new versioned protocol with
  the reason recorded. Results from the old version are reported regardless.

## 9. Test openings
| Test | Role | Opened when | Evaluated models (frozen beforehand) | Script | Allowed uses | Forbidden uses |
|---|---|---|---|---|---|---|
| **Potsdam test (10 tiles)** | **Confirmatory** (the only one) | Once, after all 77 Stage D runs plus the 3 reused K0 runs are complete and integrity-checked | All 80 Stage D models (arms 1–11), final step-2,000 checkpoints | Hashed before opening; the analysis code for C1 and C2 is frozen | C1 and C2 (§7); descriptive reporting of all arms | Choosing K, arms, candidates or thresholds; rerunning with changes |
| **Vaihingen locked test (8 tiles)** | Secondary: held-out check of the Phase 2D single-block findings | Once, after the Stage B scores and all §5–§8 thresholds are hashed (it cannot influence Phase 3 design) | The 75 Phase 2D final checkpoints (K0 + 24 blocks × 3 seeds) | Hashed; the frozen Phase 2D analysis definitions apply | Reporting the utility curve, R2 vs utility and the prior on held-out tiles | Any Phase 3 selection or threshold |

**Contradictions and accidents:**
- If the Potsdam and Vaihingen test conclusions disagree, both are reported. The confirmatory claim
  follows the Potsdam test only, and the disagreement limits any generality statement.
- If a test is accessed early, that setting becomes development-only. A confirmatory claim then
  requires LoveDA's held-out split, frozen under the same rules.
- Test results never change a method, threshold or protocol version.

## 10. Compute summary (from the actual Phase 2D rates, E1)
| Item | Runs or models | Hours |
|---|---|---|
| Stage A probes | 0 training | ≈ 1 |
| Stage B: selector scoring (excluding K0, which is in C) | — | < 1 |
| Stage C: 75 runs (training 23.5 h + validation 75 × 922 s + overhead) | 75 | **44.6** |
| Stage D | 77 | **47.7** |
| Potsdam test opening (80 models × 10 tiles × 36 MP × 3.2 s/MP) | 80 | **25.6** |
| Vaihingen test opening (75 models × 8 tiles × ≈ 5 MP) | 75 | **2.7** |
| **ISPRS total** | | **≈ 122 h** (≈ 116 h without a candidate) |
| LoveDA Stage C + its held-out evaluation | 75 + | 40–65 (unmeasured: RGB mapping, image count) |
| **Total with LoveDA** | | **≈ 165–190 h** |

**Uncertainties:** Potsdam evaluation throughput on 6000² tiles (assumed to scale linearly at
3.2 s/MP); the uniform-LoRA overhead factor; the memory headroom with the Potsdam cache; LoveDA's
pipeline cost; and operational interruptions (INCIDENT_001–010 history).
