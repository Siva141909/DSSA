# Phase 3: compute audit and Measurement C (2026-11-06)

Supersedes the compute figures in protocol v3, decision register v2 and executive recommendation v3.
Those documents are kept unchanged. Every number below can be reproduced from the listed sources with
the formulas given.

## 1. Why the v3 figures did not reproduce from "1,673 + 928 + 90"
- **1,673 s was never the training time for every arm.** It is the **uniform-LoRA** time only
  (Measurement B). v3 used a per-arm training time (the Phase 2D time of the earliest adapted block)
  but did not print it.
- **Reproducing v3:**
  - S1 = Σ over arms of seeds × (T_arm + 928 + 90) = 47.4 h.
  - Stage C = 3 × (T_K0 + Σ_ℓ T_ℓ) + 75 × (928 + 90) = 23.54 h + 21.21 h = 44.7 h.
  - So v3 was arithmetically consistent but undocumented.
- **Two v3 inputs were assumptions, now replaced by measurements:**
  - **overhead:** 90 s assumed, **34 s measured** (4 s training-process start-up + 30 s reload
    verification; Phase 2D v12 guard log, 17 runs);
  - **evaluation:** 116 s per tile in one shared process. That design is no longer safe (§3), so
    evaluation is now **132.5 s per tile in its own process**.

## 2. Sources of every input
| Symbol | Value | Source |
|---|---|---|
| T_K0 | 761 s | Phase 2D `operations[*].training_seconds` (= loop − validation), mean over 3 seeds |
| T_ℓ (single block ℓ) | L0 1,521; L1 1,483; L2 1,464; L3 1,426; L4 1,401; L5 1,375; L6 1,355; L7 1,292; L8 1,254; L9 1,219; L10 1,184; L11 1,157; L12 1,118; L13 1,100; L14 1,061; L15 1,035; L16 996; L17 963; L18 935; L19 900; L20 862; L21 829; L22 797; L23 759 s | Same source |
| T_unif (uniform r1 and r8, all 24 blocks) | 5 × 1.812 + 1,995 × 0.836 = **1,677 s** (1.102 × T_L0) | Measurement B: the first 5 warm-up steps total 9.06 s; steady 0.836 s per step. r1 ≤ r8 by construction (not measured separately) |
| ε (extra cost per additional LoRA block) | (1,677/1,521 − 1)/23 = **0.0044** | Derived from uniform (24 blocks) vs L0 (1 block) |
| T_K3(set) | T_earliest · (1 + 2ε) | Assumption: backpropagation depth (the earliest adapted block) dominates the cost |
| T_unknown (Candidate, Fisher, LogME blocks unknown until Stage B) | mean(T_ℓ) · (1 + 2ε) = 1,155 s | Assumption |
| T_random3 | E over all 3-subsets of T_K3 = 1,365 s | Computed |
| STARTUP | 4 s | v12 guard log: training-process wall minus in-run timing (mean 4, range 2–6) |
| RELOAD | 30 s | v12 guard log: reload-verification process (30 s on every run) |
| CACHE | 120 s | **Allowance:** 20 Potsdam tiles × (0.6 s image read, measured + ≤ 5 s label decode, **unmeasured**) |
| TILE_EVAL | 121.3 s | Measurement C (121.6 and 121.0 s per 6000² tile; Measurement A gave 116 s) |
| TILE_IO | 1.2 s | Measurement C: read 0.57–0.64 s + calibration 0.38–0.74 s |
| PROC (per evaluation process) | 10 s | Measured parts ≈ 3.3 s (imports 1.4, model 1.5, interpreter 0.35), rounded up for checkpoint load and cold-cache variance |
| E_tile = TILE_EVAL + TILE_IO + PROC | **132.5 s** | One tile per process |
| VAL = 8 · E_tile | **1,060 s** | 8 Potsdam validation tiles |
| TEST = 10 · E_tile | **1,325 s** | 10 Potsdam test tiles |
| FIXED = STARTUP + CACHE + VAL + RELOAD | **1,214 s** | Per Stage C or D run, excluding training |
| VTEST | 10 + 8 × 5.01 MP × 3.22 s/MP = 139 s | One process per Phase 2D model. The tiles are small, as in Phase 2D in-process evaluation (5.01 MP = mean non-test Vaihingen tile) |

## 3. Measurement C: two-tile sequential evaluation in one fresh process
- **Setup.**
  - Tiles: `top_potsdam_2_10` and `top_potsdam_2_11` (training tiles; 1st and 2nd in sorted order).
  - Forward only, inside `torch.no_grad()` (in `evaluation.window_logits`); no labels; no test data.
  - Abort threshold 11.0 GB, never reached.
- **Wall time.** 248.5 s in total; `/usr/bin/time` peak footprint 7,903,532,120 bytes (7,537 MiB).

| Event (time from start) | Footprint | MPS driver |
|---|---|---|
| Imports done (1.4 s) | 266 MB | 0 |
| Model loaded (2.9 s; load 1.5 s; transient peak 4,505 MB) | 3,170 MB | 2,089 MB |
| Tile 1 evaluated (read 0.57 s, calibration 0.74 s, logits 121.6 s); **tile peak 7,537 MB** | 6,431 MB residual | 2,123 MB |
| After `del` + `gc.collect()` + `torch.mps.empty_cache()` | **6,407 MB** | 2,099 MB |
| Tile 2 evaluated (read 0.64 s, calibration 0.38 s, logits 121.0 s); **tile peak 7,511 MB** | 7,465 MB residual | 2,123 MB |
| After `del` + `gc` + `empty_cache` | **7,441 MB** | 2,099 MB |

**Interpretation.**
- The per-tile peak did not rise (7,537 → 7,511 MB), but the **residual footprint grew by 1,034 MB**
  between tiles, and `gc` and `empty_cache` did not release it.
- Two points cannot distinguish a plateau from linear growth. Linear growth would exceed 11.5 GB
  before tile 6.
- **Safe headroom for 8–10 sequential tiles is not established.**
- **Decision: one tile per evaluation process** (each peaks at ≤ 7.54 GB, with ≈ 4.0 GB margin).
- Measured overhead per extra process: ≈ 3.3 s (budgeted at 10 s).
- **Added cost vs a shared process:** 7 extra processes × 10 s = 70 s per validation run and
  9 × 10 = 90 s per test model.

## 4. Training-process memory (Potsdam)
- **Uniform r8, worst LoRA case (measured on Vaihingen):** 6,750 − 391 (Vaihingen cache) + 2,747
  (Potsdam cache) = **9,106 MB** projected.
- **Single block, most conservative bound:** the Phase 2D maximum peak of 8,303 MB already includes
  in-process Vaihingen evaluation and model-build transients. 8,303 − 391 + 2,747 = **10,659 MB**,
  which is under the 11,776 MB limit by 1.1 GB. The true training-only value is lower: Measurement B,
  the heaviest LoRA configuration, peaked at 6,750 MB.
- **Training processes never evaluate Potsdam tiles** (D22).

## 5. Budgets (formulas; seconds converted to hours)
- **Stage C:** 3 · (T_K0 + Σ_{ℓ=0}^{23} T_ℓ) + 75 · FIXED = 84,746 + 91,050 s = **23.54 + 25.29 = 48.8 h**.
- **Stage D:** Σ over arms of seeds · (T_arm + FIXED).

| Arm | T_arm (s) | Run (s) | S1 seeds | S2 seeds | S3 seeds |
|---|---|---|---|---|---|
| 1 K0 (7 new; 3 reused from C) | 761 | 1,975 | 7 | 7 | 7 |
| 2 Prior-3 {13, 14, 15} | 1,110 | 2,324 | 10 | 10 | 10 |
| 3 Candidate-3 | 1,155 | 2,369 | 10 | — | — |
| 4 Uniform r1 | 1,677 | 2,891 | 10 | 10 | 10 |
| 5 Middle-3 {10, 11, 12} | 1,194 | 2,408 | 5 | 5 | 5 |
| 6 Late-3 {21, 22, 23} | 836 | 2,050 | 5 | 5 | — |
| 7 DSS-R2-3 (assumed {19, 20, 22}) | 908 | 2,122 | 5 | 5 | — |
| 8 Fisher-3 | 1,155 | 2,369 | 5 | 5 | — |
| 9 LogME-3 | 1,155 | 2,369 | 5 | 5 | — |
| 10 Random-3 (10 draws × 1 seed) | 1,365 | 2,579 | 10 | 10 | 10 |
| 11 Uniform r8 | 1,677 | 2,891 | 5 | 5 | — |
| **New runs** | | | **77** | **67** | **42** |
| **Stage D hours** | | | **51.8** | **45.2** | **28.8** |
| **Test models** (new + 3 reused K0) | | | **80** | **70** | **45** |
| **Potsdam test** = models × 1,325 s | | | **29.4 h** | **25.8 h** | **16.6 h** |

| Total | S1 | S2 | S3 |
|---|---|---|---|
| Stages A + B (allowance) | 2.0 | 2.0 | 2.0 |
| Stage C | 48.8 | 48.8 | 48.8 |
| Stage D | 51.8 | 45.2 | 28.8 |
| Potsdam test | 29.4 | 25.8 | 16.6 |
| Vaihingen test (75 × 139 s) | 2.9 | 2.9 | 2.9 |
| **ISPRS total** | **135.0 h** | **124.7 h** | **99.1 h** |

**LoveDA (separate, mandatory for generalisation or method claims).**
- **Formula:** Stage C = 3 · (T_K0 + Σ T_ℓ) + 75 · (STARTUP + 60 s cache + N_val · 1.05 MP · 3.22 s/MP
  + PROC + RELOAD).
- This assumes Vaihingen-rate training, 1024² images and one evaluation process (small images; the
  memory is not measured).
- **N_val = 200:** 39.8 h. **N_val = 400:** 53.9 h. N_val is a design choice that is not yet fixed.
- Any LoveDA held-out evaluation is additional.
- RGB band mapping and pipeline costs are unmeasured.

## 6. Remaining uncertainty (explicit)
| Item | Effect | How it is bounded |
|---|---|---|
| Label decode time for the 20 Potsdam tiles (not measurable without labels) | ≤ 120 s per run allowed | If exceeded, it is visible on the first Stage C run (canary) |
| Single-block training memory on Potsdam | ≤ 10.66 GB conservative bound | 11.0 GB abort sampler + the existing 11.5 GB guard; the first Stage C run is an early block (worst case) |
| T_K3 ≈ earliest-block time × (1 + 2ε) | ± a few % on Stage D | Stage D is approved after Stage C, and can be re-estimated from measured Stage C times |
| Candidate, Fisher, LogME and DSS block positions | ± ≈ 10% on those arms | Known after Stage B |
| Evaluation-process overhead (10 s budgeted vs 3.3 s measured) | ≈ +1.5 h over Stage C | Conservative |
| Interruptions (INCIDENT_001–010) | Wall time, not compute | Existing guards and recovery manifests |
