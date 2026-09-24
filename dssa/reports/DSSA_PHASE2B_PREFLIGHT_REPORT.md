# DSSA Phase 2B Pre-Flight Report

**No LoRA trained. No segmentation trained. No optimizer run. No gradients computed. No frozen methodology modified. This is an implementation/design audit only.**

Status vocabulary used throughout: **VERIFIED** / **UNSPECIFIED — REQUIRES DECISION** / **BLOCKER** / **NOT APPLICABLE**.

---

## 1. Scope

Determine whether the Phase 2B adaptation experiment is sufficiently specified and implementation-ready to request separate training authorization. Nothing here trains anything, ranks methods, or predicts outcomes.

## 2. Frozen Inputs Verified

| Item | Status | Detail |
|---|---|---|
| Backbone / checkpoint | **VERIFIED** | `ibm-nasa-geospatial/Prithvi-EO-2.0-300M`, revision `9eb1b1102806593963daa333bcc491b1c6f8562f` (Phase 1B, byte-verified) |
| Dataset | **VERIFIED** | ISPRS Potsdam (IRRG) → Vaihingen (TOP/IRRG), 38 + 33 files staged and integrity-audited (Phase 1B) |
| Band mapping | **VERIFIED** | IR→Narrow-NIR, R→Red, G→Green; Blue/SWIR1/SWIR2 zero-filled in normalized space |
| T | **VERIFIED** | T=1 |
| Strategy C coefficients | **VERIFIED** | offset(IR,R,G)=(44.078086, 69.273417, 63.265727), scale=(51.043832, 61.576644, 59.248827) — fit on all 38 Potsdam files only, reused unchanged in Phase 2A |
| DSS definition | **VERIFIED** | Mean-pooled patch tokens, source centroid, cosine primary, bootstrap source-vs-source null (Phase 2A: 40 resamples), deterministic tie-break (1e-6 tolerance, lower index wins) |
| LoRA rank / target modules | **VERIFIED** | rank=8, W_q/W_v only (`DSSA_PROJECT_FREEZE.md` §O-E/O-F) |
| Backbone frozen / decoder trainable | **VERIFIED** | Stated frozen decisions; not yet exercised in code (no training code exists) |
| Target split ratios | **VERIFIED** | 60/15/25, target-probe carved from target-train (§O-I) |
| K=0 / K=all as frozen controls | **VERIFIED** | §G |
| Random-K / Lowest-DSS / Early / Middle / Late as frozen controls | **VERIFIED** | §Q (Random-K), Phase 2A report (Lowest-DSS/Early/Middle/Late definitions, consistent with §L required ablations) |
| CKA | **VERIFIED excluded** | Deferred, N-1 Flag 1 — not used anywhere in this audit |

## 3. DSSA Selection Verification

Inspected directly from `dssa/artifacts/dss/phase2a_dss_results.json` and `dssa/sanity/run_phase2a_dss.py` — not recomputed, not modified.

- Primary metric: **cosine** — confirmed (`raw_dss` field uses `cosine_dss_per_layer`, the only metric feeding `normalized_dss`/`ranking_desc`).
- Normalized DSS: `(raw_dss − null_mean) / (null_std + 1e-8)`, null_mean/null_std from a 40-resample bootstrap of an 8-vs-8 split of a 16-file null pool, seed 1234 — confirmed, matches §O-C.
- Ranking: descending normalized DSS, tie-break by lower layer index within 1e-6 — confirmed in code (`rank_layers()`), and no ties actually occurred in Probe A's data (verified: all 24 normalized values distinct beyond 1e-6).
- K=6 selection source: **Probe A only** (the first-defined, unshifted-crop, unshifted-file probe), used as the reference for defining illustrative control sets in Phase 2A — not re-derived here.

```
DSSA K=6 (Probe A, cosine, normalized DSS, Top-6):
[18, 19, 20, 21, 22, 23]

Late K=6 (fixed, last 6 of 24 layers):
[18, 19, 20, 21, 22, 23]

Are identical? YES
```

**As sets, `DSSA@K=6` and `Late@K=6` are identical.** No layer distinguishes them. Under the current frozen selection result, at this K, using this metric, these two named conditions would train LoRA on the exact same six transformer blocks and therefore cannot function as two different experimental arms — any observed difference between a run labeled "DSSA" and a run labeled "Late" at K=6 would be attributable only to training noise (seed, ordering, etc.), not to a difference in which layers were adapted. This was not changed, adjusted, or reinterpreted to be more convenient — it is reported exactly as Phase 2A found it.

## 4. Verify Whether an Alternative K Is Already Frozen

Searched `DSSA_PROJECT_FREEZE.md` and `DSSA_IMPLEMENTATION_FREEZE.md` directly for any numeric K commitment: none found. K is specified only as a *protocol* — "chosen only on target-validation, never target-test" (§G) — never as a fixed number.

**K=6 itself is not frozen.** It was used in Phase 2A explicitly and repeatedly labeled "illustrative... not a final K choice" (`DSSA_PHASE2A_DSS_VALIDATION_REPORT.md` §9, `run_phase2a_dss.py`'s `controls["note"]` field). It is the only K value any artifact currently defines layer sets for.

**No alternative K is authorized by the existing freeze.** No new K is introduced here.

## 5. Experiment-Condition Matrix

All layer-index values pulled directly from `phase2a_dss_results.json`'s `controls` block — not recomputed.

| Condition | K | Layer indices | Selection source | Uses target labels? | Uses target-test data? | LoRA rank | LoRA modules | Decoder trainable? | Backbone frozen? |
|---|---|---|---|---|---|---|---|---|---|
| A. DSSA (cosine) | 6 | `[18,19,20,21,22,23]` | Phase 2A, Probe A, normalized cosine DSS Top-6 | No | No (unlabeled Potsdam/Vaihingen crops only) | 8 | W_q, W_v | Yes | Yes |
| B. Random-K | 6 | `[0,3,7,8,19,20]` | Fixed seed 42, uniform draw over 24 indices | No | No | 8 | W_q, W_v | Yes | Yes |
| C. Lowest-DSS | 6 | `[0,2,3,4,5,6]` | Bottom 6 of the same Probe A ranking | No | No | 8 | W_q, W_v | Yes | Yes |
| D. Early | 6 | `[0,1,2,3,4,5]` | Fixed by depth position | No | Not applicable (no DSS computation involved) | 8 | W_q, W_v | Yes | Yes |
| E. Middle | 6 | `[9,10,11,12,13,14]` | Fixed by depth position | No | Not applicable | 8 | W_q, W_v | Yes | Yes |
| F. Late | 6 | `[18,19,20,21,22,23]` | Fixed by depth position | No | Not applicable | 8 | W_q, W_v | Yes | Yes |
| G. K=0 | 0 | `[]` | Frozen degenerate control | Not applicable | Not applicable | n/a | none | Yes (decoder-only) | Yes |
| H. K=all | 24 | `[0..23]` | Frozen degenerate control (≈ uniform LoRA) | Not applicable | Not applicable | 8 | W_q, W_v | Yes | Yes |
| I. MMD-selected | 6 | `[3,4,5,6,11,19]` | Phase 2A, Probe A, MMD Top-6 (comparison metric) | No | No | 8 | W_q, W_v | Yes | Yes |

No condition uses target labels or target-test data for **selection**. (Whether condition I is actually authorized as a full training run, versus a ranking-comparison-only artifact, is addressed in Section 10 — not assumed here either way.)

## 6. Capacity Equality Audit

**Structural guarantee (already frozen, holds regardless of exact numeric values below):** per `DSSA_PROJECT_FREEZE.md` §O-G, since rank and target modules are fixed and identical across every condition, trainable LoRA parameter count is a deterministic function of K alone. **Conditions A–F and I share K=6 and therefore share an identical LoRA parameter count by construction.** Condition G (K=0) has zero LoRA parameters. Condition H (K=24) has exactly 4× the LoRA parameter count of the K=6 conditions.

**Exact numeric LoRA parameter count per adapted layer — computed analytically, not yet empirically verified in code (no LoRA implementation has been written):** for `embed_dim=1024`, standard LoRA (ΔW = BA, no bias) on one `(1024×1024)` weight matrix at rank 8 adds `A∈ℝ^{8×1024}` and `B∈ℝ^{1024×8}`, i.e. `8×1024×2 = 16,384` parameters per matrix. With two targeted matrices (W_q, W_v) per layer: **32,768 trainable LoRA parameters per selected layer.** For K=6: **196,608** total LoRA parameters (conditions A–F, I). For K=0: **0**. For K=24: **786,432**.

**Caveat, flagged precisely:** this assumes the standard, no-bias, ΔW=BA LoRA formulation and does not assume any specific weight-initialization scheme (e.g., zero-init B) — **the exact LoRA bias/initialization convention is not frozen in any prior document** and is marked **UNSPECIFIED — REQUIRES DECISION** below. This does not threaten cross-condition fairness, since whatever convention is eventually chosen will be applied identically to every condition — but it does mean the 32,768-per-layer figure is analytical, not yet a verified property of actual code.

**Decoder trainable parameter count: UNSPECIFIED — REQUIRES DECISION.** No decoder architecture has been frozen anywhere (`DSSA_IMPLEMENTATION_FREEZE.md` only states "decoder always trainable" — no layer count, channel width, or head design is specified). This blocks computing a *total* trainable parameter count, but — critically — **does not threaten cross-condition equality**, since the same (whatever it ends up being) decoder architecture applies identically to every condition. It is a prerequisite for training, not a fairness risk between conditions.

**Required-identical checklist, audited:**

| Must be identical across same-K conditions | Status |
|---|---|
| LoRA rank | VERIFIED (8, frozen) |
| W_q/W_v targeting | VERIFIED (frozen) |
| Decoder architecture | UNSPECIFIED — REQUIRES DECISION (not yet chosen for *any* condition, so cannot yet differ *between* them) |
| Decoder trainability | VERIFIED (always trainable) |
| Backbone | VERIFIED (same checkpoint, same revision, frozen) |
| Optimizer | UNSPECIFIED — REQUIRES DECISION |
| Training steps/epochs | UNSPECIFIED — REQUIRES DECISION |
| Batch size | UNSPECIFIED — REQUIRES DECISION |
| Learning-rate schedule | UNSPECIFIED — REQUIRES DECISION |
| Augmentation | UNSPECIFIED — REQUIRES DECISION |
| Loss | UNSPECIFIED — REQUIRES DECISION |
| Checkpoint initialization | UNSPECIFIED — REQUIRES DECISION (LoRA A/B init scheme specifically) |
| Random seed policy (training) | UNSPECIFIED — REQUIRES DECISION |

**No BLOCKER found here** — nothing already committed conflicts with anything else. Every unresolved item is a genuine prerequisite decision, not yet made for even one condition, and therefore not yet capable of being *unequal* between conditions. The risk is that these get decided piecemeal, per-condition, rather than once as a single shared protocol — that would be a real fairness violation if it happened, but it has not happened.

## 7. Data Leakage Audit

**Selection stage (Phase 1B/2A, already executed):**

| Check | Status |
|---|---|
| Target-train labels used for selection | VERIFIED not used — no label file path appears anywhere in `run_phase2a_dss.py`, `run_real_data_sanity.py`, or `preprocessing.py` |
| Target-validation labels used for selection | VERIFIED not used (same basis) |
| Target-test labels used for selection | VERIFIED not used (same basis) |
| Source data used | VERIFIED — Potsdam only, for source centroid + null pool |
| Target-probe (unlabeled) data used | VERIFIED — Vaihingen images used, unlabeled role only |

**One genuine, precise gap, not previously surfaced:** the frozen split policy (§J/§R) defines target-probe as a slice **carved from target-train**, with target-validation and target-test held separately. **No formal, file-level 60/15/25 manifest has actually been generated for the 33 Vaihingen files.** Phase 2A's "target" role (16, then a shifted 16, of the 33 Vaihingen files) was assigned ad hoc, for a mechanism-validation exercise, not against a locked split. Because Phase 2A used these files in an **unlabeled** capacity only, and did not use its results to make any final K/metric commitment (Phase 2A explicitly declines to select a final K or a winning metric), this does not constitute the specific leakage the frozen policy prohibits (test labels or test-informed selection). **However:** before Phase 2B's *real*, final DSS computation (the one that will actually govern which layers get LoRA in an authorized training run) is executed, the 60/15/25 split must be formally generated and locked, and it must be confirmed that whichever files feed that final DSS computation fall within target-probe/target-train, not target-test. This is flagged as **UNSPECIFIED — REQUIRES DECISION**, not a BLOCKER (no violation has occurred; a necessary step has simply not yet happened).

**Training/evaluation stage:** not applicable — no training or evaluation code exists yet to audit.

## 8. Reproducibility / Seed Audit

| Component | Status | Detail |
|---|---|---|
| Python `random` seed (Random-K draw) | VERIFIED | seed=42, logged |
| Python `random` seed (bootstrap null resampling) | VERIFIED | seed=1234, logged |
| PyTorch global seed (`torch.manual_seed`) | **Not set anywhere in Phase 1B/2A code** | Forward passes run under `torch.no_grad()` with no dropout/masking active (`forward_features` applies no random masking, unlike MAE pretraining's `forward`), so this has not been observed to matter for the diagnostic numbers produced so far — but it was never explicitly set, and no training-time randomness (weight init, augmentation) has been exercised yet |
| NumPy seed | **Not set** | NumPy is used for array math (e.g., `np.mean`) but no NumPy-side randomness was invoked in Phase 1B/2A |
| MPS determinism | **UNSPECIFIED / documented limitation, not verified** | `torch.use_deterministic_algorithms(True)` was never called. Apple's MPS backend does not provide the same bit-exact determinism guarantees CUDA's deterministic mode does (e.g., reduction-order sensitivity in some ops). **This was not empirically tested** — no probe was re-run twice in this session to check bit-exact agreement of the DSS numbers. This is stated as a documented limitation, not glossed over as "presumed deterministic." |
| DataLoader/shuffling seed | NOT APPLICABLE yet | No DataLoader exists — Phase 1B/2A process files directly in fixed, logged order |
| LoRA A/B initialization seed | UNSPECIFIED — REQUIRES DECISION | No LoRA code exists |
| Decoder initialization seed | UNSPECIFIED — REQUIRES DECISION | No decoder code exists |
| Augmentation randomness | NOT APPLICABLE | No augmentation used or specified anywhere yet |

**Conclusion:** the *selection*-stage randomness (Random-K, bootstrap) is deterministic and reproducible by construction (fixed, logged seeds). The *model forward-pass* stage's reproducibility under MPS has not been empirically verified and should not be assumed bit-exact. The *training*-stage seed policy does not exist yet.

## 9. Training Protocol Audit

Searched both freeze documents directly for every item below: **none are specified.** No values are invented here.

| Item | Status |
|---|---|
| Optimizer | UNSPECIFIED — REQUIRES DECISION |
| Learning rate | UNSPECIFIED — REQUIRES DECISION |
| Weight decay | UNSPECIFIED — REQUIRES DECISION |
| Scheduler | UNSPECIFIED — REQUIRES DECISION |
| Warmup | UNSPECIFIED — REQUIRES DECISION |
| Epochs/steps | UNSPECIFIED — REQUIRES DECISION |
| Batch size | UNSPECIFIED — REQUIRES DECISION |
| Gradient accumulation | UNSPECIFIED — REQUIRES DECISION |
| Mixed precision | UNSPECIFIED — REQUIRES DECISION |
| Gradient clipping | UNSPECIFIED — REQUIRES DECISION |
| Loss function | UNSPECIFIED — REQUIRES DECISION |
| Class weighting | UNSPECIFIED — REQUIRES DECISION |
| Augmentation | UNSPECIFIED — REQUIRES DECISION |
| Early stopping | UNSPECIFIED — REQUIRES DECISION |
| Checkpoint selection rule | UNSPECIFIED — REQUIRES DECISION |

**Every item in this section is unresolved.** None is a BLOCKER (nothing conflicts with anything frozen) — but collectively, Phase 2B training cannot begin until this entire table is filled in as one shared protocol applied identically across every condition in Section 5.

## 10. Evaluation Audit

| Item | Status | Detail |
|---|---|---|
| mIoU | VERIFIED | Frozen, §K/§S |
| Per-class IoU | VERIFIED | Frozen |
| F1 score | VERIFIED | Frozen |
| Pixel accuracy | VERIFIED | Frozen |
| Trainable parameters, GPU memory, training time, inference time | VERIFIED | Frozen (efficiency metrics, §S) |
| Same target-test set for every condition | UNSPECIFIED — REQUIRES DECISION | Depends on the split manifest not yet generated (Section 7) |
| Same preprocessing across conditions | VERIFIED in principle (Strategy C is frozen and identical for all conditions) — NOT YET IMPLEMENTED in an evaluation script |
| Same inference procedure / tiling / aggregation | UNSPECIFIED — REQUIRES DECISION | No evaluation code exists; full-tile inference will need its own tiling/aggregation procedure (distinct from the 224×224 sanity-check crops), not yet specified |
| No test-time adaptation | VERIFIED by absence — nothing resembling test-time adaptation appears anywhere in the frozen design |
| No test labels used before final evaluation | VERIFIED so far (Section 7) — contingent on the split manifest being locked before Phase 2B's real training begins |

## 11. MMD Condition Audit

Inspected `phase2a_dss_results.json`'s `mmd_ablation` block directly — **not recomputed, not redesigned.**

- MMD ranking (descending, full 24 layers, verified directly from `mmd_ablation.mmd_ranking_desc`): `[5, 4, 11, 6, 19, 3, 18, 10, 13, 17, 20, 7, 16, 14, 8, 21, 15, 9, 12, 22, 2, 23, 1, 0]`; **MMD Top-6: `[5, 4, 11, 6, 19, 3]`** (same set as `{3,4,5,6,11,19}`).
- This was computed once, on Probe A, as the frozen "metric ablation" comparison (`DSSA_PROJECT_FREEZE.md` §T item 5: "DSS metric ablation: cosine vs MMD") — this specific ablation **is** frozen and **has** been executed (Phase 2A §13).
- **What is not settled:** whether an MMD-selected layer set is additionally authorized as its own **full LoRA-training condition** (Condition I in Section 5), on equal footing with DSSA/Random-K/Lowest-DSS/Early/Middle/Late. `DSSA_PROJECT_FREEZE.md` §Q ("Frozen Baselines") lists Source-only, Full fine-tuning, Uniform LoRA, Adapters, VPT, DSSA, Random-K, and the null baseline — **MMD is not named there.** It appears only under §T ("Required Ablations") as a ranking comparison. **This is flagged as UNSPECIFIED — REQUIRES DECISION, not assumed either way:** whether Phase 2B's first training run includes Condition I or defers it.
- Cosine remains primary. MMD was not substituted for it anywhere in this audit.

## 12. DSSA vs Late Identifiability

**At K=6, using the cosine metric, using fixed Top-K selection on Probe A: DSSA and Late are IDENTICAL** (Section 3). This is not a partial overlap — it is exact set equality, `{18,19,20,21,22,23}` both ways.

**Scientific consequence, stated plainly:** an adaptation run labeled "DSSA vs Late" at this specific K, under this specific selection rule, would train LoRA on the same six transformer blocks under both names. Any measured difference in the resulting segmentation performance would be attributable to training noise (seed, initialization, data order), not to a difference in which layers were adapted. Such a run cannot distinguish DSS-based selection from the Late heuristic.

**This was not solved by changing DSS.** Per instruction, only *already-authorized* options in the existing frozen design were considered:

1. **The Top-K sweep across K values** (§T item 6, already a frozen required ablation — not yet executed against real training). Different K values are not guaranteed to produce Late-identical sets; whether they do is unknown until the sweep is run. This is not a new K being invented here — it is an already-planned activity.
2. **Threshold-based selection instead of fixed Top-K** (§G explicitly authorizes threshold selection as a candidate alongside Top-K, "compared empirically" — not yet exercised). A threshold cutoff could select a different-sized or different-composition set than a hard top-6 count, depending on where the actual normalized-DSS values fall.
3. **The formally-locked, final (non-illustrative) DSS computation**, run under the proper validation-only protocol on the eventual real split (Section 7), rather than Phase 2A's exploratory probes. This could, in principle, produce a different ranking than Probe A's illustrative one — Phase 2A itself already showed the *ranking* is stable across its three probes, but all three probes tested only crop location and file selection at a fixed K=6, not the effect of a properly-locked split or a different K/threshold.

**None of these are predicted to resolve the identifiability collision — they are simply the paths the existing frozen design already authorizes for testing whether it does.** No claim is made that any of them will produce a different result from Late.

**Precise conclusion:** at the specific configuration examined (K=6, cosine, fixed Top-K, Probe A), DSSA and Late are experimentally non-identifiable. This has not been shown to hold at other K values, under threshold-based selection, or under the formally-locked final split — those remain open, already-authorized, not-yet-executed avenues. This is reported as an experimental-design fact, not a failure of the method.

## 13. Blockers / Unresolved Decisions

**BLOCKER: none found.** Nothing in the current frozen design conflicts with anything else, and nothing already-decided contradicts anything else already-decided.

**UNSPECIFIED — REQUIRES DECISION (consolidated):**

1. Formal, file-level 60/15/25 Vaihingen split manifest (Section 7) — must exist and be locked before any real (non-illustrative) DSS computation is used to govern actual training.
2. Whether Condition I (MMD-selected layers) is an authorized full training condition for the first Phase 2B run, or deferred (Section 11).
3. Decoder architecture (Section 6) — blocks total trainable-parameter counts and blocks writing any training code, but does not threaten cross-condition fairness once chosen.
4. LoRA A/B initialization scheme and bias convention (Section 6).
5. The entire training protocol table (Section 9) — optimizer, LR, schedule, epochs, batch size, loss, augmentation, etc. — as one shared protocol, not per-condition.
6. Training-time seed policy (weight init, data ordering) — distinct from the already-deterministic selection-stage seeds (Section 8).
7. Evaluation tiling/aggregation procedure for full-resolution inference (Section 10) — the 224×224 sanity-check crop procedure is not the same thing as final-evaluation inference and has not been designed.
8. Empirical (not just designed) verification that repeated runs on MPS reproduce identical DSS numbers — not tested in this session (Section 8).

## 14. Exact Authorization Needed Before Training

Two categories, kept separate:

**Decisions someone must make** (items 1–7 above) — none of these can be inferred or defaulted without a choice being made by the team; inventing values here was explicitly out of scope for this audit.

**A specific design question someone must resolve, not just an omission:** given DSSA@K=6 == Late@K=6 (Section 12), should the first Phase 2B training run (a) proceed anyway, explicitly reporting this identifiability limitation and treating the eventual comparison as uninformative at this K; (b) wait for the Top-K sweep or threshold-based selection to find a K where the two conditions diverge before training either; or (c) something else? This audit does not recommend an answer — it surfaces that the question exists and must be decided before training is authorized.

## 15. Final Pre-Flight Status

**UNSPECIFIED — REQUIRES DECISION**, overall, driven by items 1–8 in Section 13. No BLOCKER exists against the frozen methodology itself — everything that is frozen remains internally consistent and was not touched. Phase 2B is **not yet implementation-ready** for training, specifically because the training protocol (Section 9) and the split manifest (Section 7) do not yet exist, and because the DSSA-vs-Late identifiability question (Section 12) has not been given a design answer by the team.

**Stopping here, per instruction. No training, no code for training, and no further phase is begun.**
