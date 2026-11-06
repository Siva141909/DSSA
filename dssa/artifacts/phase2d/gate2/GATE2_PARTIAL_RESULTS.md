# Gate 2 partial results: sequence stopped at run 2 of 63

Stopped by rule on 2026-11-03 at 13:27 IST. See `logs/INCIDENT_003_gate2_runtime_stop_system_sleep.md`.

## Run status
| # | Run | Status |
|---|---|---|
| 1 | p2d_oracle_L01_s1000 | Completed; all integrity checks passed |
| 2 | p2d_oracle_L02_s1000 | Failed: runtime limit (system sleep), stage `train`, step 1,804 of 2,000 |
| 3–63 | remaining 61 runs | Not started (stop rule) |

## Observation from the one new completed run (seed 1000, step 2000, 6-class pooled)
- Layer 1: mIoU 0.5206, against K0 at seed 1000 of 0.5264, so U = −0.0058 (5-class U = −0.0070).
- Best checkpoint: 0.5226 at step 1600. Validation cross-entropy: 0.560.
- Per-class difference against K0 (impervious, building, low vegetation, tree, car, clutter):
  −0.032, −0.053, +0.019, +0.012, +0.020, 0.000.
- This is the same pattern as Layer 0 at seed 1000 (U = −0.0130): losses on impervious
  surfaces and buildings, small gains elsewhere.

## Analysis scope
- The frozen `gate2_analysis.py` needs all 75 runs (24 layers × 3 seeds + K0). It was not run.
- No ranking, correlation, top-k, regret or depth-confound result exists.
- One seed and one new layer give no evidence about the DSS hypothesis.
- No full-sweep conclusion is made.
