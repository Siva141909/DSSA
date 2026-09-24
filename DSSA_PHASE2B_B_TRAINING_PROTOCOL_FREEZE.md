# DSSA Phase 2B-B — Training & Evaluation Protocol Freeze

**No training executed. No optimizer instantiated. No gradients computed. No LoRA training. No segmentation training. No target-validation or target-test labels accessed for selection. This document, `dssa/config/phase2b_training_protocol.json`, and `dssa/artifacts/phase2b_b_protocol_audit.md` are documentation/configuration artifacts only.**

**Final status: PHASE 2B-B COMPLETE — TRAINING NOT AUTHORIZED.**

---

## A. Concise Completion Summary

Every methodological decision needed to run Phase 2C (training) without post-hoc scientific judgment calls has been resolved and frozen, with one exception noted explicitly (§L). Along the way, this phase discovered and resolved two genuine implementation facts that were not yet known when earlier phases used the phrase "W_q/W_v only": (1) the actual attention module uses a single fused `qkv` matrix, not separate Q/K/V projections, requiring a documented, standard resolution (§Step 3 below); (2) three additional layer-set collisions exist beyond the already-known K=8 DSSA/Late one (K=6 Early=LowestDSS; K=8 Early=LowestDSS), found by systematically checking all pairs at every swept K rather than only the one already flagged. A real, verified class-imbalance measurement (from target-train labels only) grounds the loss-function choice. 39 unique training runs are required (42 condition-slots minus 3 architecturally-identical duplicates).

---

## Step 1 — Codebase Inspection

Directly inspected `dssa/` (excluding data/checkpoint/venv):

| Component | Found? | Detail |
|---|---|---|
| Segmentation model code | **No** | Only `dssa/sanity/model.py`, which loads the bare `PrithviViT` encoder — no decoder head anywhere |
| Decoder code | **No** | Absent — must be defined (Step 2) |
| Dataset/tile loading code | Partial | `preprocessing.py` handles Strategy C + input construction for DSS crops only; no training-time DataLoader, no label loading, exists |
| Crop/tiling utilities | Partial | Only fixed single-crop extraction (`load_irrg_crop_at`) for DSS purposes; no sliding-window/overlap tiling utility exists |
| Checkpoint loading code | Yes | `model.py`'s `load_frozen_encoder()` |
| LoRA-related code | **No** | Absent anywhere in the repository |
| Config files | Yes | `dssa/configs/sanity_config.yaml` (sanity phase only); `dssa/config/` (new, Step 17) did not exist before this phase |
| Dependency/environment file | Partial | `dssa/checkpoint/requirements.txt` (the checkpoint repo's own, minimal); the actual working `venv` was built ad hoc in Phase 1B, not captured in a project-level lockfile |
| Prior segmentation experiments | **No** | None — this project has never run a forward pass through a decoder or computed a segmentation metric |
| Loss implementations | **No** | Absent |
| Evaluation utilities | **No** | Absent — `diagnostics.py`'s checks are sanity checks (finiteness, variance, block coverage), not segmentation metrics |

**No decoder exists. One is proposed below, as a single architecture, not a menu.**

## Step 2 — Segmentation Architecture (Frozen This Phase)

- **Feature source:** the **final transformer layer only** (index 23, after the model's closing LayerNorm), cls token excluded, reshaped from `(B, num_patches, 1024)` to `(B, 1024, H/16, W/16)`. **Deliberate, stated reason:** using a single, fixed feature source decouples "what the decoder sees" from "which layers receive LoRA" — the actual experimental variable. Using multiple or K-dependent backbone layers as decoder input would confound the two questions this project exists to separate.
- **Decoder:** a 4-block progressive-upsampling convolutional head (each block: 3×3 conv, GroupNorm, ReLU, 2× bilinear upsample — total 16× upsample, matching patch size 16), followed by a 1×1 conv to 6 output classes (raw logits, no final activation — softmax is applied inside the loss/metrics, not the model). Channel widths: 1024→256→128→64→64→6.
- **Classes (6), verified empirically this phase** by reading actual ISPRS Vaihingen ground-truth pixels (not assumed): `impervious_surfaces` (white), `building` (blue), `low_vegetation` (cyan), `tree` (green), `car` (yellow), `clutter_background` (red). Zero unmapped pixels found across all 20 target-train label files.
- **Parameters:** 2,766,726, computed exactly (§F). Bias present on every conv. Initialization: PyTorch framework defaults (Kaiming-uniform for conv weights) — not a special scheme.
- **Identical across every experimental condition, including K=0.**

## Step 3 — LoRA Specification (Frozen This Phase, With One Genuine Architectural Finding)

**Finding, verified by direct source inspection of `timm.models.vision_transformer.Attention`** (the module Prithvi's `Block` uses): there is **no separate `W_q`/`W_k`/`W_v`** — attention uses one fused `self.qkv = nn.Linear(1024, 3072, bias=qkv_bias)`, producing concatenated [Q;K;V].

**Resolution (new Phase 2B-B decision, not read back into the original freeze):** LoRA rank 8 is applied to the **Q-slice** (output rows 0:1024) and **V-slice** (rows 2048:3072) of this fused matrix's output space; the K-slice (rows 1024:2048) receives no LoRA contribution. This is mathematically identical to separate-matrix W_q/W_v-only LoRA and is a standard, well-precedented technique for fused-qkv architectures (not invented for this project) — the original weight tensor is never modified in place; LoRA adds a parallel low-rank delta only to the relevant output slices.

| Item | Value |
|---|---|
| Rank | 8 (unchanged) |
| Targeted | Q-slice, V-slice of fused `qkv` (K-slice and output `proj` untouched, MLP untouched) |
| Alpha | 16 (= 2×rank, standard convention; effective scale α/r = 2.0) |
| Dropout | 0.0 (dataset already small; no added stochastic regularization) |
| A initialization | Kaiming-uniform (standard LoRA convention) |
| B initialization | zeros (guarantees the adapted model starts identical to the frozen backbone) |
| Original `qkv` weight/bias | frozen, untouched |
| Trainable params per selected block | **32,768** (verified by exact arithmetic, §F) |

## Step 4 — Experimental Conditions

| Condition | K values | Runs |
|---|---|---|
| K=0 (decoder-only) | — | 1 |
| DSSA | 2,4,6,8,12 | 5 |
| Early | 2,4,6,8,12 | 5 |
| Middle | 2,4,6,8,12 | 5 |
| Late | 2,4,6,8,12 | 5 |
| Lowest-DSS | 2,4,6,8,12 | 5 |
| Random-K (3 seeds: 101, 202, 303) | 2,4,6,8,12 | 15 |
| K=24/all | — | 1 |
| **Total condition-slots** | | **42** |
| **Deduplicated (§Step 5)** | | **−3** |
| **Unique training runs** | | **39** |

**Random-K seed count justification:** 3 — the minimum that yields a non-degenerate mean±std (n=2 gives an unstable variance estimate), kept minimal given the Kaggle/Colab-scale compute budget stated in the project's own original abstract. This is stated as a real limitation on statistical power, not papered over. Seeds `[101, 202, 303]` are arbitrary, fixed now, and were never generated from or tuned against any performance signal.

## Step 5 — Collision Handling (K=8 DSSA/Late, and Two More Found)

Systematically checked **every pairwise combination** of {DSSA, Early, Middle, Late, Lowest-DSS} at every swept K (pure set comparison on the already-frozen Phase 2B-A ranking — no new DSS computation). Result: **three** exact-identity collisions, not one:

| K | Colliding conditions | Shared layers |
|---|---|---|
| 6 | Early = Lowest-DSS | `{0,1,2,3,4,5}` |
| 8 | DSSA = Late | `{16,17,18,19,20,21,22,23}` |
| 8 | Early = Lowest-DSS | `{0,1,2,3,4,5,6,7}` |

**Treatment (identical principle applied to all three, uniformly):** where two named conditions select the exact same layer set, they are trained **once** — training both would produce a run differing only by whatever residual training-time randomness exists (data shuffling order, etc.), not by architecture, and would waste compute reproducing an architecturally identical model under a second label. The single resulting run's metrics are reported under **both** condition labels in every results table, with an explicit annotation (e.g., "DSSA@K=8 and Late@K=8 are the same trained run — architecturally identical layer sets") wherever they appear. **No difference between the two labels' numbers may be interpreted as evidence of selection-method superiority** — there is no difference to interpret; they are the same run. This treatment does not remove any condition from the design (all labels are retained in the reporting structure) and does not alter DSS to force a different selection.

## Step 6 — Data-Role Freeze and the Leakage Question

| Split | Count | Permitted use |
|---|---|---|
| Source (Potsdam) | per frozen mechanism | Unchanged from Phase 1B/2A/2B-A |
| target-train | 20 | Supervised adaptation/training (labels used) |
| target-probe | 5 (⊆ target-train) | Unsupervised DSS selection **only** (already executed, frozen — Phase 2B-A) |
| target-validation | 5 | Labels used **only** for checkpoint/model selection |
| target-test | 8 | Completely untouched until one final, locked evaluation pass |

**Does target-probe's later, labeled use in supervised training constitute leakage? No — reasoned explicitly, not asserted:**

The frozen leakage policy exists to prevent **label information from influencing the layer-selection decision**. The DSS computation that produced the frozen K-sweep results (Phase 2B-A) used the 5 target-probe files in a strictly **unlabeled** capacity — confirmed by code inspection at every prior phase (no label path ever opened during DSS computation). That decision is now fixed and will not be revisited based on anything learned during training. The same 5 files subsequently participating in supervised training, using their labels, is **the same role every other target-train file plays** — there is no asymmetry and no information flow from "probe" back into "selection." The only discipline this requires going forward: **layer selection must not be recomputed or adjusted after training begins** — doing so would reintroduce exactly the leakage this reasoning currently rules out. This is enforced by §Step 16's No Post-Hoc Changes list (K grid and baseline definitions are on it).

## Step 7 — Training Protocol (Frozen)

Full machine-readable values in `dssa/config/phase2b_training_protocol.json`. Summary:

| Item | Value | Rationale |
|---|---|---|
| Optimizer | AdamW (β=0.9/0.999, weight decay 0.01) | Standard for both LoRA and from-scratch conv decoder training |
| Learning rate | 1e-3, single shared param group | Avoids a second LR-ratio hyperparameter as an extra forking-path risk |
| Scheduler | Cosine decay to 0, 100-step warmup | Standard, simple, not tuned |
| Total steps | 2,000 | Fixed budget appropriate to a 20-image target-train pool with per-step random cropping |
| Batch size | 8 | Fits comfortably in 16GB unified memory at 224×224 |
| Precision | fp32 | MPS mixed-precision determinism is less mature than CUDA's; fp32 chosen for reliability on this specific hardware, not as a blanket policy |
| Gradient clipping | max-norm 1.0 | Standard practice |
| Checkpoint frequency | every 200 steps | — |
| Best-checkpoint rule | highest mean IoU on target-validation | Pre-registered now, not chosen after seeing results |
| Early stopping | None (fixed budget; best checkpoint kept regardless of when it occurred) | Avoids an early-stopping-criterion tuning decision |

**If any hyperparameter above ever needed tuning, the mechanism is:** target-validation only, via the same best-checkpoint-by-mIoU rule — never target-test, never test results. No tuning was performed in this phase (nothing has been trained).

## Step 8 — Class Imbalance and Loss (Frozen, Grounded in Real Measurement)

**Real class distribution measured this phase, from target-train labels only** (20 files, `ISPRS_semantic_labeling_Vaihingen_ground_truth_COMPLETE.zip`, opened read-only — target-validation and target-test labels were **not** opened):

| Class | Pixels | % |
|---|---|---|
| tree | 26,763,260 | 26.109% |
| impervious_surfaces | 26,252,732 | 25.611% |
| low_vegetation | 23,876,011 | 23.293% |
| building | 23,703,019 | 23.124% |
| **car** | **1,036,170** | **1.011%** |
| **clutter_background** | **873,507** | **0.852%** |

**Classes are confirmed not balanced** — a ~30:1 ratio between the most and least common classes. **Primary loss: unweighted Cross-Entropy + Dice (1:1 sum), no class weights.** Rationale: Dice loss is inherently robust to class imbalance (set-overlap based, not frequency-based); combining it with CE gives stable pixel-wise gradients without introducing a separately-tuned class-weight hyperparameter as a hidden free parameter. This is chosen as the single primary loss — no post-hoc loss changes are permitted (§Step 16).

## Step 9 — Seeds and Repeatability

| Seed | Value |
|---|---|
| Python `random` (training) | 1000 |
| NumPy (training) | 1000 |
| PyTorch (training) | 1000 |
| Random-K layer-selection seeds | 101, 202, 303 (pre-registered, §Step 4) |

**Policy:** one fixed training seed (1000) per condition — **not** multiple independent training seeds per condition. This is recorded explicitly as a **limitation**: single-seed training results establish a point estimate, not statistical robustness against training-time variance, for any condition except Random-K (which gets its robustness from 3 independent *layer-selection* seeds, each still trained once). **MPS determinism under active gradient computation, dropout, and data shuffling has not been empirically verified** — only the frozen, gradient-free DSS forward pass was verified bit-exact (Phase 2B-A). This gap is stated, not assumed away.

## Step 10 — Evaluation Protocol (Frozen)

- **Metrics:** mean IoU, per-class IoU, macro F1, pixel accuracy — no additional metric introduced.
- **Inference tiling:** sliding window, 224×224, stride 112 (50% overlap), reflect-padded at borders; overlapping logits averaged before argmax (not majority vote).
- **Validation use:** every 200 steps, for checkpoint selection only.
- **Test use:** exactly once per condition, only after that condition's training is complete and its best validation checkpoint is fixed. **Target-test evaluation does not occur in this phase and is not authorized by this document.**

## Step 11 — Efficiency Metrics (Plan Only, Nothing Measured Yet)

Planned measurements: total parameters, trainable parameters, trainable-parameter percentage, LoRA parameters, decoder parameters, peak training memory, training wall-clock time. **Explicit policy:** trainable-parameter reductions will not be presented as implying proportional FLOPs or wall-clock savings unless both are actually measured — the frozen backbone still runs its full forward pass regardless of how many layers carry LoRA. Hardware to report: Apple M5, 16GB unified memory, MPS, PyTorch 2.14.0.

## Step 12 — Statistical / Reporting Plan

Per condition: mean IoU, per-class IoU, F1, pixel accuracy, trainable parameter count, efficiency measurements. For Random-K only: mean ± std across its 3 seeds. **No single "DSSA score" or homemade aggregate metric will be created. No method will be declared "best." No threshold is defined in advance for declaring a difference meaningful** — the eventual write-up reports the actual measured numbers and discusses the differences observed, nothing more.

## Step 13 — K Selection Policy

DSS itself is unsupervised and already frozen (Phase 2B-A). K is **not** selected now, and not selected by intuition, DSS magnitude, overlap with Late, or the K=8 collision. **Rule, frozen now:** all five K values in {2,4,6,8,12} are trained and reported; if a "final DSSA configuration" is ever needed for a downstream purpose, it is chosen by target-validation mIoU among the five trained DSSA conditions — never target-test. Reporting all five K values, with no single universal winner declared, remains an entirely acceptable, valid outcome.

## Step 14 — Random-K Fairness

Random-K uses exactly K layers, rank 8, Q/V-slice LoRA, the same decoder, the same training protocol, the same target-train data, and the same validation/test protocol as every other condition (§Step 4 table; parameter counts match exactly at each K, §F). Seeds `[101, 202, 303]` are predefined (§Step 9) and were not generated after observing any DSSA result.

## Step 15 — MMD

**"MMD remains a representation-level metric ablation and is not a full adaptation condition."** No governing document requires it as a training baseline; none was added. The Phase 2A MMD ranking (Top-6 `[5,4,11,6,19,3]` on Probe A) remains historical only.

## Step 16 — No Post-Hoc Changes

After this protocol is frozen, the following may **not** be changed because of observed segmentation results: decoder architecture; LoRA rank; LoRA target-module convention (Q/V-slice); LoRA initialization; optimizer; learning rate; scheduler; loss function; augmentation; total step count; every seed (training: 1000; Random-K: 101/202/303); the K grid; baseline/control definitions; the target-test protocol; the evaluation metrics. **If a genuine implementation bug is found, it is fixed transparently and the affected conditions are rerun — never silently reinterpreted as an improvement.**

## Step 17 — Implementation Artifacts (This Phase)

Documentation/configuration only — no training script that could accidentally start training was created.

1. `DSSA_PHASE2B_B_TRAINING_PROTOCOL_FREEZE.md` — this document.
2. `dssa/config/phase2b_training_protocol.json` — full machine-readable protocol (new `config/` directory created this phase, distinct from the existing `configs/` used for the sanity phase).
3. `dssa/artifacts/phase2b_b_protocol_audit.md` — audit against every prior frozen/historical document.
4. `dssa/artifacts/target_train_class_distribution.json` — the real, measured class-pixel counts (§Step 8), computed from target-train labels only.

## Step 18 — Final Audit

See `dssa/artifacts/phase2b_b_protocol_audit.md` for the full, itemized audit against `DSSA_PROJECT_FREEZE.md`, `DSSA_IMPLEMENTATION_FREEZE.md`, `DSSA_RED_TEAM_REPORT.md`, `DSSA_PHASE2B_PREFLIGHT_REPORT.md`, and `DSSA_PHASE2B_A_FINAL_SPLIT_KSWEEP_REPORT.md`. None of those documents were modified.

---

## Final Required Output

**A.** See above.

**B. Decision Table**

| Decision | Status | Frozen/New | Exact value | Rationale |
|---|---|---|---|---|
| Backbone | VERIFIED | Frozen (prior) | Prithvi-EO-2.0-300M, rev `9eb1b11...` | — |
| Decoder feature source | VERIFIED | **New** | Final layer (23) only | Decouples features from LoRA variable |
| Decoder architecture | VERIFIED | **New** | 4-block conv upsample, 2.77M params | Simple, identical across conditions |
| Num classes | VERIFIED | **New** (measured) | 6, verified from real labels | — |
| LoRA rank/modules | VERIFIED | Frozen (prior), **resolution new** | r=8, Q/V-slice of fused qkv | Fused-qkv finding required a documented resolution |
| LoRA alpha/dropout/init | VERIFIED | **New** | α=16, dropout=0, B=zeros | Standard LoRA convention |
| K grid | VERIFIED | Frozen (Phase 2B-A) | {2,4,6,8,12} | — |
| Conditions | VERIFIED | **New** | 8 condition types, 42 slots, 39 unique runs | Minimum necessary matrix |
| Collisions | VERIFIED | **New (discovered this phase)** | 3 total (K6 Early=Lowest; K8 DSSA=Late; K8 Early=Lowest) | Train once, dual-label report |
| Random-K seeds | VERIFIED | **New** | 3 seeds: 101,202,303 | Minimum for mean±std |
| Data roles | VERIFIED | Frozen (prior), reasoning **new** | train=20/probe=5/val=5/test=8 | No leakage, reasoned explicitly |
| Loss | VERIFIED | **New (measured)** | CE+Dice, unweighted | Real imbalance measured (30:1) |
| Optimizer/LR/schedule | VERIFIED | **New** | AdamW, 1e-3, cosine, 2000 steps | See §Step 7 |
| Seeds (training) | VERIFIED | **New** | 1000 (single seed) | Limitation, stated |
| Evaluation protocol | VERIFIED | **New** | mIoU/IoU/F1/acc, sliding-window tiling | — |
| MMD as training condition | VERIFIED | **New** | Not included | Remains ablation-only |

**C. Experiment Matrix:** 42 condition-slots → 39 unique training runs (§Step 4–5).

**D. Validation/Model-Selection Procedure:** every 200 steps, highest mIoU on the 5-file target-validation split selects the checkpoint kept per run.

**E. Final-Test Procedure:** one evaluation pass per condition's selected checkpoint, on the 8-file target-test split, only after that condition's training and checkpoint selection are complete — not performed in this phase.

**F. Parameter-Count Accounting:** decoder = 2,766,726 (fixed). LoRA = 32,768 × K. K=0: 2,766,726 total. K=2: 2,832,262. K=4: 2,897,798. K=6: 2,963,334. K=8: 3,028,870. K=12: 3,159,942. K=24: 3,553,158. Backbone (frozen, not counted as trainable): 303,886,336.

**G. Efficiency-Measurement Plan:** §Step 11 — parameters, memory, wall-clock time to be measured; no FLOPs/speed claim without direct measurement.

**H. Leakage/Data-Role Audit:** §Step 6 — no leakage found; target-probe's later supervised role reasoned through explicitly, not asserted.

**I. K=8 Collision Treatment:** §Step 5 — train once, report under both labels, no superiority inference permitted.

**J. Random-K Treatment:** §Step 14 — fully matched to every other condition on architecture and protocol; 3 pre-registered seeds.

**K. MMD Treatment:** §Step 15 — ablation-only, not a training condition.

**L. Remaining Unresolved Decisions:** **None found to be essential-and-unresolvable.** Every decision this phase was scoped to make was made and is recorded above. (Items already known and out of this phase's scope — e.g., whether a "final DSSA configuration" is ever formally declared post-training — remain open by design, per §Step 13, not by omission.)

**M. Files Created:**
- `DSSA_PHASE2B_B_TRAINING_PROTOCOL_FREEZE.md`
- `dssa/config/phase2b_training_protocol.json`
- `dssa/artifacts/phase2b_b_protocol_audit.md`
- `dssa/artifacts/target_train_class_distribution.json`

---

## PHASE 2B-B COMPLETE — TRAINING NOT AUTHORIZED.
