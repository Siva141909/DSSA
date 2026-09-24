# DSSA Phase 2B-A — Final Split + DSS K-Sweep Report

**No LoRA trained. No segmentation trained. No optimizer instantiated. No gradients computed. No frozen methodology modified. No final K selected. No method ranked.**

**This phase stopped early, correctly, at two explicit, pre-specified stop conditions.** What follows documents exactly what was checked, what stopped and why, and what genuinely could still be done independently of those two blockers.

Status vocabulary used throughout: **VERIFIED** / **UNSPECIFIED — REQUIRES DECISION** / **BLOCKER** / **NOT APPLICABLE**.

---

## 1. Scope

Attempt: (1) lock a formal file-level Vaihingen split, (2) recompute DSS on the locked target-probe, (3) execute the authorized Top-K sweep, (4) compare DSSA against Early/Middle/Late at the swept K values, (5) audit and report. **Actual outcome: steps 1–4 could not proceed past their respective specification checks; step 5 (this report) documents why, plus the independent sub-tasks that could and did proceed (source/null mechanism inspection, a non-training repeatability check, and a leakage audit).**

## 2. Governing K-Sweep Specification

Searched directly, not from memory: `DSSA_PROJECT_FREEZE.md`, `DSSA_IMPLEMENTATION_FREEZE.md`, `DSSA_FREEZE_FINAL_REVIEW.md`, `DSSA_ABSTRACT_GAP_ANALYSIS.md`.

Every mention of the Top-K sweep states only that it is **required as an activity**:
- `DSSA_IMPLEMENTATION_FREEZE.md` §11: *"6. Top-K sweep (validation-only)."*
- `DSSA_PROJECT_FREEZE.md` §T: *"Top-K sweep, chosen on validation only — already E8."*
- `DSSA_ABSTRACT_GAP_ANALYSIS.md` G-13: confirms K "will be chosen on a held-out validation split" as a **protocol**, not a value.

**No document anywhere specifies an actual K grid** (no list of numbers, no range, no step size). No seed, ordering, or aggregation rule for a sweep is specified either, because the sweep itself was never numerically instantiated.

```
K-SWEEP GRID UNSPECIFIED — REQUIRES DECISION
```

No arbitrary grid (e.g., 2/4/6/8/12) was substituted. Per instruction, this is reported, not resolved.

## 3. Final Vaihingen Split Methodology

`DSSA_PROJECT_FREEZE.md` §O-I fixes the **ratios** (60/15/25) and the **relationship** (target-probe is a slice of target-train, 10–20% of the pool). It does **not** specify: a random seed, a deterministic ordering rule (e.g., sort-then-slice vs. shuffle), or any grouping constraint (e.g., whether spatially adjacent Potsdam-style tiles — not applicable to Vaihingen's irregular area numbering, but the general principle — should be kept together or separated across splits). Searched directly for "seed," "shuffle," "deterministic order" in both freeze documents: no matches.

Two different, equally literal readings of "60/15/25 of 33 files" are already possible without any further rule (e.g., sorted-alphabetical-then-sliced vs. a seeded shuffle) — sorted vs. shuffled selection could easily produce a **different** manifest, and nothing in the frozen documents picks between them.

```
SPLIT METHODOLOGY UNSPECIFIED — REQUIRES DECISION
(missing: split-construction seed and/or deterministic ordering rule)
```

**No split was created.** No file was written to `dssa/artifacts/splits/`. Per instruction, this is reported rather than silently resolved by picking a plausible-looking rule.

## 4. Complete File-Level Split Manifest

**NOT APPLICABLE.** No manifest exists (Section 3).

## 5. Split Integrity Verification

**NOT APPLICABLE.** Nothing to verify — no manifest was created.

## 6. Final DSS Input Definition

**NOT APPLICABLE — blocked by Section 3.** The frozen instruction is explicit that the final DSS computation must use "ONLY the formally locked target-probe images" — since no formal lock exists, no final DSS computation was attempted. Running it against an ad hoc file selection (as Phase 2A did, explicitly for mechanism validation, not as "the final calculation") would not satisfy this phase's own stated requirement and was not done.

## 7. 24-Layer Cosine DSS Results (Final)

**NOT APPLICABLE — blocked by Section 6.** No new 24-layer table was computed in this phase. Phase 2A's existing tables (Probes A/B/C) remain the only computed results and are unchanged, not reproduced here.

## 8. Final Source-vs-Source Null

**NOT APPLICABLE — blocked by Section 6**, for the DSS itself. However, Part 5 of the task (inspecting the *mechanism*, independent of running it on a new split) was completed:

**Source/null construction mechanism — inspected directly from `dssa/sanity/run_phase2a_dss.py` (unchanged, not modified in this phase):**
- Source role: pooled patch-token representations (cls excluded) from a fixed file list, centroid = mean of pooled vectors.
- Null pool: a **separate**, disjoint file list (never overlapping the source-role files), split via `bootstrap_null()` into repeated random 50/50 halves (`random.Random(seed).shuffle` on the pool's index list, `n = len(pool)`, `half = n // 2`), cosine-distance computed between the two halves each resample, per layer, `BOOTSTRAP_RESAMPLES = 40` fixed resamples, `BOOTSTRAP_SEED = 1234` fixed.
- Normalization: `(raw_dss − null_mean) / (null_std + 1e-8)`, per layer.
- This mechanism was **reused, not redesigned**, per Part 5's explicit instruction — it is the same code Phase 2A used, verified by direct inspection to still be exactly as described in the Phase 2A report.
- **No issue was found** between this mechanism and the (not-yet-created) formal split — the mechanism itself only requires a source file list and a disjoint null file list, both of which the eventual split would supply once locked. There is nothing to report as a conflict.

## 9. Authorized Top-K Sweep

**NOT APPLICABLE — blocked by Section 2.** No K grid exists to sweep over. No layer sets were selected at any new K value in this phase.

## 10. DSSA vs Early/Middle/Late Overlap

**NOT APPLICABLE — blocked by Sections 2 and 9.** No new comparison table was produced. The only existing comparison remains Phase 2A's K=6 result (`DSSA_PHASE2A_DSS_VALIDATION_REPORT.md` §8, `DSSA_PHASE2B_PREFLIGHT_REPORT.md` §3): DSSA@K=6 == Late@K=6 exactly, unchanged and not reproduced here.

## 11. Random-K / Lowest-DSS Status

Inspected the frozen definitions directly — not modified, not recomputed:

- **Random-K:** `DSSA_PROJECT_FREEZE.md` §Q lists it as a **frozen baseline reserved for training** ("Random-K layer selection... same K, same LoRA configuration, same training data, same training budget, same evaluation protocol") — its purpose is defined relative to an actual LoRA-training run, not a standalone selection computation. The Phase 2A illustrative set (`[0,3,7,8,19,20]`, seed 42, K=6) exists and is unchanged, but K=6 itself is not locked (Section 2), so this set is not being newly used or extended here.
- **Lowest-DSS:** similarly a **control reserved for later comparison**, not a target of new computation in this phase. Phase 2A's illustrative set (`[0,2,3,4,5,6]`, from Probe A) is unchanged.

**Distinction, as required:** both are **"defined now but reserved for training"** — neither was "computed for this phase," since this phase performed no new selection computation of any kind.

## 12. MMD Status

No document requires MMD to be recomputed on a final/locked split at this specific phase — MMD's frozen role (`DSSA_PROJECT_FREEZE.md` §N-1 Flag 1, §T item 5) is a **comparison/ablation**, already executed once in Phase 2A. **No new MMD computation was performed in this phase.** The Phase 2A MMD artifact (`phase2a_dss_results.json`'s `mmd_ablation` block, Top-6 = `[5,4,11,6,19,3]` on Probe A) is retained, unmodified, as historical comparison only. Cosine was not replaced by MMD anywhere in this phase — no MMD code was even invoked in this phase's execution.

## 13. Reproducibility Audit

| Seed | Value | Status |
|---|---|---|
| Split-construction seed | **none — no split was created** | UNSPECIFIED — REQUIRES DECISION |
| Bootstrap null seed | 1234 | VERIFIED, unchanged from Phase 2A |
| Random-K seed | 42 | VERIFIED, unchanged from Phase 2A (illustrative set only, not re-used for new selection here) |
| PyTorch global seed | not set | UNSPECIFIED (unchanged status from Phase 2B pre-flight — no training-relevant randomness has been exercised that would require it) |
| NumPy global seed | not set | UNSPECIFIED (same basis) |

**Non-training repeatability check — performed, per explicit authorization (Part 10), using the exact existing Probe A configuration, no methodology change:**

`dssa/sanity/run_repeatability_check.py` re-ran Probe A's identical 48-file configuration (same source/target/null file lists, same Strategy C coefficients, same checkpoint, same bootstrap seed) and compared against the stored Phase 2A result.

```
raw_dss_bitexact_match:        true   (max abs diff: 0.0)
normalized_dss_bitexact_match: true   (max abs diff: 0.0)
ranking_bitexact_match:        true
```

**Result: bit-exact, not merely numerically close.** This closes a limitation explicitly flagged as untested in `DSSA_PHASE2B_PREFLIGHT_REPORT.md` §8 ("MPS determinism... not empirically tested in this session"). It is now empirically verified, for this specific computation (deterministic eval-mode forward pass with no dropout/masking, plus CPU-side Python `random` for the bootstrap) — **not** a general claim that all MPS operations are deterministic, only that this exact pipeline, run twice, produced identical output. The DSS procedure itself was not altered to force this outcome — the same, unmodified code was simply invoked twice.

## 14. Leakage Audit

Code-searched directly across every file in `dssa/sanity/` (not asserted from memory):

- **No label file path** appears anywhere (`grep -niE "label|gts_for_participants|ground_truth|\.mask\."` across all `.py` files returns only the word "label" used as a plain string/logging parameter name — e.g., `check1_forward_pass(model, x, label: str)` — never a file path).
- **No optimizer** — `grep -niE "optim|\.backward\(\)|lr_scheduler|\.step\(\)"` returns zero real matches (only comments/docstrings/audit-flag variable names stating that none exists).
- **No gradients** — every forward pass in every script is wrapped in `torch.no_grad()` (confirmed at 4 call sites: `diagnostics.py`, `model.py`, `run_phase2a_dss.py`, `run_sanity_check.py`'s docstring/design).
- **No target-validation or target-test path** appears anywhere — confirmed, and unsurprising, since no split manifest exists yet to even name such paths.
- **No LoRA or segmentation training code** exists anywhere in `dssa/sanity/`.

**Leakage audit: clean.** No violation found.

## 15. Artifacts

| Artifact | Status |
|---|---|
| `dssa/artifacts/splits/vaihingen_target_split_manifest.json` | **Not created** (Section 3) |
| `dssa/artifacts/dss/phase2b_final_dss_results.json` | **Not created** (Section 7) |
| `dssa/artifacts/dss/phase2b_final_dss_run.log` | **Not created** |
| `dssa/artifacts/dss/phase2b_a_repeatability_check.json` | **Created** — bit-exact repeatability result (Section 13) |
| `dssa/sanity/run_phase2b_final_dss.py` | **Not created** — no final DSS computation to implement without a locked split |
| `dssa/sanity/run_repeatability_check.py` | **Created** — the non-training repeatability check code |
| `DSSA_PHASE2B_A_FINAL_SPLIT_KSWEEP_REPORT.md` | This report |

**Phase 2A artifacts:** unmodified, unread-into-and-changed — only referenced. **Phase 1B artifacts:** unmodified.

## 16. Deviations from Frozen Methodology

**None.** No DSS definition, Strategy C coefficient, band mapping, checkpoint, T value, or selection rule was changed, approximated, or worked around. The two stop conditions (Sections 2, 3) are gaps in **specification**, not deviations from what **is** specified — nothing frozen was contradicted.

## 17. Open Decisions Remaining Before Training

1. **K-sweep grid** — an explicit list of K values must be chosen by the team (Section 2). Not inferable from existing documents.
2. **Split-construction methodology** — a seed and/or deterministic ordering rule for the 60/15/25 Vaihingen split must be chosen (Section 3).
3. Once 1–2 are resolved: the final, locked-split DSS computation (Sections 6–10) can be executed exactly as this phase's Parts 4–7 specify — no other blocker stands in the way of that work once these two decisions exist.
4. All items already listed in `DSSA_PHASE2B_PREFLIGHT_REPORT.md` §13 remain open and unchanged by this phase (training protocol, decoder architecture, LoRA init convention, whether MMD gets a full training condition, and the DSSA-vs-Late design question) — this phase did not touch or resolve any of them.

## 18. Final Status

**UNSPECIFIED — REQUIRES DECISION**, overall — driven entirely by items 1 and 2 in Section 17. **No BLOCKER** was found (nothing already decided conflicts with anything else). What *could* proceed independently of those two gaps was completed cleanly: the source/null mechanism was verified unchanged and conflict-free with the (future) locked split (Section 8), a real empirical reproducibility gap was closed with a bit-exact result (Section 13), and the leakage audit found nothing (Section 14).

**Stopping here, per instruction. No split, no final DSS computation, no K-sweep execution, and no further phase is begun. Waiting for the two named decisions before this phase's Parts 2–7 can be attempted.**
