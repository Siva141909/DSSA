# Phase 3: experimental protocol, v4

Revision history:
- v1–v3 are kept unchanged.
- **v4 (2026-11-06)** changes only:
  - the evaluation-process design;
  - the per-run cost model;
  - the Stage C budget;
  - the S1–S3 budgets;
  - the test compute.

  Source: `PHASE3_COMPUTE_AUDIT_2026-11-06.md`. Every other section of v3, and of v2 where v3 defers to
  it, applies unchanged.

## §6 and §10 (replace v3): cost model and budgets
**Per-run cost:**
- Stage C or D run = T_arm + FIXED, where FIXED = 4 s (start-up) + 120 s (cache allowance) + 1,060 s
  (8 validation tiles, one process per tile) + 30 s (reload verification) = **1,214 s**.
- **T_arm** = the Phase 2D training time of the earliest adapted block × (1 + 0.0044 per additional
  block). Uniform r1 and r8 use 1,677 s (measured). The full list is in the compute audit §2.

| Budget | S1: candidate passes | S2: no candidate, prior transfers | S3: no candidate, prior fails |
|---|---|---|---|
| Stage C (75 runs) | 48.8 h | 48.8 h | 48.8 h |
| Stage D new runs | 77 | 67 | 42 |
| Stage D hours | 51.8 h | 45.2 h | 28.8 h |
| Reused K0 runs | 3 | 3 | 3 |
| Potsdam test models | 80 | 70 | 45 |
| Potsdam test hours (× 1,325 s) | 29.4 h | 25.8 h | 16.6 h |
| Vaihingen test (75 models × 139 s) | 2.9 h | 2.9 h | 2.9 h |
| Stages A + B | 2.0 h | 2.0 h | 2.0 h |
| **ISPRS total** | **135.0 h** | **124.7 h** | **99.1 h** |
| LoveDA Stage C (separate) | 39.8 h (N_val = 200) to 53.9 h (N_val = 400) | same | same |

The arm-by-arm table is in the compute audit §5. The arms, seeds and primary analyses are unchanged
from v3 (S1: C1 and C2; S2: C3; S3: descriptive).

## §11 (replaces v3 §11): evaluation-process design and memory limits
1. **One evaluation process per tile,** for both Potsdam validation (8 processes per run) and the
   Potsdam test (10 processes per model).
   - Each process loads the step-2,000 checkpoint, evaluates one tile, and writes that tile's confusion
     matrix and pooled logits statistics.
   - Pooling over tiles happens afterwards, from the per-tile matrices, exactly as `gate2_analysis.py`
     pools tile matrices.
   - Measured per-process peak: ≤ 7.54 GB.
2. **Training processes never evaluate Potsdam tiles.**
3. **Memory guards:**
   - the existing 11.5 GB footprint limit stays;
   - an 11.0 GB early-abort sampler is added in every Phase 3 process;
   - the first Stage C run is an **early block** (the highest training memory; conservative bound
     10.66 GB) and acts as the canary.
   - Stop the sequence if any process exceeds 10.5 GB.
4. **Vaihingen locked-test evaluation** of the Phase 2D checkpoints uses one process per model: small
   tiles, the same scale as the Phase 2D in-process evaluation.
