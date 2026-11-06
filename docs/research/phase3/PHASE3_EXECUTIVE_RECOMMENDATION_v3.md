# Phase 3: executive recommendation, v3

Revision history:
- v1 and v2 are kept unchanged.
- v3 (2026-11-06) aligns with protocol v3, decision register v2 and the measurements of 2026-11-06.

## Direction (unchanged)
Path 2 is primary: a pre-registered, oracle-validated test of whether any selection signal beats a
frozen depth prior, with label-free vs label-using comparisons. A method claim is nested inside it.

## What changed since v2
- **GSD operator corrected:** 9 → 5 cm uses a 124-px window up-sampled to 224 (protocol v3 §4).
- **Three Stage D scenarios,** with consistent run, model and compute counts (protocol v3 §6).
- **No joint false-positive claim.** LoveDA is a replication requirement (D11).
- **Measured memory:**
  - Potsdam training is safe at ≈ 9.1 GB worst case;
  - **in-process evaluation is unsafe** at ≈ 13.2 GB, so evaluation must run in a separate process;
  - one-tile evaluation peaks at 8.19 GB.
- **Measured costs:** evaluation at 3.22 s/MP; uniform LoRA at 1.10 × L0.

## Compute (measured rates)
| Scenario | Stage D new runs / tested models | ISPRS total |
|---|---|---|
| **S1** candidate passes | 77 / 80 | **≈ 125 h** |
| **S2** no candidate, prior transfers | 67 / 70 | **≈ 115 h** |
| **S3** no candidate, prior fails | 42 / 45 | **≈ 92 h** |

LoveDA adds about 40–65 h (unmeasured).

## Can the full budget be approved now?
**Not yet in full. A staged approval is justified:**
1. **Approvable now:**
   - Stage A completion (the split manifest, the radiometric refit decision);
   - **one** bounded 2-tile sequential evaluation-memory measurement, or adopting one-tile-per-process
     evaluation (D25);
   - Stage B;
   - Stage C (75 runs, ≈ 45 h). Memory for training (≈ 9.1 GB) and single-tile evaluation (8.19 GB) is
     within 11.5 GB.
2. **Approve after Stage C:** the Stage D budget of the scenario that actually occurs (≈ 26–47 h + 16–28
   h test).
3. **LoveDA:** a separate approval (licence, download, RGB mapping), required before any generalisation
   or method claim.

## Decisions requiring approval
- From register v1: **D2–D6, D9, D10, D13, D15–D17, D20**.
- From register v2:
  - **D8** (scenario budgets);
  - **D11** (the replication wording);
  - **D14** (the GSD operator);
  - **D22** (separate-process evaluation);
  - **D23** (primary analyses for S2 and S3);
  - **D25** (multi-tile evaluation option).
