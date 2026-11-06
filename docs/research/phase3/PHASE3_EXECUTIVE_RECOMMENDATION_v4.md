# Phase 3: executive recommendation, v4

Revision history:
- v1–v3 are kept unchanged.
- v4 (2026-11-06) aligns with `PHASE3_COMPUTE_AUDIT_2026-11-06.md`, protocol v4 and decision register
  v3.

## Agreed figures (identical in all four v4-level documents)
- **Per run:** T_arm + 1,214 s. This covers 4 s start-up, a 120 s cache allowance, 8 validation tiles
  in one process each at 132.5 s (1,060 s), and 30 s reload verification.
- **Stage C:** 75 runs, **48.8 h**.

| Scenario | Stage D runs / hours | Potsdam test models / hours | ISPRS total |
|---|---|---|---|
| S1 | 77 / 51.8 h | 80 / 29.4 h | **135.0 h** |
| S2 | 67 / 45.2 h | 70 / 25.8 h | **124.7 h** |
| S3 | 42 / 28.8 h | 45 / 16.6 h | **99.1 h** |

- **Vaihingen test:** 75 models, 2.9 h.
- **LoveDA Stage C (separate):** 39.8–53.9 h.
- **Evaluation:** one process per tile, ≤ 7.54 GB each. Training processes never evaluate Potsdam tiles.
- **Memory:** training ≤ 10.66 GB conservative bound; the 11.5 GB guard, an 11.0 GB abort sampler and a
  10.5 GB stop rule; an early-block canary run first.

## Stage C readiness: **READY WITH EXPLICIT LIMITS**
Stage C can be authorised safely once the approvals below are given. The limits:
1. one evaluation process per tile;
2. no Potsdam evaluation inside training processes;
3. an early-block canary first, with the sequence stopping if any process exceeds 10.5 GB;
4. the existing guards (power, sleep, thermal, swap growth 512 MB, footprint 11.5 GB, runtime 1.5×,
   no retry);
5. Stage B scores hashed before any single-block run;
6. the Potsdam split hashed before any Potsdam label is read;
7. budget 48.8 h (± about 10%) for Stage C alone.

**Stage D and the test openings are not part of this authorisation** (D28).

## Decisions still requiring approval before Stage C
- **D3:** use the Potsdam labels; freeze and hash the split first.
- **D4:** refit the radiometric transform on Vaihingen training images.
- **D5 and D6:** the Fisher and LogME definitions (Stage B).
- **D9:** evaluate at step 2,000 only.
- **D10 and D11:** the frozen quadratic prior and the non-inferential gate (LoveDA as replication).
- **D13:** 3 seeds in Stage C.
- **D14:** the candidate list and the corrected GSD operator.
- **D15:** Prior-3 as the primary comparator.
- **D16 and D17:** test-opening roles and the contradiction / early-access policy.
- **D20:** a new Phase 3 code directory.
- **D22 and D25:** separate-process, one-tile-per-process evaluation.
- **D27:** the memory limits and the canary.
- **D8 (Stage C part only):** 48.8 h.

**Decided later:** D8 (Stage D part), D23, D28 after Stage C; D2 (LoveDA) before any generalisation
claim.
