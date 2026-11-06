# Phase 3: executive recommendation, v2

Revision history:
- v1 (2026-11-06): `PHASE3_EXECUTIVE_RECOMMENDATION.md`, kept unchanged.
- v2 (2026-11-06): updated after the red-team review (`PHASE3_PROTOCOL_REDTEAM.md`).

## What changed and why (evidence-driven only)
1. **RAW_R2 is no longer the lead label-free candidate.** Against the frozen non-linear depth prior,
   its residual association is −0.27 (E4). The v1 claim relied on linear depth control.
2. **Vaihingen → Potsdam is a new-target, new-label replication within the ISPRS pair,** not an
   independent image-domain replication (D1). **LoveDA is now mandatory** for any generalisation or
   method claim (D2).
3. **The screening gate is non-inferential** (≈ 7% false pass per candidate, E5). Confirmation moves
   to Stage D on the Potsdam test, with 10 seeds (D11, D16).
4. **The primary depth comparator is the frozen quadratic prior's top-3 {14, 13, 15}** (D15).
5. **Revised compute, from actual Phase 2D rates:** about 122 h for the ISPRS stages including both
   test openings, and about 165–190 h with LoveDA (protocol v2 §10).

## Unchanged recommendation
Path 2 is primary: a pre-registered, oracle-validated test of whether any selection signal beats a
depth prior, with label-free vs label-using comparisons. A method claim is nested inside it and now
requires passing **both** the Potsdam and LoveDA gates **and** the Potsdam-test contrast C1.

## Minimum credible set
1. Stage A.
2. Stage B (K0 × 3 first, then hashed scores).
3. Stage C (75 runs).
4. Stage D (77 runs; 67 if no candidate passes).
5. The Potsdam test opening.
6. LoveDA Stage C (mandatory for anything beyond the ISPRS pair).

## Ready for approval?
**Yes, as a protocol, subject to the approval decisions in `PHASE3_DECISION_REGISTER.md`:**
D2, D3, D4, D5, D6, D8, D9, D10, D11, D13, D14, D15, D16, D17 and D20.

Two items must be measured before the full training budget is committed:
- **The Potsdam memory headroom (D18).** A forward-only Stage A probe, with no training.
- **The uniform-LoRA cost factor.** This needs a short timing run of about 50 steps with no
  evaluation. That is training, so it requires approval as the first step of Stage C.

## Do not do yet
- Any training, scoring or selector code.
- Opening Potsdam labels before the split hash exists.
- Opening any test.
- Downloading LoveDA before approval.
