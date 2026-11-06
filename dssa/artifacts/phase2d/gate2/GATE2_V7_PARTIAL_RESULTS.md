# Gate 2 recovery (v7) partial results: stopped at run 17 of 57

Stopped by rule on 2026-11-04 at 07:58 IST. See `logs/INCIDENT_006_gate2_v7_charger_disconnected.md`.
Earlier partial reports are preserved unchanged.

## Run status
| Scope | Count |
|---|---|
| Gate 2 authorized | 63 |
| Completed, all integrity checks pass | 22 (seed 1000: all 21 layers; seed 2000: Layer 1) |
| Failed, partial folder preserved | 4 (L02 s1000, L06 s1000, L07 s1000, L02 s2000) |
| Not yet completed | 41 (L02 s2000 plus 40 never started) |

v7 runs 1–16 completed with 0 MB swap growth each; loop 1,508–2,190 s; peak 5.56–8.24 GB.
Run 17 (`p2d_oracle_L02_s2000`) was stopped by the guard (charger disconnected) and killed at
step 1,561.

## Observed utilities, seed 1000 (step 2000, pooled 6-class; K0 s1000 = 0.5264)
| Layer | U6 | U5 | | Layer | U6 | U5 |
|---|---|---|---|---|---|---|
| 1 | −0.0058 | −0.0070 | | 13 | +0.0267 | +0.0310 |
| 2 | −0.0066 | −0.0084 | | 14 | +0.0187 | +0.0214 |
| 3 | −0.0059 | −0.0071 | | 15 | +0.0243 | +0.0287 |
| 4 | +0.0064 | +0.0056 | | 16 | +0.0233 | +0.0273 |
| 5 | +0.0067 | +0.0079 | | 17 | +0.0184 | +0.0216 |
| 6 | +0.0024 | +0.0029 | | 18 | +0.0184 | +0.0221 |
| 7 | +0.0020 | +0.0023 | | 19 | +0.0178 | +0.0211 |
| 8 | +0.0147 | +0.0159 | | 20 | +0.0149 | +0.0178 |
| 9 | +0.0068 | +0.0073 | | 21 | +0.0080 | +0.0094 |
| 10 | +0.0152 | +0.0181 | | 22 | +0.0167 | +0.0196 |
| 11 | +0.0207 | +0.0224 | | | | |

Seed 2000, Layer 1: U6 +0.0075, U5 −0.0039 (K0 s2000).

Recomputed from raw confusion matrices with the frozen analysis functions (read-only).

## Analysis scope
- Seed 1000 is complete for Layers 1–22, but the frozen analysis needs three seeds per layer
  and was not run. No ranking, correlation, top-k, regret, depth-confound or hypothesis
  result is drawn.
- These are single-seed values with no seed interval; no layer-vs-K0 or layer-vs-layer
  claim is made from them.
