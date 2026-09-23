# DSSA Project Freeze

**Status: NOT READY TO FREEZE — one decision remains open (the dataset pair).** All three previously-flagged research decisions from the first review round are now **APPROVED** (Section N-1). All ten remaining methodological decisions (A–J) have been resolved with a single defensible default each (Section O). The dataset question was investigated with live verification (not memory) and **cannot be silently resolved** — see Section P, `DATASET DECISION REQUIRED`.

Companion documents: `DSSA_ABSTRACT_GAP_ANALYSIS.md` (original 16-gap register), this document (current state of record).

Every implementation-critical line below is tagged **[FROZEN]** or **[DECISION REQUIRED]**.

---

## A. Frozen Research Question `[FROZEN]`

> Can layer-wise representation drift, measured from a frozen geospatial foundation model using only unlabeled target-domain images, identify which transformer layers are worth adapting — such that inserting LoRA only into those layers produces target-domain segmentation accuracy competitive with full fine-tuning or uniform LoRA, using substantially fewer trainable parameters?

## B. Frozen Hypothesis `[FROZEN]`

> Transformer layers in a pretrained geospatial foundation model are not equally affected by domain shift. A layer-wise Domain Sensitivity Score (DSS), computed from unlabeled source and target representations before any adaptation, can identify a small subset of layers such that adapting only that subset (via LoRA) yields segmentation performance competitive with adapting all layers (uniform LoRA) or the full model (full fine-tuning), while using substantially fewer trainable parameters.

Falsifiable: fails if DSS-selected layers perform no better than randomly-selected layers of the same count, or if the accuracy gap versus full fine-tuning/uniform LoRA exceeds a pre-agreed margin.

## C. Frozen Scope `[FROZEN]`

Unchanged from the previous review — see prior text, still valid.

## D. Explicit Non-Goals `[FROZEN]`

Unchanged from the previous review — see prior text, still valid.

## E. Frozen Methodology `[FROZEN]`

The 6-stage pipeline (§5 of the abstract) — unchanged, still frozen at this level of description.

---

## N-1. Previously-Flagged Decisions — NOW APPROVED

### 🚨→✅ Flag 1 — CKA: **DEFERRED** `[FROZEN]`

- CKA is **not** implemented in the first version of DSSA.
- No unpaired-sample CKA variant is invented or adopted at this time.
- CKA remains documented as future work, to be revisited only if cosine/MMD prove insufficient.
- **DSS candidate metrics for the first implementation: cosine distance and MMD only.**

### 🚨→✅ Flag 3a — Random-K layer selection: **APPROVED as mandatory baseline** `[FROZEN]`

- Same K as DSSA, same LoRA configuration (rank, target matrices — see O-E, O-F), same training data, same training budget, same evaluation protocol.
- Layer indices for the random draw are sampled with a fixed, logged seed per run (see O-H for the determinism policy this extends).

### 🚨→✅ Flag 3b — Source-vs-source null baseline: **APPROVED as mandatory DSS validity control** `[FROZEN]`

- Must be computed and inspected **before** any source-vs-target DSS ranking is trusted or used for layer selection.
- Implementation detail: this control is also the mechanism used to resolve decision O-C (cross-layer normalization) below — the null-baseline computation is not a one-off check, it is load-bearing infrastructure reused inside the DSS pipeline itself.

---

## O. Remaining Methodological Decisions — Resolved (One Default Each)

Each item: what it is → why it's appropriate → what assumption it introduces → how it will be tested. Each is a single proposed default, not a menu.

### O-A. DSS pooling strategy `[FROZEN]`

**Default:** Mean-pool over the spatial/patch-token dimension, per image, per layer — one vector per image per layer, discarding token position.

**Why:** Removes dependence on token-grid size (which varies with input resolution and patch geometry — relevant given the resolution questions in Section P). Matches common practice in representation-similarity literature. Much cheaper than per-token comparison, avoiding the O(N²)-over-tokens cost flagged in the earlier audit.

**Assumption introduced:** Discards spatial/positional information — if domain sensitivity is spatially localized within an image (e.g., only at edges, or only for certain object types), pooling could dilute that signal.

**How tested:** Not a required ablation for the core hypothesis test; if results are ambiguous, compare against an unpooled (per-token) variant on a small subset as a follow-up sensitivity check.

### O-B. DSS sample aggregation `[FROZEN]`

**Default:** Two-stage aggregation, not full pairwise and not pure centroid-to-centroid: (1) compute a single **source centroid** per layer (mean of pooled source-probe representations); (2) for each target-probe image, compute its distance to that source centroid; (3) DSS = the **mean of these per-target-image distances**.

**Why:** Pure centroid-to-centroid comparison can hide real distributional spread via cancellation (flagged in the original math audit); full pairwise comparison is O(N_source × N_target), expensive at scale. This middle ground is O(N_target), cheap, and preserves target-side distributional information via the per-image distances (whose spread can be reported as a diagnostic).

**Assumption introduced:** Assumes the source domain is reasonably concentrated around its own centroid (i.e., source data isn't wildly multimodal). If source data mixes very different scene types, a single centroid may not represent it well.

**How tested:** Report source-side per-image spread (distance of each source-probe image to the source centroid) as a diagnostic — this falls out of the already-approved source-vs-source null baseline computation at no extra cost.

### O-C. DSS cross-layer normalization `[FROZEN]`

**Default:** Z-score each layer's raw DSS against **that same layer's** source-vs-source null-baseline distribution (estimated via bootstrap resampling of the source-probe set): `normalized_DSS_l = (raw_DSS_l − mean(null_l)) / std(null_l)`.

**Why:** Directly fixes the magnitude-vs-genuine-sensitivity confound identified in the original audit (naturally high-variance layers otherwise dominate raw rankings) — and reuses the mandatory null-baseline control (Flag 3b) rather than adding new machinery.

**Assumption introduced:** With a small source-probe set, the bootstrap-estimated null distribution is itself noisy (few resamples) — confidence should be reported, not just a point estimate.

**How tested:** Compare Top-K selection under raw vs. normalized DSS; if they select different layers *and* downstream accuracy differs, that validates the normalization step mattered.

### O-D. Exact cosine DSS mathematical definition `[FROZEN]`

Given O-A and O-B, for layer *l*:

1. `s_i = mean_over_tokens(h_l(x_i))` for each source-probe image *i* (pooled representation).
2. `c_src = mean_i(s_i)` (source centroid).
3. `t_j = mean_over_tokens(h_l(x_j))` for each target-probe image *j*.
4. `d_j = 1 − (c_src · t_j) / (‖c_src‖ · ‖t_j‖ + ε)`, ε = 1e-8 (guards zero-vector division).
5. `raw_DSS_l = mean_j(d_j)`.
6. `normalized_DSS_l` per O-C.

**Why:** Cosine distance is scale-invariant, has no kernel/bandwidth hyperparameter (unlike MMD) and no paired-sample requirement (unlike CKA) — the fewest additional undetermined choices of the two approved candidate metrics, making it the natural first metric to implement. MMD (second approved candidate) is implemented and compared against it per the already-planned metric ablation (E9).

**Assumption introduced:** Captures only directional (angular) difference; ignores magnitude/scale shift entirely.

**How tested:** Already covered by the approved cosine-vs-MMD ablation (E9) — divergence between the two rankings is itself informative about whether direction or magnitude dominates the real signal.

### O-E. LoRA rank `[FROZEN]`

**Default:** Fixed rank **r = 8**, uniform across all selected layers (not variable by DSS magnitude).

**Why:** A well-precedented, unremarkable default from the broader LoRA literature. A fixed rank keeps the experiment focused on the actual research question (does *layer selection* matter) rather than conflating it with a second, untested question (does *rank allocation* also matter) — that second question is what SPECTRA already studies; DSSA's contribution is about selection, so rank should not be a confound.

**Assumption introduced:** A single fixed rank may be suboptimal in absolute accuracy for some layers versus others — acceptable, since isolating the selection question is the priority for the first implementation.

**How tested:** Rank sensitivity (r = 4, 8, 16) is a candidate secondary ablation, deferred until the primary DSSA vs. random-K vs. uniform-LoRA comparison (at fixed rank) is validated.

### O-F. LoRA target matrices `[FROZEN]`

**Default:** Attention **query and value** projection matrices only (W_q, W_v) — not key, not output projection, not MLP.

**Why:** This is the original LoRA paper's primary, most widely reproduced configuration (W_q/W_v captured most of the benefit at lowest parameter cost in that study) — a minimal-surprise default that keeps the trainable-parameter count, and therefore the efficiency claim, as clean and interpretable as possible.

**Assumption introduced:** Assumes attention projections are where domain-relevant adaptation matters most, not the MLP sublayers. If the true adaptation need is more in the MLP blocks, this default would systematically under-adapt regardless of layer-selection quality — a real, acknowledged limitation, not tested in the first round.

**How tested:** Not a required ablation (would multiply the experiment grid); documented as a scope-limiting design choice, revisited only if primary results are inconclusive.

### O-G. Trainable parameter budget policy `[FROZEN]`

**Default:** No separate numeric budget cap. Given O-E and O-F are fixed, trainable-parameter count for "K selected layers" is a deterministic function of K alone — so DSSA and random-K, sharing the same K by construction (already approved), automatically have **identical** trainable-parameter counts without any extra budget-matching mechanism.

**Why:** Simplest possible way to satisfy the already-approved fairness requirement (random-K at "same K, same LoRA configuration") — no additional policy needed beyond what O-E/O-F/random-K approval already fix.

**Assumption introduced:** None beyond O-E/O-F.

**How tested:** Trivial correctness check — assert DSSA and random-K trainable-parameter counts are exactly equal at matched K.

### O-H. Deterministic tie-breaking `[FROZEN]`

**Default:** Ties in (normalized) DSS — within a 1e-6 tolerance, to absorb floating-point noise — broken by preferring the **lower layer index** (earlier in the network). Random-K's own sampling (N-1, Flag 3a) uses a separate, explicitly logged random seed per run — deterministic tie-breaking applies to the DSS ranking itself, not to the random-K control's intentionally random draw.

**Why:** Simple, fully deterministic, no extra configuration; exact ties are expected to be rare with continuous-valued scores, so the specific convention matters far less than having one at all.

**Assumption introduced:** None of scientific consequence — a pure implementation-determinism concern.

**How tested:** Unit test — running layer selection twice on identical inputs must produce an identical selected-layer set.

### O-I. Exact target split percentages/protocol `[FROZEN policy / sizes contingent on dataset]`

**Default:** 60% target-train / 15% target-validation / 25% target-test. target-probe (unlabeled) is a slice of target-train, sized at roughly 10–20% of the total target pool (capped at a few hundred images for compute reasons) — its labels simply are not accessed during the selection step, even though they exist. target-validation and target-test are never touched by DSS computation (already frozen in the prior review's split policy).

**Why:** 60/15/25 is a standard, unremarkable split ratio; drawing target-probe from within target-train (rather than a fifth physical partition) keeps the scheme simple while still strictly protecting target-validation/target-test from the selection step.

**Assumption introduced:** Assumes target-train is large enough that carving out a probe-sized unlabeled slice doesn't meaningfully starve the subsequent LoRA fine-tuning step. For a small target dataset this could be a real tension.

**How tested:** Once the dataset (Section P) is resolved and exact sample counts are known, verify the probe slice doesn't leave target-train too small; if it does, fall back to a literal fifth held-out probe pool instead — a contingency, not a re-decision of the policy itself.

### O-J. Dataset compatibility verification requirements `[FROZEN policy]`

**Default:** A fixed, mandatory five-item checklist, to be completed and documented (pass/fail) before **any** dataset pair is locked in:

1. Band count/order compatibility with the chosen backbone's expected input, with a named handling strategy if mismatched (not silent duplication/zero-fill).
2. Ground sampling distance (resolution) compatibility with the backbone's pretraining scale, with a named resizing/patch-handling strategy if mismatched.
3. Class taxonomy alignment — identical label sets, or an explicit, documented remapping table with an assessment of how many classes/pixels are affected.
4. Licensing terms permit the intended academic use (and any planned redistribution of code/checkpoints).
5. An explicit statement of which shift types (sensor / geography / content / class-distribution / resolution) the chosen pair is understood to vary, so the claimed framing (e.g., "cross-sensor") matches what was actually tested.

**Why:** Operationalizes the abstract's own §8 "critical rule" into a concrete, reusable, checkable gate — applies to whichever pair is finally chosen, so it doesn't need to be re-derived if the dataset decision changes.

**Assumption introduced:** None — formalizes a commitment the abstract already made.

**How tested:** Not an experiment — a one-time verification gate. **Applied below, to LoveDA → DeepGlobe specifically.**

---

## P. Dataset Verification — LoveDA → DeepGlobe

Checked against the O-J checklist using live, sourced verification (not memory) in this review.

| Property | LoveDA | DeepGlobe (Land Cover) | Prithvi-EO-2.0 (backbone) |
|---|---|---|---|
| Sensor / source | Google Earth platform imagery | WorldView-3 satellite | Pretrained on NASA HLS (Harmonized Landsat–Sentinel-2) |
| Resolution | 0.3 m/pixel | 0.5 m/pixel | Pretrained at **30 m**/pixel |
| Bands | RGB only (3) | RGB only (3) | Expects **6 bands**: Blue, Green, Red, Narrow NIR, SWIR1, SWIR2 |
| Classes (7 each) | background, building, road, water, barren, forest, agricultural | urban, agriculture, rangeland, forest, water, barren, unknown | — |
| Geography | 3 Chinese cities (Nanjing, Changzhou, Wuhan) | Thailand, Indonesia, India (2013–2017) | Global |

*Sources: LoveDA — NeurIPS 2021 datasets-and-benchmarks paper; DeepGlobe — DeepGlobe 2018 challenge paper and dataset documentation; Prithvi-EO-2.0 — arXiv:2412.02732 abstract and Hugging Face model card, fetched directly for this review.*

### O-J checklist result

1. **Band compatibility — FAIL as stated.** Both datasets are RGB-only (3 bands); Prithvi-EO-2.0 expects 6 bands including two SWIR channels neither dataset has. A named handling strategy (patch-embedding redesign for 3 channels, or explicit channel duplication/zero-fill with its artifacts acknowledged) is **not specified anywhere** in our abstract, unlike SPECTRA, which has an explicit mechanism (Band-Routed Embedding) for exactly this problem. *Mitigating context, found this session:* the Prithvi-EO-2.0 paper's own abstract states the model "outperforms six other geospatial foundation models when benchmarked on remote sensing tasks from different domains and resolutions (i.e. from 0.1 m to 15 m)" — meaning some adaptation path to non-native band/resolution inputs has precedent in the original authors' own benchmark suite. The exact mechanism was not confirmed from the abstract alone and would need to be traced through the full paper or codebase before relying on it.
2. **Resolution compatibility — FAIL as stated, but precedented.** Both datasets are ~60–100× finer resolution than Prithvi-EO-2.0's 30 m pretraining scale. This is a severe mismatch on its face, but per point 1's mitigating context, the backbone has apparently been used successfully down to 0.1 m elsewhere. No resizing/patch-handling strategy is specified in our abstract.
3. **Class taxonomy — FAIL, confirmed.** The two label sets are structurally different, not just differently named: LoveDA separates **building** and **road** as distinct classes, which DeepGlobe collapses into a single **urban** class; DeepGlobe has **rangeland** and **unknown** classes with no LoveDA equivalent. Segmentation accuracy across this pair is **not well-defined** without an explicit, lossy remapping — and no such remapping is specified anywhere in our materials.
4. **Licensing — NOT CHECKED this session** (out of scope for this pass; both are established public academic benchmarks, but exact license terms were not re-verified here).
5. **Shift types actually varied by this pair, separated explicitly:**
   - **Sensor shift:** Yes — genuinely different acquisition platforms (Google Earth composite vs. WorldView-3 direct capture).
   - **Geographic shift:** Yes — China vs. Thailand/Indonesia/India.
   - **Content/scene shift:** Likely yes (not independently measured) — different urban morphology and vegetation are plausible given the geographic difference, but not quantified.
   - **Class-distribution / taxonomy shift:** Yes, confirmed structurally different (see point 3) — this is a confound with the "domain shift" being studied, not a form of it.
   - **Resolution shift, source vs. target themselves:** Small (0.3 m vs. 0.5 m, ~1.7×) — not a major factor **between the two datasets**. The large resolution mismatch is **against the backbone**, symmetrically affecting both source and target, not a source-vs-target confound per se.
   - **Band/spectral shift, source vs. target themselves:** **None** — both are RGB-only, so this dimension does not vary between source and target (though both vary strongly against the backbone's expected 6-band input, symmetrically).

### 🚨 DATASET DECISION REQUIRED

**LoveDA → DeepGlobe, as currently specified in the abstract (no remapping scheme, no band-handling scheme, no resolution-handling scheme documented), cannot support the research question as written.** The specific, confirmed problem is not "domain shift might be confounded" in the abstract — it is:

- A **verified class-taxonomy mismatch** makes segmentation accuracy comparison across the pair ill-defined without a decision the team has not yet made.
- A **verified band and resolution mismatch against the backbone** (not between the two datasets) requires an explicit handling strategy that neither the abstract nor this review invents on the team's behalf, per instruction.

The part of the original claim that **does** hold up: there is a genuine, real sensor-and-geography shift between LoveDA and DeepGlobe themselves — that part of the "cross-sensor domain shift" framing is defensible. What is not yet resolved is whether it can be **measured cleanly**, given the confounds above.

**No replacement dataset is chosen here.** Paths the team could choose between (not a recommendation, per instruction — options only):
- (a) Define and document an explicit class-remapping between LoveDA and DeepGlobe, accept the resulting label-definition noise as a known limitation, and decide on a band/resolution-handling strategy for Prithvi-EO-2.0 (e.g., patch-embedding redesign for 3-band input, with resizing to a scale closer to the backbone's pretraining GSD).
- (b) Use a **same-sensor** pair for the first phase (e.g., LoveDA's own Urban↔Rural split — same sensor, same label taxonomy, same resolution, varying mainly geography/content), which sidesteps the band/taxonomy problems entirely and gives a cleaner first test of the DSS mechanism itself, with a genuine cross-sensor pair (LoveDA→DeepGlobe or otherwise) reserved for the cross-domain validation phase (already-planned E10) once the method is validated on a cleaner pair.
- (c) Select a different target dataset entirely that is both band-and-resolution-compatible with Prithvi-EO-2.0 (i.e., Landsat/Sentinel-2-scale, multispectral) and taxonomy-compatible with LoveDA — not identified or searched for in this review.

---

## Q. Frozen Baselines `[FROZEN]`

| Baseline | Status |
|---|---|
| Source-only | Frozen (abstract E1) |
| Full fine-tuning | Frozen (abstract E2) |
| Uniform LoRA | Frozen (abstract E3) |
| Adapters | Frozen (abstract §9) |
| Visual Prompt Tuning (if compatible) | Frozen (abstract §9) |
| DSSA (Top-K by DSS) | Frozen (abstract E7) |
| Random-K layer selection | **Frozen — approved, Section N-1** |
| Source-vs-source null baseline | **Frozen — approved, Section N-1** |

## R. Frozen Data Split Policy `[FROZEN]`

Unchanged structurally from the prior review (probe / train / validation / test, target-test and target-validation never touched by DSS); exact percentages now fixed per O-I.

## S. Frozen Evaluation Metrics `[FROZEN]`

Unchanged — mIoU, per-class IoU, F1, pixel accuracy (segmentation); trainable parameters, GPU memory, training time, inference time reported as **separate, distinct quantities** (efficiency).

## T. Required Ablations `[FROZEN]`

Unchanged list from the prior review (source-vs-source null; random-K; lowest-DSS; early/mid/late; cosine-vs-MMD metric ablation, CKA excluded per N-1; Top-K sweep; probe-size sensitivity; seed sensitivity; cross-domain validation; full efficiency measurement).

## U. Known Risks `[FROZEN — as open experimental questions]`

Unchanged from prior review, **plus**: the dataset-specific risk that a class-taxonomy remapping (if path (a) in Section P is chosen) introduces its own label noise, separate from any noise the model itself contributes.

## V. Decisions Still Requiring Human Approval

Only one remains implementation-blocking:

1. 🚨 **Dataset pair — Section P.** Must be resolved before implementation: fix LoveDA→DeepGlobe with explicit remapping/band/resolution decisions (path a), substitute a cleaner same-sensor first-phase pair (path b), or find an alternative (path c).

Non-blocking, but should be resolved before any public novelty claim (unchanged from prior review):

2. Whether the two-paper novelty comparison (SPECTRA, CrossEarth-Gate) is sufficient, or a broader/refreshed literature search is needed before publication-facing novelty language is used.

---

**This project is NOT READY TO FREEZE until item 1 above is resolved.** Every other implementation-critical decision (A–J, plus the three original flags) is now `[FROZEN]`. See `DSSA_FREEZE_FINAL_REVIEW.md` for the consolidated final statement.
