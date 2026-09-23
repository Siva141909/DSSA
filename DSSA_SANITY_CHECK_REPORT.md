# DSSA Sanity Check Report

**Scope:** Section 7 (Non-Degeneracy Sanity Check) of `DSSA_PREIMPLEMENTATION_CALIBRATION.md` only. Not training. Not LoRA. Not layer selection. Not segmentation.

**Outcome up front:** execution did not proceed past pre-flight verification. Two independent, pre-registered stop conditions were triggered before any model or data was touched. Nothing was substituted, fabricated, or worked around. This report documents exactly what is missing and why nothing further was attempted.

---

## 1. Environment

Checked directly in this session, before any execution attempt:

| Item | Status |
|---|---|
| Python | 3.14.3 present |
| `torch` | **Not installed** |
| `transformers` / `timm` / `einops` | Not checked further once `torch` was confirmed absent (no point checking downstream dependencies) |
| Network access to huggingface.co | Available (HTTP 200 confirmed) |
| Hugging Face cache (`~/.cache/huggingface`) | Present but contains no Prithvi artifacts — `hub/` and `datasets/` subdirectories exist from unrelated prior work; no `ibm-nasa-geospatial/*` entries |
| Hugging Face auth token | **Not present** (no `~/.cache/huggingface/token`, no `HF_TOKEN`/`HUGGINGFACE_*` environment variable) |
| ISPRS Potsdam data, anywhere on this machine | **Not found** (searched Documents, Downloads, Desktop) |
| ISPRS Vaihingen data, anywhere on this machine | **Not found** |
| A known-good, natively-scaled HLS reference sample | **Not found** |
| Local `.pt`/checkpoint files matching "Prithvi" | **None** (only unrelated checkpoints from a different, unrelated project elsewhere in `Documents`) |

No packages were installed and no downloads were attempted, in either direction (data or model), per the instruction not to substitute or fabricate missing artifacts.

## 2. Exact Checkpoint

**Not determined — execution stopped here per explicit instruction (Strict Rule 4).**

Grepped all five governing documents (`DSSA_PROJECT_FREEZE.md`, `DSSA_FREEZE_FINAL_REVIEW.md`, `DSSA_PRITHVI_COMPATIBILITY_AUDIT.md`, `DSSA_PREIMPLEMENTATION_CALIBRATION.md`, `DSSA_ABSTRACT_GAP_ANALYSIS.md`) for any explicit selection of a specific checkpoint size. Result: **`Prithvi-EO-2.0-300M` and `Prithvi-EO-2.0-600M` are both referenced only as checkpoints whose *compatibility was investigated* (both share the same `in_chans`, `bands`, `num_frames` input contract, per `DSSA_PRITHVI_COMPATIBILITY_AUDIT.md` §1) — neither document freezes one as the project's actual choice.** The original abstract itself says only "Prithvi-EO-2.0 (initial choice)," without a size. A 100M variant also exists and was not discussed at all.

This is exactly the ambiguity Strict Rule 4 requires stopping on, so it is reported rather than resolved. Note for whoever makes this decision: it also determines `patch_size` (`[1,16,16]` for 300M vs. `[1,14,14]` for 600M), which changes the exact tiling geometry in Section 9's preprocessing contract — this is not a cosmetic choice.

## 3. Exact Dataset Samples Used

**None used — no samples exist locally, and none were fetched.**

- ISPRS Potsdam (IRRG): not available locally. Per the ISPRS benchmark's own access process, this dataset requires a data-request/registration step, not a plain public download — acquiring it was out of scope for this execution step and was not attempted.
- ISPRS Vaihingen (IRRG): same status.
- A "known-good, natively-scaled HLS reference sample" for Check 3: not available locally. No specific file was named as the intended reference anywhere in the governing documents — this itself is a second, independent gap (see Section 6, Check 3).

## 4. Exact Preprocessing Parameters

**Specified in the frozen documents, but never applied — there was no data to apply them to.** For completeness, the contract that *would* have been used (from `DSSA_PREIMPLEMENTATION_CALIBRATION.md` §9) is: source-fit-only affine radiometric transform (Potsdam statistics only, frozen, applied unchanged to both domains), zero-fill for Blue/SWIR1/SWIR2, `T=1`, tiled to the checkpoint's patch grid. No parameter values (e.g., the actual fitted affine coefficients) exist yet, since fitting them requires the Potsdam data this report confirms is unavailable.

## 5–7. Results, Numerical Criteria, and PASS/FAIL for Checks 1–7

Every check requires either the model (blocked: checkpoint undetermined, `torch` not installed) or the data (blocked: no local Potsdam/Vaihingen/reference sample). None could be attempted.

| Check | Requires | Status | Reason |
|---|---|---|---|
| 1 — Forward pass succeeds | Model + both datasets | **NOT EXECUTED** | Checkpoint undetermined; datasets unavailable |
| 2 — `torch.isfinite` on all layers | Model + both datasets | **NOT EXECUTED** | Same |
| 3 — Activation magnitude vs. reference | Model + both datasets + reference sample | **NOT EXECUTED** | Same, plus no reference sample identified at all (see below) |
| 4 — Cross-sample variance > 1e-6 | Model + both datasets | **NOT EXECUTED** | Same |
| 5 — DSS diagnostic (finite, non-zero) | Model + both datasets | **NOT EXECUTED** | Same |
| 6 — All transformer blocks produce output | Model | **NOT EXECUTED** | Checkpoint undetermined |
| 7 — Procedural leakage audit (no labels loaded, no optimization) | A real run to audit | **Vacuously true, not meaningfully verified** | Since no execution occurred at all, no labels were loaded and no optimization ran — but this is true only because nothing ran, not because a real pipeline was audited and found clean. Recorded honestly as a non-result, not a pass. |

**No numerical results exist for any criterion.** No criterion was weakened, loosened, or reinterpreted to produce a result — none was attempted.

**Check 3, specifically:** beyond the general data unavailability, the pre-registered procedure names "any publicly available Prithvi demo/example tile" as an acceptable reference — but does not name a specific one. Even with data and a checkpoint available, this would need a specific file identified and recorded *before* running the check (to keep the criterion pre-registered rather than chosen after the fact) — this should be done at that time, not silently picked now.

## 8. Warnings

- None generated — no code executed.

## 9. Deviations from the Pre-Registered Procedure

**None.** No threshold was changed. No criterion was loosened. No checkpoint was silently chosen. No dataset was substituted. No reference sample was fabricated. The procedure was not deviated from — it was not run, and the reasons are stated plainly above rather than concealed.

## 10. Final Verdict

## 🟡 YELLOW — sanity check could not be fully executed because of missing external/local artifacts, without changing criteria

Two independent blockers, both explicitly covered by this task's own stop conditions:

1. **Checkpoint variant not frozen** (300M vs. 600M vs. a possible 100M) — a genuine open decision in the project's own governing documents, not something this execution step is authorized to resolve on its own.
2. **No local ISPRS Potsdam/Vaihingen data, and no identified known-good HLS reference sample** — required for every one of the seven checks; none was substituted or fabricated.

Neither blocker reflects a failure of the frozen research design, the radiometric strategy, or the temporal strategy — nothing about those was tested, so nothing about them is now in question. This is a readiness gap (missing artifacts and one missing decision), not a RED finding against the methodology.

### What would need to happen before this check can actually run

1. **A team decision** on the exact Prithvi-EO-2.0 checkpoint (100M / 300M / 600M), recorded in `DSSA_PROJECT_FREEZE.md` as a frozen item — not decided here.
2. **Access to ISPRS Potsdam and Vaihingen IRRG data**, obtained through the ISPRS benchmark's own access process.
3. **A specific, named known-good HLS reference sample** for Check 3, identified and fixed *before* the check is next attempted (not chosen after seeing any results).
4. A working Python environment with `torch` (and the model's dependencies) installed — not present in this session and not installed here, since doing so ahead of resolving 1–3 would not have enabled execution regardless.

Once 1–4 are in place, this exact report's Section 5–7 table should be re-run with real results — not amended, a fresh execution against the same seven pre-registered criteria stated in `DSSA_PREIMPLEMENTATION_CALIBRATION.md` §7, unchanged.
