# DSSA Implementation Freeze

**This is the single-source-of-truth consolidated statement of the frozen DSSA research design**, current as of the backbone decision below. It supersedes nothing on its own authority — every line here is a pointer to the governing document where the decision was actually made and justified. Read those documents for reasoning; read this one for the current state.

**Governing documents, in the order the design was built:** `DSSA_ABSTRACT_GAP_ANALYSIS.md` → `DSSA_PROJECT_FREEZE.md` → `DSSA_FREEZE_FINAL_REVIEW.md` → `DSSA_DATASET_SELECTION_AUDIT.md` → `DSSA_PRITHVI_COMPATIBILITY_AUDIT.md` → `DSSA_PREIMPLEMENTATION_CALIBRATION.md` → `DSSA_SANITY_CHECK_REPORT.md` → this document.

---

## 1. Dataset Pair — `[FROZEN]`

**ISPRS Potsdam (IRRG) → ISPRS Vaihingen (IRRG).**

Selected from among three defensible candidates (LoveDA Urban→Rural, Potsdam→Vaihingen, DynamicEarthNet cross-region) presented without ranking in `DSSA_DATASET_SELECTION_AUDIT.md`. Verified against the Prithvi backbone in `DSSA_PRITHVI_COMPATIBILITY_AUDIT.md` (🟡 YELLOW — compatible via documented transformation). The original candidate, LoveDA → DeepGlobe, was ruled out (🔴 RED) due to a confirmed class-taxonomy mismatch and is retained only as historical record in `DSSA_PROJECT_FREEZE.md` §P.

## 2. Backbone / Checkpoint — `[FROZEN]`

**Prithvi-EO-2.0-300M** — exact checkpoint `ibm-nasa-geospatial/Prithvi-EO-2.0-300M`.

- 600M and 100M are **not part of the primary experiment**.
- Backbone size is **not an experimental variable** in this project — no ablation in Section 11 varies it.
- Changing the backbone after implementation begins is a **research-design change requiring an explicit freeze review**, since it changes `patch_size` and therefore the preprocessing tiling geometry (Section 4).
- This resolves the checkpoint ambiguity that stopped execution in `DSSA_SANITY_CHECK_REPORT.md` §2.

## 3. Input Contract — `[FROZEN]`

Verified directly from the checkpoint's raw `config.json` (`DSSA_PRITHVI_COMPATIBILITY_AUDIT.md` §1):

| Property | Value |
|---|---|
| `in_chans` | 6 |
| Band order | Blue, Green, Red, Narrow-NIR, SWIR1, SWIR2 (HLS-harmonized naming) |
| `patch_size` | `[1, 16, 16]` (300M-specific) |
| `img_size` | 224 |
| `embed_dim` / `depth` / `heads` | 1024 / 24 / 16 |
| Input tensor shape | `(B, 6, T, 224, 224)` |
| Per-band normalization mean/std | As published in the checkpoint config |

## 4. Radiometric Contract — `[FROZEN]`

Per `DSSA_PREIMPLEMENTATION_CALIBRATION.md` §3, §9:

- **Band mapping:** Green→Green, Red→Red, aerial-IR→Narrow-NIR (approximate correspondence, explicitly documented, not exact); Blue/SWIR1/SWIR2 zero-filled in normalized space (mathematically equivalent to using only the pretrained weight-slices for the three available bands — no weights reinitialized).
- **Radiometric strategy: Strategy C** — a fixed per-channel affine transform, fit **once, on Potsdam (source) statistics only**, frozen, and applied **unchanged** to both Potsdam and Vaihingen. No dataset-specific normalization, no per-image contrast stretching, no histogram matching (all rejected — see `DSSA_PREIMPLEMENTATION_CALIBRATION.md` §2 for why each would suppress the very signal DSS measures).
- Does **not** claim to recover true physical reflectance — no such recovery is possible given the available documentation (no official ISPRS reflectance-conversion exists).

## 5. Temporal Contract — `[FROZEN]`

Per `DSSA_PREIMPLEMENTATION_CALIBRATION.md` §6:

- **True `num_frames=1`.** Confirmed directly against the actual model source (`prithvi_mae.py`): positional embeddings are sinusoidal, not a learned 4-slot table, and the code contains an explicit path that exactly recomputes the positional embedding for a changed frame count. Precedented by an official NASA-IMPACT downstream config (`burn_scars.py`) using `num_frames=1` in production.
- `TemporalEncoder` (calendar-date encoding) is inactive — disabled in the released checkpoint config (`coords_encoding: []`). No acquisition-date metadata decision is needed.

## 6. DSS Definition — `[FROZEN]`

Per `DSSA_PROJECT_FREEZE.md` §F/O-C/O-D:

- Computed **once**, on the frozen backbone, before any adaptation, from labeled source + **unlabeled** target-probe data only.
- Per individual transformer layer (not per stage/module group).
- **Metrics: cosine distance and MMD only.** CKA is deferred — not implemented, no unpaired-sample variant invented (N-1, Flag 1).
- Pooling: mean over spatial tokens, per image, per layer.
- Aggregation: mean of per-target-image cosine distances to a single source centroid.
- Normalization: z-scored against a source-vs-source null-baseline distribution (bootstrap-estimated), per layer, before ranking.
- Exact cosine formula fixed in `DSSA_PROJECT_FREEZE.md` §O-D.

## 7. Layer-Selection Policy — `[FROZEN]`

Per `DSSA_PROJECT_FREEZE.md` §G/O-H:

- Rank layers by normalized DSS, descending; Top-K or threshold, compared empirically.
- K = 0 → decoder-only baseline (legitimate). K ≥ num_layers → clamped to "all layers" (≈ uniform LoRA).
- Deterministic given fixed inputs; ties (within 1e-6) broken by lower layer index.
- K/threshold and final metric chosen **only** on target-validation, never target-test.

## 8. LoRA Configuration — `[FROZEN]`

Per `DSSA_PROJECT_FREEZE.md` §H/O-E/O-F/O-G:

- Rank **r = 8**, fixed across all selected layers.
- Applied to attention **query and value** projections only (W_q, W_v).
- Segmentation decoder always trainable, regardless of K.
- No separate parameter-budget cap — DSSA and random-K match automatically in trainable-parameter count by construction (same K, rank, target matrices).

## 9. Target Split — `[FROZEN]`

Per `DSSA_PROJECT_FREEZE.md` §J/O-I:

- **60% target-train / 15% target-validation / 25% target-test.**
- **target-probe** (unlabeled): a 10–20%-sized slice of target-train; labels present but unused during selection.
- target-validation and target-test are **never** touched by DSS or layer selection.

## 10. Baselines — `[FROZEN]`

Per `DSSA_PROJECT_FREEZE.md` §Q:

Source-only · Full fine-tuning · Uniform LoRA · Adapters · Visual Prompt Tuning (if compatible) · DSSA (Top-K by DSS) · **Random-K layer selection** (approved, N-1) · **Source-vs-source null baseline** (approved, N-1).

## 11. Required Ablations — `[TO BE EXECUTED]`

Per `DSSA_PROJECT_FREEZE.md` §T — designed, none yet run:

1. Source-vs-source null baseline (run first).
2. Random-K layer selection, matched K.
3. Lowest-DSS layer selection.
4. Early / middle / late fixed-position layer selection.
5. Cosine-vs-MMD metric ablation (CKA excluded).
6. Top-K sweep (validation-only).
7. Probe-size sensitivity.
8. Seed sensitivity.
9. Cross-domain validation (second, different domain shift).
10. Full efficiency measurement (parameters, memory, time) across all of the above.

## 12. Sanity-Check Criteria — `[TO BE EXECUTED]`

Per `DSSA_PREIMPLEMENTATION_CALIBRATION.md` §7, confirmed **not yet run** by `DSSA_SANITY_CHECK_REPORT.md`:

Seven pre-registered checks (forward pass succeeds; no NaN/Inf; activation magnitude within two orders of magnitude of a reference forward pass; cross-sample variance > 1e-6; DSS diagnostic finite and non-zero; every transformer block produces output; no labels loaded / no optimization occurs). Blocked in the last attempt by two missing prerequisites, both now partly addressed by this document: the checkpoint ambiguity is resolved (Section 2 above); ISPRS Potsdam/Vaihingen data and a named HLS reference sample are still **not present in this environment** and remain outstanding artifacts, not research decisions.

---

## Not Part of Scope

- **Prithvi-EO-2.0-600M and -100M** — investigated for compatibility only, never adopted; not a comparison arm.
- **CKA as a DSS metric** — deferred to future work, not implemented.
- **Any dataset pair other than Potsdam→Vaihingen** for the primary experiment (LoveDA Urban→Rural and DynamicEarthNet cross-region remain documented alternatives in `DSSA_DATASET_SELECTION_AUDIT.md`, not adopted).
- **True physical reflectance recovery** for Potsdam/Vaihingen — not achievable with available documentation; the radiometric contract (Section 4) is an explicitly bounded approximation, not a claim of exact calibration.
- **Segmentation training, LoRA training, layer selection execution, or any metric computation** — none of this has occurred. This document freezes a design, not a result.

---

## Final Status

## FROZEN DESIGN — PENDING SANITY EXECUTION

Every implementation-critical research and engineering decision (dataset, backbone, input/radiometric/temporal contracts, DSS definition, layer selection, LoRA configuration, target split, baselines, required ablations) is now `[FROZEN]`. Nothing above constitutes an implementation-ready **PASS** — the non-degeneracy sanity check (Section 12) has not been executed, and per this project's standard throughout, a check that has not been run is not yet a check that has passed. Its execution is the correct next action, exactly as specified in `DSSA_PREIMPLEMENTATION_CALIBRATION.md` §7, once the outstanding artifacts (Potsdam/Vaihingen data, a named HLS reference sample) are available and once `torch` and the model's dependencies are installed — none of which occurred in this session.
