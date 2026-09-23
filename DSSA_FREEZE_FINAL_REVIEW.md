# DSSA Freeze — Final Review

Consolidated statement of record. Full reasoning lives in `DSSA_ABSTRACT_GAP_ANALYSIS.md` and `DSSA_PROJECT_FREEZE.md`; this document is the short version.

## 1. Frozen Research Question

> Can layer-wise representation drift, measured from a frozen geospatial foundation model using only unlabeled target-domain images, identify which transformer layers are worth adapting — such that inserting LoRA only into those layers produces target-domain segmentation accuracy competitive with full fine-tuning or uniform LoRA, using substantially fewer trainable parameters?

## 2. Frozen Hypothesis

> Transformer layers are not equally affected by domain shift. A layer-wise Domain Sensitivity Score (DSS), computed once, before adaptation, from unlabeled source/target representations, can identify a subset of layers such that adapting only that subset (via LoRA) is competitive with adapting all layers or the full model, at substantially lower trainable-parameter cost. **Falsifiable:** fails if DSS-selected layers perform no better than a random subset of the same size.

## 3. Frozen DSS Definition

- Computed once, per individual transformer layer, on the frozen backbone, from labeled source + **unlabeled** target data only.
- Candidate metrics: **cosine distance and MMD.** CKA deferred (not implemented; no unpaired variant invented).
- Pooling: mean over spatial tokens, per image, per layer.
- Aggregation: mean of per-target-image distances to a single source centroid.
- Normalization: z-scored against a source-vs-source null-baseline distribution (bootstrap-estimated), per layer, before ranking.
- Exact cosine formula fixed (see `DSSA_PROJECT_FREEZE.md` §O-D).

## 4. Frozen Layer-Selection Rule

- Rank layers by normalized DSS, descending. Top-K or threshold, compared empirically.
- K = 0 → decoder-only baseline (legitimate, not an error). K ≥ num_layers → clamped to "all layers" (≈ uniform LoRA).
- Deterministic given fixed inputs; ties (within 1e-6) broken by lower layer index.
- K/threshold and final metric chosen **only** on target-validation — never on target-test.

## 5. Frozen LoRA Configuration

- Rank r = 8, fixed across all selected layers.
- Applied to attention **query and value** projections only (W_q, W_v).
- Segmentation decoder always trainable, regardless of K.
- No separate parameter-budget cap — DSSA and random-K automatically match in trainable-parameter count, since both use the same K, rank, and target matrices by construction.

## 6. Frozen Dataset Protocol

- A fixed, five-item compatibility checklist (band/resolution/taxonomy/licensing/shift-type disclosure) must pass before **any** pair is locked in — this checklist itself is frozen and reusable regardless of which pair is chosen.
- **The specific pair (LoveDA → DeepGlobe) is NOT frozen — see Section 10.**

## 7. Frozen Target Split

60% target-train / 15% target-validation / 25% target-test. target-probe (unlabeled) is a 10–20%-sized slice of target-train, labels unused during selection. target-validation and target-test are never touched by DSS or layer selection.

## 8. Frozen Baselines

Source-only, full fine-tuning, uniform LoRA, adapters, visual prompt tuning (if compatible), DSSA — **plus, now approved:** random-K layer selection (matched K/config) and source-vs-source null baseline (mandatory DSS validity check, must run first).

## 9. Frozen Ablations

Source-vs-source null → random-K → lowest-DSS → early/mid/late fixed-position → cosine-vs-MMD metric ablation → Top-K sweep (validation-only) → probe-size sensitivity → seed sensitivity → cross-domain validation → full efficiency measurement (params, memory, time) across all of the above.

## 10. Remaining Risks

- **Dataset (blocking):** LoveDA → DeepGlobe, verified this session (not from memory) — both datasets are RGB-only vs. Prithvi-EO-2.0's expected 6-band HLS input, and roughly 60–100× finer resolution than its 30 m pretraining scale (the model's own paper claims precedent down to 0.1 m, but the mechanism wasn't confirmed here). More decisively: **LoveDA and DeepGlobe use structurally different class taxonomies** (LoveDA separates building/road; DeepGlobe merges them into "urban" and adds "rangeland"/"unknown" with no LoveDA equivalent) — segmentation accuracy across the pair is not currently well-defined without an explicit remapping decision nobody has made yet.
- **Scientific (open by design, not defects):** representation drift may not correlate with task-relevant importance; DSS may reduce to detecting layer noise rather than genuine sensitivity; DSS-selected layers may perform no better than random ones; efficiency gains may be limited to parameter count and not extend to FLOPs/wall-clock time.
- **Novelty (non-blocking for freeze, blocking for publication claims):** the novelty comparison so far covers only two papers (SPECTRA, CrossEarth-Gate) found in one prior session, not the broader "latest literature" the abstract itself says must be checked.

## 11. Exact Assumptions We Are Making

- Frozen-backbone representations, mean-pooled per image, are a reasonable unit of comparison for domain sensitivity (O-A).
- The source domain is concentrated enough around its own centroid for a single-centroid comparison to be meaningful (O-B).
- A layer's own source-vs-source null variance is a fair baseline for what counts as "just noise" at that layer (O-C).
- Cosine distance (directional) and MMD (distributional) together are sufficient without CKA for the first round of evidence (N-1).
- Attention-projection-only, fixed-rank LoRA isolates the layer-*selection* question from the rank/matrix-*allocation* question well enough to test the core hypothesis cleanly (O-E, O-F).
- Whichever dataset pair is ultimately chosen will pass the five-item compatibility checklist (O-J) before being used — **not yet true for LoveDA → DeepGlobe as currently specified.**

## 12. Final Statement

## NOT READY TO IMPLEMENT

Every methodological decision this round (A–J) is resolved with a single, justified default, and all three previously-flagged research decisions (CKA, random-K, null baseline) are approved and frozen. The one remaining implementation-blocking item is the dataset pair: live verification this session confirmed LoveDA and DeepGlobe use incompatible class taxonomies, and both are a severe band/resolution mismatch against Prithvi-EO-2.0's pretraining specification. This was not invented or assumed — it was checked against primary sources (the LoveDA and DeepGlobe papers, and Prithvi-EO-2.0's own arXiv abstract) in this review.

Per instruction, no replacement dataset was chosen. Three concrete paths are laid out in `DSSA_PROJECT_FREEZE.md` §P for the team to choose between. Once that single decision is made and the five-item compatibility checklist (§O-J) is run against whichever pair results, this document should be updated and re-issued — at that point, if no new blocking issue surfaces, the project would be **READY TO IMPLEMENT**.

No code was written to produce this review.
