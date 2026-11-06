# DSSA Phase 2D Addendum V2: 8-bit training cache

Adds to PHASE2D_ADDENDUM.md and does not replace it. Authorization: memory
optimisation and one further Layer 0 attempt.

- Training tiles are cached as uint8 imagery and uint8 class indices. Calibration
  runs per crop with the same frozen coefficients and the same arithmetic.
- Validation still uses the Phase 2C dataset class unchanged.
- Exact equivalence is a gate: file order, calibrated crops, labels, augmented
  arrays, model inputs, RNG states and fixed-batch model outputs must be
  bit-identical. Any difference stops the work.
- Run ID p2d_oracle_L00_s1000_a3. The two failed attempts are preserved.
- K0_s1000 stays complete if equivalence passes.
- Telemetry: exact optimizer step, stage, footprint, MPS driver and current
  allocation, pressure, swap, timestamp, every 0.25 s, plus incident.json on failure.
- Limits unchanged: 11.5 GB footprint, 512 MB swap growth, critical pressure,
  1.5x runtime, integrity failures. If the attempt fails there is no retry.
- After this one run the work returns to the research lead.
