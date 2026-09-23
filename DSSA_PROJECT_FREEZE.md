# DSSA Project Freeze

**Status: NOT READY TO FREEZE.** See Section N. This document freezes everything that safely can be frozen without pre-judging the three open decisions raised in `DSSA_ABSTRACT_GAP_ANALYSIS.md`, and names exactly what cannot be frozen yet.

Companion document: `DSSA_ABSTRACT_GAP_ANALYSIS.md` (16 gaps, 3 critical decision flags — read that first for the reasoning behind every line here).

---

## A. Frozen Research Question

> Can layer-wise representation drift, measured from a frozen geospatial foundation model using only unlabeled target-domain images, identify which transformer layers are worth adapting — such that inserting LoRA only into those layers produces target-domain segmentation accuracy competitive with full fine-tuning or uniform LoRA, using substantially fewer trainable parameters?

## B. Frozen Hypothesis

> Transformer layers in a pretrained geospatial foundation model are not equally affected by domain shift. A layer-wise Domain Sensitivity Score (DSS), computed from unlabeled source and target representations before any adaptation, can identify a small subset of layers such that adapting only that subset (via LoRA) yields segmentation performance competitive with adapting all layers (uniform LoRA) or the full model (full fine-tuning), while using substantially fewer trainable parameters.

This is falsifiable: it fails if DSS-selected layers perform no better than randomly-selected layers of the same count, or if the accuracy gap versus full fine-tuning/uniform LoRA is not "competitive" by a pre-agreed margin.

## C. Frozen Scope

DSSA will investigate:
- Whether label-free, layer-wise representation drift is a usable signal for selecting adaptation targets in a geospatial foundation model.
- Whether selective LoRA guided by that signal is competitive with full fine-tuning and uniform LoRA on segmentation accuracy.
- Whether such selection reduces trainable parameters and optimizer/GPU-memory footprint relative to those baselines.
- How sensitive the result is to the choice of DSS metric, K, and layer-selection strategy (via the required ablations, Section L).

## D. Explicit Non-Goals

DSSA will **not** claim, until specifically evidenced:
- That it is the first or only method to do selective adaptation for remote-sensing segmentation (it is not — see CrossEarth-Gate).
- That the entire adaptation pipeline is label-free (it is not — only the layer-selection step is; LoRA fine-tuning uses labeled target data, per Gap G-11).
- That fewer trainable parameters implies proportionally lower forward-pass compute or proportionally faster wall-clock training (per Gap G-15 — only parameter count and optimizer memory are expected to drop; FLOPs and training time must be measured separately, not assumed).
- That the method generalizes across sensors/regions beyond what is directly tested (cross-domain validation, E10, is required before any such claim).
- Any specific accuracy or efficiency number, until measured.

## E. Frozen Methodology

The 6-stage pipeline, as stated in the abstract (§5), is frozen at this level of description:

1. **Source training** — pretrained foundation model + labeled source segmentation data → source-trained model.
2. **Target analysis** — unlabeled target images through the frozen backbone → layer-wise hidden representations.
3. **DSS computation** — compare source and target feature distributions per layer → Domain Sensitivity Score per layer.
4. **Layer selection** — rank layers by DSS; select Top-K or threshold-selected layers → adaptation mask.
5. **Selective PEFT** — insert LoRA only into selected layers → adapted backbone.
6. **Target segmentation** — adapted backbone + decoder on target imagery → target segmentation maps.

The *exact mathematics* inside stages 3 and 4, and the *exact configuration* of stage 5, are **not** frozen — see Sections F, G, H.

## F. Frozen DSS Definition — PARTIALLY FROZEN

**Frozen (form):**
- DSS is computed **once**, on the frozen (pre-adaptation) backbone.
- DSS is computed **per individual transformer layer**, not per stage or module group.
- DSS requires only labeled source data and **unlabeled** target data.
- DSS must be reported alongside a **source-vs-source null-baseline** value for the same layer, so raw drift can be distinguished from natural layer-to-layer variance (Gap G-5, G-16).
- Candidate metrics under consideration: cosine-distance statistics, MMD. **CKA remains a candidate only pending resolution of 🚨 Flag 1** (its standard form assumes paired samples; our comparison is unpaired).

**NOT frozen (must be decided before implementation):**
- Exact pooling strategy (per-token vs. per-image-pooled representations).
- Exact sample-aggregation strategy (pairwise mean distance vs. centroid distance).
- Exact cross-layer normalization method.
- Final single metric (to be chosen empirically on a validation split, per the abstract's own §6 instruction — this process is frozen, the outcome is not).
- Whether CKA is included at all, and if so, in what adapted form.

## G. Frozen Layer Selection Rule — PARTIALLY FROZEN

**Frozen:**
- Layers ranked by (null-baseline-normalized) DSS, descending.
- Selection by either Top-K (fixed count) or threshold (cutoff value) — both remain candidates, to be compared empirically (already planned as part of E8).
- K = 0 is a legitimate degenerate baseline (backbone fully frozen, decoder-only training), not an error state.
- K ≥ number of layers is clamped to "all layers selected" (equivalent to uniform LoRA), not an error state.
- Selection must be **deterministic** given fixed inputs (same model, same source/target probe batches, same metric, same K) — no randomness in the selection step itself.
- **K and threshold values are chosen only on a held-out validation split — never on the reported test split** (Gap G-13). This is a hard requirement, not a preference.

**NOT frozen:**
- The specific K value(s) to report as primary results.
- Tie-breaking rule for equal DSS scores (must be defined, e.g., stable sort by layer index, before implementation).

## H. Frozen Adaptation Rule — PARTIALLY FROZEN

**Frozen:**
- LoRA is inserted **only** into selected layers; every other backbone layer remains fully frozen.
- The segmentation decoder is **always** trainable, regardless of K (including at K = 0).
- LoRA is a **design choice** for the adaptation mechanism, not a logical consequence of the DSS score itself (Gap G-14) — this must be stated as such in any write-up.

**NOT frozen:**
- LoRA rank (fixed across selected layers, or variable — and if variable, by what rule).
- Which weight matrices within a selected layer receive LoRA (attention projections only, or also MLP).
- Overall trainable-parameter budget policy.

## I. Frozen Baselines — INCLUDES REQUIRED ADDITIONS PENDING APPROVAL

| Baseline | Status |
|---|---|
| Source-only | Frozen (already in abstract, E1) |
| Full fine-tuning | Frozen (already in abstract, E2) |
| Uniform LoRA | Frozen (already in abstract, E3) |
| Adapters | Frozen (already in abstract, §9) |
| Visual Prompt Tuning (if compatible) | Frozen (already in abstract, §9) |
| DSSA (Top-K by DSS) | Frozen (already in abstract, E7) |
| **Random-K layer selection (same K, same parameter budget as DSSA)** | **Recommended addition — requires explicit team sign-off (🚨 Flag 3). Without it, the central hypothesis is not falsifiable even in principle.** |
| **Source-vs-source null baseline (for DSS validity, not accuracy comparison)** | **Recommended addition — requires explicit team sign-off (🚨 Flag 3 / Gap G-16).** |

## J. Frozen Data Split Policy

**Frozen, independent of which dataset pair is finally used (Gap G-12):**

| Split | Contents | Used for |
|---|---|---|
| **target-probe** | Unlabeled target images | DSS computation and layer selection **only**. Never touched by anything requiring labels. |
| **target-train** | Labeled target images | LoRA fine-tuning, once layers are selected. |
| **target-validation** | Labeled target images | Choosing K/threshold and the final DSS metric. **Never the test split.** |
| **target-test** | Labeled target images, held out | Final reported metrics only. Never used for DSS, K selection, or metric selection. |

This split is frozen as a **policy**; it does not require the dataset pair itself to be finalized first (🚨 Flag 2 remains open independently).

## K. Frozen Evaluation Metrics

**Segmentation:** mIoU, per-class IoU, F1 score, pixel accuracy.
**Efficiency (reported as distinct, separate quantities — never bundled, per Gap G-15):** trainable parameter count; optimizer/GPU memory; training wall-clock time; inference latency/throughput.
**Robustness / analysis:** performance under whichever shift types the finalized dataset pair actually supports (not assumed in advance — depends on 🚨 Flag 2 resolution); qualitative prediction maps; failure-case review.

## L. Required Ablations

1. Source-vs-source null baseline (must run first — cheapest validity check of DSS itself).
2. Random-K layer selection, matched K.
3. Lowest-DSS layer selection (adapt the *least* sensitive layers).
4. Early / middle / late fixed-position layer selection (already E4–E6).
5. DSS metric ablation: cosine vs. MMD vs. (CKA, pending Flag 1 resolution) — already E9.
6. Top-K sweep, chosen on validation only — already E8.
7. Different target-probe sample sizes (stability check).
8. Different random seeds.
9. Cross-domain validation on a second, different domain shift — already E10.
10. Full efficiency measurement (parameters, memory, time) across every baseline above — already E11.

## M. Known Risks (Intentional Open Experimental Questions)

These are not defects — they are exactly what the project exists to find out:

- Representation drift may not correlate with task-relevant (loss-sensitive) importance (Section 3 of the gap analysis, weakest link in the reasoning chain).
- DSS may reduce to detecting general layer variance rather than domain-specific sensitivity (addressed by the null baseline, but the *outcome* of that check is unknown).
- DSS-selected layers may perform no better than randomly-selected layers of the same count (addressed by the random-K control, outcome unknown).
- Efficiency gains may be limited to parameter count / optimizer memory, not FLOPs or wall-clock time (must be measured, not assumed).
- The chosen dataset pair may not isolate a clean "cross-sensor" shift (🚨 Flag 2).

## N. Decisions Still Requiring Human Approval

Only genuine unresolved decisions — nothing here has been decided on the team's behalf:

1. 🚨 **DSS mathematical form, specifically CKA's validity for unpaired samples** — drop it, adapt it, or defer it (Flag 1).
2. 🚨 **Dataset pair verification** — confirm LoveDA → DeepGlobe against the abstract's own compatibility rule (bands, resolution, labels, licensing), or restrict initial scope to a cleaner same-sensor pair with cross-sensor validation added later (Flag 2). **No new dataset has been chosen — this is explicitly left open.**
3. 🚨 **Approve adding random-K and source-vs-source-null as required baselines** (Flag 3) — recommended, not yet approved.
4. DSS pooling/aggregation/normalization specifics (Section F, "not frozen" items).
5. LoRA rank policy and which weight matrices receive LoRA (Section H, "not frozen" items).
6. Band-alignment strategy, if the finalized dataset pair has mismatched bands (depends on decision 2).
7. Whether a two-paper novelty comparison (SPECTRA, CrossEarth-Gate) is sufficient to proceed, or whether a broader/refreshed literature search is required before any public novelty claim (Gap G-9) — not blocking for freezing the *research question*, but blocking for any future paper/publication claim.

---

**This project will remain NOT READY TO FREEZE until items 1–3 above receive explicit team decisions.** Items 4–7 should be resolved before implementation begins, but do not change the shape of the research question itself. No implementation should begin until this document is reviewed and updated to reflect those decisions.
