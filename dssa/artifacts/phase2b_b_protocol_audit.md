# Phase 2B-B Protocol Audit

Cross-references `DSSA_PHASE2B_B_TRAINING_PROTOCOL_FREEZE.md` and `dssa/config/phase2b_training_protocol.json` against the project's prior frozen/historical documents. None of the five documents below were modified by this audit or by this phase.

Documents audited: `DSSA_PROJECT_FREEZE.md`, `DSSA_IMPLEMENTATION_FREEZE.md`, `DSSA_RED_TEAM_REPORT.md`, `dssa/reports/DSSA_PHASE2B_PREFLIGHT_REPORT.md`, `dssa/reports/DSSA_PHASE2B_A_FINAL_SPLIT_KSWEEP_REPORT.md`.

## 1. Preserved Frozen Decisions (unchanged this phase)

| Decision | Source document | Preserved as |
|---|---|---|
| Backbone = Prithvi-EO-2.0-300M, revision `9eb1b1102806593963daa333bcc491b1c6f8562f` | `DSSA_PROJECT_FREEZE.md` §W | Referenced verbatim in `phase2b_training_protocol.json.meta` |
| Dataset pair = ISPRS Potsdam IRRG → ISPRS Vaihingen IRRG | `DSSA_PROJECT_FREEZE.md` §P-1 | Unchanged; no alternate dataset considered |
| Strategy C source-fit-only radiometric transform | `DSSA_PREIMPLEMENTATION_CALIBRATION.md` | Referenced as-is (`radiometric_transform.json`), not refit |
| Band mapping (Green/Red/NarrowNIR populated; Blue/SWIR1/SWIR2 zero-filled) | `DSSA_PRITHVI_COMPATIBILITY_AUDIT.md` | Unchanged |
| `num_frames=1` | `DSSA_PREIMPLEMENTATION_CALIBRATION.md` | Unchanged |
| DSS definition (cosine distance, bootstrap-normalized against source-vs-source null) | `DSSA_PROJECT_FREEZE.md` §O-A–J | Unchanged; reused via `run_phase2a_dss.py` imports |
| CKA deferred/excluded | `DSSA_PROJECT_FREEZE.md` Decision 1 | Unchanged; not reintroduced |
| Random-K baseline, source-vs-source null baseline | `DSSA_PROJECT_FREEZE.md` Decisions 2–3 | Unchanged; extended with 3 pre-registered seeds this phase |
| Formal Vaihingen split (20/5/8, lexicographic, target-probe=5) | `dssa/reports/DSSA_PHASE2B_A_FINAL_SPLIT_KSWEEP_REPORT.md` | Unchanged; loaded read-only via manifest |
| K-sweep grid {2,4,6,8,12} | `dssa/reports/DSSA_PHASE2B_A_FINAL_SPLIT_KSWEEP_REPORT.md` | Unchanged |
| Final DSS ranking (24 layers) | `dssa/artifacts/dss/phase2b_final_dss_results.json` | Unchanged; consumed read-only |
| LoRA rank = 8, target = "Q and V only" | `DSSA_PROJECT_FREEZE.md` §O-H | Rank preserved exactly; "Q and V only" resolved to slice-based application (see §2) because the intended separate-matrix reading does not match the actual fused-qkv module |

## 2. New Phase 2B-B Decisions

| Decision | Why it was needed | Documented in |
|---|---|---|
| Decoder architecture (4-block conv upsample, final-layer-only input) | No decoder existed anywhere in the codebase; abstract requires segmentation output | Freeze §Step 2 |
| LoRA Q/V-slice resolution for fused `qkv` | Direct source inspection showed `timm`'s `Attention` has no separate W_q/W_k/W_v; the frozen freeze text's literal reading was inapplicable to the real module | Freeze §Step 3 — flagged explicitly as new, not backdated into the original freeze |
| LoRA alpha/dropout/init values | Not specified in any prior document | Freeze §Step 3 |
| Full training hyperparameters (optimizer, LR, schedule, steps, batch size, precision, clipping, checkpointing) | Not specified in any prior document | Freeze §Step 7 |
| Loss function (CE+Dice, unweighted) | Required real class-imbalance measurement, which had never been performed | Freeze §Step 8, grounded in `target_train_class_distribution.json` |
| Training seed (1000) and its single-seed-per-condition policy | Not previously specified; policy limitation explicitly disclosed | Freeze §Step 9 |
| Evaluation protocol (tiling stride, overlap aggregation, metrics) | Not previously specified | Freeze §Step 10 |
| Collision-handling rule (train once, dual-label report) | Required once the K=8 DSSA=Late collision (already known) and two further collisions (newly found) needed a uniform, pre-registered treatment | Freeze §Step 5 |
| K-selection-for-later policy | Needed to pre-commit against any post-hoc "pick the best K" temptation | Freeze §Step 13 |
| No-Post-Hoc-Changes list | Explicit instruction this phase; had not previously existed as a single enumerated list | Freeze §Step 16 |

## 3. Unresolved Items

None found to be essential-and-blocking for the next phase. All 18 requested steps produced a concrete, frozen answer. The single acknowledged **limitation** (not an unresolved blocker) is single-seed training per non-Random-K condition (Freeze §Step 9), which was disclosed rather than silently assumed acceptable.

## 4. Potential Methodological Risks (disclosed, not hidden)

- **Single training seed per condition** (except Random-K's 3 layer-selection seeds) means point estimates, not variance estimates, for DSSA/Early/Middle/Late/Lowest-DSS — a result difference of a few mIoU points between conditions cannot be distinguished from training-run noise with this design alone.
- **MPS gradient-path determinism is unverified** — unlike the already-verified no_grad() DSS forward pass, repeated identical training runs on this hardware/framine combination have not been shown to reproduce bit-exact numbers.
- **Three architectural collisions** (not one) mean 3 of the 8 named conditions do not yield an independent data point at every K — this reduces the effective comparative power of the design at K=6 and K=8 specifically, and is now stated plainly rather than glossed over.
- **20-file target-train pool** is small for a 2000-step training budget; overfitting risk exists and is only partially mitigated by geometric augmentation — no claim of adequacy is made here.
- Freeze document deliberately does **not** claim these risks are resolved — they are accepted, disclosed limitations of the chosen design.

## 5. Conditions That Will Be Trained Later (exact list)

Per Freeze §Step 4–5: 8 named condition types (DSSA, Early, Middle, Late, Lowest-DSS, Random-K×3 seeds, K=0, K=all) across K∈{2,4,6,8,12} where applicable = 42 condition-slots, reduced to **39 unique training runs** after merging the 3 identified architectural collisions (K=6 Early=Lowest-DSS; K=8 DSSA=Late; K=8 Early=Lowest-DSS). No run has been executed; this is the pre-registered target list for Phase 2C only.

---

This audit confirms: no prior frozen document was altered, every new decision this phase is traceable to a specific unresolved gap, and no experimental condition, dataset, checkpoint, or DSS mechanism was silently changed.
