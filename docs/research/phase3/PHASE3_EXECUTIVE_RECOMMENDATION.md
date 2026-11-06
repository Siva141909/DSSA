# Phase 3: executive recommendation

## The single recommended direction
**A pre-registered, oracle-validated study of whether *any* layer-selection signal predicts LoRA
utility in a geospatial foundation model better than block depth.** It has three parts:
- a fresh independent target (Vaihingen → **Potsdam**, using Potsdam labels that have never been
  opened);
- the original DSS, the strongest exploratory label-free candidate (RAW distance) and one physically
  motivated candidate (GSD-perturbation sensitivity), each tested against a **pre-registered
  non-linear depth prior**;
- cheap **label-using** references (LogME as in SPECTRA; Fisher as in CrossEarth-Gate).

A method claim is allowed only if a label-free candidate passes the pre-registered criteria.

## Why this beats the alternatives
- **It matches the evidence.**
  - Phase 2D shows that DSS ≈ depth (ρ 0.94) and partial ρ 0.076.
  - The *pre-registered* Middle rule was the best of all rules (D1 in the state audit).
  - A new discrepancy score has a low prior of success. A rigorous test of what explains layer utility
    builds directly on the 75 runs already done.
- **It survives the novelty audit.** Layer-wise discrepancy for placement (DDC 2014), label-free layer
  selection (Act-LoRA, LS-LoRA and the LREC 2026 work) and RS module selection (CrossEarth-Gate, which
  even uses Potsdam ↔ Vaihingen) already exist. What is not established in the literature read is a
  **depth-controlled, oracle-validated comparison of label-free vs label-using selectors** for a GFM
  under RS domain shift.
- **It has a guaranteed interpretable outcome.** If a selector passes, that's a method. If none does,
  that's a replicated, depth-controlled negative result plus a label-free vs label-using comparison.

## Minimum experiments for a credible paper
1. **Stage A:** freeze the Potsdam-target split *before* opening labels; evaluation memory test.
2. **Stage B:** compute and hash all selector scores (label-free + LogME + Fisher).
3. **Stage C:** the 24-block + K0 oracle on Potsdam, 3 seeds (75 runs, ≈ 45–55 h).
4. **Stage D:** K = 3 joint arms vs **uniform LoRA rank 1 at the exact same 98,304-parameter budget**
   and decoder-only, with 10 seeds for the confirmatory contrasts and measured time, memory and
   latency (≈ 60–70 h).
5. **One pre-registered opening** each of the Potsdam test and the Vaihingen locked test.

**The fallback paper** is A–C only, plus the Phase 2D data.
**Strongly recommended** is the LoveDA oracle, for a second, genuinely different shift.

## Do first
1. **Approve this direction and the Potsdam-as-target use of the Potsdam labels.**
2. Stage A only:
   - the split rule and manifest;
   - the radiometric-transform decision;
   - the evaluation memory test on one 6000² tile, using no labels beyond the frozen split's training
     tiles.
3. Read the [S]/[U] papers in full (the must-read list in the literature audit) before any writing.

## Do not do yet
- No new training, scoring or selector code until the Stage A manifest is approved.
- Don't open any Potsdam label before the split manifest is hashed.
- Don't open the Vaihingen locked test.
- Don't add composite or new metrics beyond the 3 label-free candidates.
- Don't claim novelty for "layer-wise discrepancy", "label-free layer selection", "middle layers are
  best" or "efficiency".
- Don't describe the setting as unsupervised domain adaptation.

## Decisions needing your approval
1. **Path:** Path 2 primary, with the method claim nested as a hypothesis.
2. **Potsdam labels:** use them (never opened so far) for the new target, with the split frozen first.
3. **LoveDA:** download and accept the CC BY-NC-SA 4.0 licence and the Google Earth terms.
4. **Compute budget:** ≈ 105–125 h (A–D) or ≈ 150–185 h (with LoveDA), on this Mac, under the existing
   guards.
5. **Opening rules:** when the Vaihingen locked test and the Potsdam test may be opened, and for which
   configurations.
6. **Code location:** a new versioned code directory for Phase 3. `dssa/phase2d` stays hash-locked.
7. **Git:** whether to commit `docs/research/phase3/` (not done).
