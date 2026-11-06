# Gate 2 recovery (v5) partial results: stopped at run 5 of 62

Stopped by rule on 2026-11-03 at 17:17 IST. See `logs/INCIDENT_004_gate2_v5_swap_growth_stop.md`.
The earlier `GATE2_PARTIAL_RESULTS.md` (v4 stop) is preserved unchanged.

## Run status (v5)
| # | Run | Status | Loop time | Peak footprint | Swap growth |
|---|---|---|---|---|---|
| 1 | p2d_oracle_L02_s1000_a2 | Completed; all checks pass | 2,229 s | 7.71 GB | 0 MB |
| 2 | p2d_oracle_L03_s1000 | Completed; all checks pass | 2,187 s | 7.90 GB | 0 MB |
| 3 | p2d_oracle_L04_s1000 | Completed; all checks pass | 2,147 s | 8.10 GB | 0 MB |
| 4 | p2d_oracle_L05_s1000 | Completed; all checks pass | 2,109 s | 8.13 GB | 0 MB |
| 5 | p2d_oracle_L06_s1000 | **Failed**: swap growth 513 MB > 512 MB, stage `validation`, step 400 | — | 7.10 GB | 513 MB |
| 6–62 | remaining 57 runs | Not started (stop rule) | | | |

Gate 2 totals, with Layer 1 from v4: 5 of 63 authorized runs completed (all seed 1000).

## Observed utilities (seed 1000 only, step 2000, pooled 6-class; K0 s1000 = 0.5264)
| Layer | mIoU | U (6-class) | U (5-class) | Best (step) |
|---|---|---|---|---|
| 1 | 0.5206 | −0.0058 | −0.0070 | 0.5226 (1600) |
| 2 | 0.5198 | −0.0066 | −0.0084 | 0.5227 (1600) |
| 3 | 0.5205 | −0.0059 | −0.0071 | 0.5250 (1600) |
| 4 | 0.5328 | +0.0064 | +0.0056 | 0.5391 (1600) |
| 5 | 0.5331 | +0.0067 | +0.0079 | 0.5357 (1600) |

Per-class difference against K0 (impervious, building, low vegetation, tree, car, clutter):
- L01: −.032, −.053, +.019, +.012, +.020, .000
- L02: −.027, −.063, +.023, +.016, +.009, +.002
- L03: −.033, −.065, +.023, +.021, +.018, .000
- L04: −.004, −.021, +.024, +.022, +.007, +.011
- L05: −.002, −.022, +.028, +.027, +.008, .000

Recomputed from raw confusion matrices with the frozen analysis functions (read-only).

## Analysis scope
- One seed only. Every |U| is below δ = 0.010, and the audited single-contrast t(2)
  half-width is about 0.014–0.025, so no layer differs from K0 at this evidence level.
- The frozen `gate2_analysis_v5.py` needs all 75 runs and was not run. No ranking,
  correlation, top-k, regret or depth-confound result exists.
- No conclusion about the DSS hypothesis is drawn.
- No final backup was made (that step belongs to the completed sequence).
