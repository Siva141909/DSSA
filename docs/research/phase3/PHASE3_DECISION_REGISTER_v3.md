# Phase 3: decision register v3

v1 and v2 are kept unchanged. v3 **amends D8 and D25** and adds **D26–D28**. All other v1 and v2
entries apply unchanged.

| ID | Original issue | Evidence | Revised decision | Remaining uncertainty | Approval? | Status |
|---|---|---|---|---|---|---|
| D8 (amended again) | v3 budgets not reproducible from the stated per-run cost | Compute audit §1–§5 | Per-run = T_arm + 1,214 s; **Stage C 48.8 h**; **S1** 77 runs, 51.8 h, 80 test models, 29.4 h; **S2** 67 runs, 45.2 h, 70, 25.8 h; **S3** 42 runs, 28.8 h, 45, 16.6 h; ISPRS totals **135.0 / 124.7 / 99.1 h**; LoveDA Stage C 39.8–53.9 h, separately | Label-decode allowance; K = 3 cost model; Stage B block positions | **Yes** (staged budget) | Proposed |
| D25 (resolved) | Multi-tile evaluation memory | Measurement C: per-tile peaks 7,537 / 7,511 MB, but the residual grew by 1,034 MB per tile and `gc` / `empty_cache` did not release it | **One evaluation process per tile** (≤ 7.54 GB each). Overhead budgeted at 10 s per process (3.3 s measured) | Growth beyond 2 tiles was not tested (not needed under this design) | **Yes** (design) | Proposed |
| D26 | Overhead assumed at 90 s | v12 guard log: start-up 4 s (2–6), reload 30 s | Use 4 s + 30 s; add a 120 s Potsdam cache allowance | Label decode unmeasured | No (record) | Adopted |
| D27 | Training memory bound for single-block Potsdam runs | Phase 2D maximum peak 8,303 MB (including in-process evaluation) − 391 + 2,747 | Conservative bound **10.66 GB**; the first Stage C run is an early block as the canary; stop at 10.5 GB per process; 11.0 GB abort sampler | True training-only value unknown, but lower (uniform r8 measured 6.75 GB on Vaihingen) | **Yes** (limit) | Proposed |
| D28 | Stage D budget approval timing | Arm costs depend on Stage B and C outcomes | Approve Stage D only after Stage C, recomputed from measured Stage C times with the same formulas | — | **Yes** | Proposed |
