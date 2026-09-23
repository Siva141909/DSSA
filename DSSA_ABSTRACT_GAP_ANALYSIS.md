# DSSA Abstract Gap Analysis

**Primary source:** `DSSA_Final_Project_Abstract.pdf` (read in full for this audit — not the PPT, not the presentation script, not prior sessions' assumptions). All quotes below are taken directly from that document.

**Posture for this document:** hostile reviewer. The question asked throughout is not "how would we build this," it is **"why should I believe this reasoning is sound?"**

---

## 1. Abstract Summary

The abstract (title: *"DSSA — Domain Sensitivity-guided Selective Parameter-Efficient Adaptation for Cross-Sensor Remote Sensing Semantic Segmentation"*) proposes: take a pretrained geospatial foundation model (initial choice: Prithvi-EO-2.0), measure how much each transformer layer's internal representation changes between labeled source-domain data and *unlabeled* target-domain data, rank layers by this "Domain Sensitivity Score" (DSS), select the most-affected layers (Top-K or threshold), insert LoRA only into those layers, and fine-tune. The stated goal is competitive target-domain segmentation accuracy at substantially lower trainable-parameter and compute cost than full fine-tuning or uniform LoRA. The abstract explicitly frames this as a **proposed research direction**, not a proven result, and explicitly requires ("Important," Section 6) a novelty audit before any novelty claim is made.

---

## 2. Claims Extracted From Abstract

| Claim | Exact meaning | Evidence in abstract | Confidence |
|---|---|---|---|
| C-1 | Foundation models degrade under domain shift (sensor/region/season/resolution/atmosphere) | "Modern geospatial foundation models achieve strong performance on remote-sensing tasks but can degrade when applied to imagery from different sensors, geographic regions, seasons, resolutions, or acquisition conditions." (§1) | High — well-established general phenomenon in the field; not specific to this project. |
| C-2 | Conventional adaptation (full FT or uniform PEFT) may update parameters unaffected by domain shift | "These strategies can update many parameters that may not be equally affected by domain shift." (§1) | Medium — plausible, but the abstract cites no prior evidence that this is actually true, only that it "may" be true. Stated as an assumption, correctly hedged with "may." |
| C-3 | Hypothesis: layers are not equally affected by domain shift; measuring drift can find the affected ones; adapting only those is competitive at lower parameter cost | "Domain shift does not affect every transformer layer equally. Measuring layer-wise representation drift can identify domain-sensitive layers; selectively adapting those layers should provide competitive target-domain segmentation while using substantially fewer trainable parameters..." (§3) | Stated correctly as a **hypothesis** — appropriately hedged with "should." Not yet evidenced. |
| C-4 | DSS quantifies source-to-target representation drift per layer | "Domain Sensitivity Score (DSS): quantify source-to-target representation drift for each transformer layer." (§4) | Definitional — this is a proposed measurement, not itself a claim requiring evidence, but see Section 5 of this document for whether it is *defined precisely enough to compute*. |
| C-5 | Candidate DSS metrics: cosine-distance statistics, MMD, CKA; final metric chosen empirically | "Candidate measures include cosine-distance statistics, Maximum Mean Discrepancy (MMD), and centered kernel alignment (CKA). The final metric should be selected empirically after a small validation study." (§6) | Appropriately hedged — explicitly deferred, not claimed as solved. |
| C-6 | DSS uses unlabeled target images | "Pass unlabeled target images through the frozen backbone" (§5, Stage 2) | Precise for the **selection step only** — see Gap G-11 for a wording risk this creates elsewhere. |
| C-7 | Efficiency: fewer trainable parameters and lower cost than full FT/uniform PEFT | "...substantially reducing trainable parameters and computational cost compared with full fine-tuning and uniform PEFT." (§1) | Stated as the project's target outcome, not an achieved result — abstract does not distinguish parameter count from FLOPs/wall-clock time here (see Gap G-15). |
| C-8 | DSSA is not claimed as novel yet; a novelty audit is required | "Important: DSSA is a proposed research direction, not a guaranteed novel contribution. A final targeted novelty audit against the latest literature is required before claiming novelty in a paper." (§6) | This is the abstract being explicitly, deliberately conservative — a genuine strength, not a weakness (see Section 8). |
| C-9 | Do not claim cross-sensor transfer without a defensible shift | "Do not claim cross-sensor transfer if the selected datasets do not actually provide a defensible sensor/domain shift." (§16) | The abstract has already anticipated the dataset-confound risk explored in Gap G-6/G-7 below, as a self-imposed rule — but the rule is a future commitment, not yet satisfied. |

---

## 3. Research Logic Audit

The abstract's implicit reasoning chain, made explicit:

```
Problem (domain shift hurts segmentation accuracy)
        ↓
Domain shift (sensor / region / season / resolution / atmosphere / spectral — bundled together)
        ↓
Representation drift (the model's internal features change between source and target)
        ↓
DSS (a chosen statistic quantifies that drift, per layer)
        ↓
Layer sensitivity (high DSS = "this layer is domain-sensitive")
        ↓
Selective LoRA (adapt only high-DSS layers)
        ↓
Improved adaptation (competitive accuracy, far fewer trainable parameters)
```

| Arrow | Status | Reasoning |
|---|---|---|
| Problem → Domain shift | **Established** | Well-documented general phenomenon; not controversial. |
| Domain shift → Representation drift | **Assumed** (with general precedent) | Domain shift causing representation-distribution shift in deep networks is broadly consistent with domain-adaptation literature generally, but the abstract cites no specific prior evidence that this holds for Prithvi-EO-2.0 specifically, at the per-layer granularity proposed. Experimentally testable. |
| Representation drift → DSS | **Proposed (definitional)** | DSS is *defined as* an operationalization of drift; this arrow is a methodological choice, not an empirical claim. Its validity depends entirely on the precision of the definition (see Section 5 — currently underspecified). |
| DSS → Layer sensitivity | **Assumed, unsupported** | The leap from "this layer's output statistics changed" to "this layer is meaningfully *sensitive* (as opposed to just naturally high-variance/noisy)" is not defended anywhere in the abstract. No null-baseline or control is proposed to rule out the alternative explanation. Experimentally testable (see Gap G-5, G-16). |
| Layer sensitivity → Selective LoRA (i.e., sensitive layers are the *right* layers to adapt) | **Assumed, unsupported — the weakest link in the chain** | Representation-space drift and task-relevant (loss-gradient) importance are not the same thing. A layer can shift a lot in representation space while being nearly irrelevant to the segmentation loss, or shift little while being exactly where the fix needs to happen. The abstract does not address this distinction at all. Experimentally testable, but currently there is no evidence either way. |
| Selective LoRA → Improved adaptation | **Explicitly framed as the hypothesis to test** | This is Section 3's Hypothesis, correctly hedged with "should." This is the one arrow the abstract itself already treats as unproven — appropriately. |

**Finding:** the abstract does **not** present these arrows as already-equivalent or already-proven — the hedged language ("may," "should," "candidate," "proposed") is used consistently and correctly throughout. The weakness is not overclaiming within the text; it is that **the two weakest arrows (DSS → Layer sensitivity, Layer sensitivity → Selective LoRA) currently have no proposed control or check in the experimental design** to distinguish "this worked because DSS is meaningful" from "this worked because adapting *any* subset of layers of this size helps." See Section 6 and Gap G-10/G-16.

---

## 4. Research Gaps

| ID | Severity | Location in abstract | Problem | Why it matters | Assumption exposed | What must be decided | Blocking? |
|---|---|---|---|---|---|---|---|
| G-1 | High | §2 Problem Statement | "Sensor characteristics, geographic location, season, spatial resolution, atmospheric conditions, or spectral statistics" are all bundled as one thing — "domain shift" — with no plan to isolate which factor(s) the experiments will actually test. | An experiment that varies several of these factors at once cannot attribute a result to any one of them. | That "domain shift" is a single, interchangeable phenomenon regardless of cause. | Which shift type(s) will the primary experiment isolate? | **YES** |
| G-2 | High | Title vs. §3 Hypothesis, §8 | The title specifically promises **"Cross-Sensor"** adaptation; the Hypothesis and dataset strategy are written generically about "domain shift" without a sensor-specific mechanism or guarantee that the chosen pair isolates sensor shift specifically. | Risk of a title/claim the eventual experiment cannot support. | That the planned dataset pair automatically delivers a "cross-sensor" test because the title says so. | Confirm (or narrow the title to) exactly which shift the frozen dataset pair provides — see G-6. | **YES** |
| G-3 | High | §6 DSS Formulation | DSS is defined only qualitatively: "a distance/similarity statistic... to estimate how strongly that layer changes." No formula, no pooling rule (per-token vs. per-image), no sample-aggregation rule (pairwise vs. centroid), no normalization across layers. | Three different engineers could implement three mathematically different things, all calling themselves "DSS." | That "compare representations" is a well-defined operation without further specification. | **IMPLEMENTATION-BLOCKING AMBIGUITY** — see Section 5. | **YES** |
| G-4 | High | §6 | Of the three named candidate metrics, **CKA** is classically defined for *paired* samples (same inputs, two representations) — our use case compares *unpaired* source vs. target image sets at the same layer. The abstract does not address this mismatch. | If applied naively, "CKA" would not compute what the abstract intends; results would be uninterpretable or simply wrong. | That CKA is a drop-in tool applicable to any two representation matrices, regardless of whether rows correspond to the same underlying samples. | 🚨 See Critical Flags, below. | **YES** |
| G-5 | Medium | §6 (absence) | No normalization step is defined to separate "genuinely domain-sensitive" from "naturally high-variance/noisy" layers — no source-vs-source null-comparison is proposed. | Without this, DSS could just rank layers by their baseline representational variance, which is a different (and less interesting) thing than domain sensitivity. | That raw drift magnitude is directly comparable and meaningful across layers without a baseline. | Add an explicit null-baseline step to the DSS protocol (see Section 6, Layer Selection audit, below). | **YES** |
| G-6 | High | §8 Dataset Strategy | Primary source (LoveDA) and primary target (DeepGlobe) differ in sensor **and** geography **and**, based on general knowledge of these two widely-used benchmarks (**not re-verified in this session**), very likely differ in class-label taxonomy. If labels differ, segmentation accuracy across the pair is not even well-defined without an explicit class-remapping step, which is not mentioned anywhere. | The dataset pair may not isolate the "domain shift" the project studies from confounds of scene content and label definitions. | That "primary source: LoveDA... primary target: DeepGlobe" (§8) is a usable pair as stated, without further verification. | 🚨 See Critical Flags, below. | **YES** |
| G-7 | Medium | §8 | The abstract's own safeguard — "the final source–target pair must be locked only after checking sensor bands, spatial resolution, labels, licensing, and preprocessing compatibility" (§8) — is stated as a future action, not yet performed. | The entire experimental plan currently rests on an unverified pair. | That this check will pass, or is a formality. | Perform the check the abstract already requires, before anything else proceeds. | **YES** |
| G-8 | High | §2 vs. §5 (pipeline) | "Sensor characteristics" and "spectral statistics" are named domain-shift causes (§2), but the proposed pipeline (§5) has no band-alignment/remapping stage analogous to what related work (SPECTRA's Band-Routed Embedding) uses to handle exactly this problem. | If source and target sensors have different band layouts, early-layer representations will differ for a trivial input-format reason, contaminating DSS with a non-domain-sensitivity artifact. | That the frozen backbone can consume both sensors' imagery without any band-level reconciliation step. | Confirm whether the eventual dataset pair has matched bands; if not, decide whether to add a band-alignment step or restrict scope. | **YES, conditional on G-6/G-7 outcome** |
| G-9 | High | §6, §17, §20 | The abstract itself never names a specific competing paper. Its "Related Work" is listed only as a placeholder chapter topic — "geospatial foundation models, SSL, domain adaptation, PEFT" (§17) — not populated with citations. The required "targeted novelty audit against the latest literature" (§6) has only been partially attempted, in a separate later session, against two papers (SPECTRA, CrossEarth-Gate) found via web search — not against the full current literature, and not re-verified since. | Any novelty claim currently rests on a two-paper comparison, not the "targeted... audit against the latest literature" the abstract itself calls for. | That finding two related papers constitutes having performed the required audit. | Explicit decision: is a two-paper comparison sufficient to proceed, or is a broader/refreshed search required before any novelty language is used publicly? | No (does not block freezing the research *question*, blocks any *novelty claim*) |
| G-10 | High | §9 Baselines, §10 Experiments (E1–E12) | The planned baseline/experiment list has **no random-layer-selection control** (adapt a random K layers, same K as DSSA). Without it, there is no way to distinguish "DSS-guided selection is better than arbitrary selection" from "adapting any K layers helps, regardless of which ones." | This is the minimum control needed to test the central hypothesis (Layer sensitivity → Selective LoRA, per Section 3). As currently planned, the hypothesis **cannot be falsified** even in principle. | That comparing DSSA against uniform LoRA and full fine-tuning is sufficient to validate the *selection* mechanism specifically. | 🚨 See Critical Flags, below. | **YES** |
| G-11 | Medium | §5 (architecture table), §1 (Executive Abstract) | "Unlabeled target images" is specified only for the DSS/layer-selection step (§5, Stage 2). The abstract never explicitly states, anywhere, that the subsequent LoRA fine-tuning step (§5, Stage 5) requires *labeled* target data. | Risk that "unlabeled target data" gets communicated as if the *entire method* needs no target labels, which would misstate what DSSA actually does. | That the scope of the "unlabeled" claim is self-evident from context. | Precise wording must distinguish "label-free *selection*" from "label-free *adaptation*" (the latter is not true — see Section 9). | No (wording issue, not an implementation blocker) |
| G-12 | Medium | §5, §8 | No target-side data-split policy (probe / train / validation / test) is specified anywhere. | Without an explicit split, it is easy to accidentally let the same target images inform both layer selection and final reported metrics — a leakage risk. | That "unlabeled target images" (§5 Stage 2) is implicitly a separate pool from whatever produces final metrics. | Define and freeze a 4-way target split policy (Section J of the freeze document). | **YES** |
| G-13 | Medium | §5 Stage 4, §10 E8 | No protocol for choosing the final reported K. "Top-K sensitivity" is listed as an experiment (E8), but nothing says K will be chosen on a validation split rather than by peeking at test performance. | K chosen by looking at test results is leakage through hyperparameter search, even though DSS itself is label-free. | That sweeping K in an experiment automatically implies a leakage-safe protocol for choosing the *final* K. | Fix the protocol: K chosen only on a held-out validation split. | **YES** |
| G-14 | Low–Medium | §7 Tech Stack, §5 Stage 5 | LoRA is listed as "the adaptation mechanism" without stating this is a scoping choice (inherited from prior PEFT literature) rather than something DSS output logically requires. Rank, which weight matrices receive LoRA, and parameter budget are all unspecified. | Without these specifics, LoRA cannot actually be implemented once the project moves to that stage; also, the causal framing ("DSS says X, therefore LoRA") slightly overstates what DSS actually justifies (it justifies *where*, not *how*, to intervene). | That "insert LoRA" is a fully specified action once a layer is selected. | Specify rank policy and which matrices receive LoRA before implementation; state explicitly in any write-up that LoRA is a design choice, not a logical consequence of DSS. | **YES** (for implementation); **NO** (for freezing the research question) |
| G-15 | Medium | §1, §4 | "Substantially reducing trainable parameters and computational cost" (§1) and "trainable parameters, memory, training time, and inference cost" (§4) bundle several distinct quantities. Adapting fewer layers reduces trainable-parameter count and optimizer memory; it does **not** proportionally reduce forward-pass FLOPs, since the full frozen backbone still runs on every step. | Overclaiming "faster training" broadly, when only some sub-quantities are actually expected to drop, is the kind of statement a reviewer punctures immediately. | That "parameters," "memory," "time," and "cost" all move together in the same direction and magnitude. | Rewrite efficiency claims to name which specific quantities are expected to drop, and by what mechanism (see Section 9). | No (wording issue) |
| G-16 | Medium | §10 (absence) | No source-vs-source null-baseline experiment appears in E1–E12, despite being the cheapest, most direct check of whether DSS reflects genuine domain sensitivity rather than each layer's natural variance (same underlying issue as G-5, but this entry is about the missing *experiment*, not the missing *normalization step*). | Without this check, a positive DSSA result could be indistinguishable from "the metric is just noisy in a way that happens to correlate with layer depth." | That the planned experiment list (E1–E12) already covers what is needed to validate DSS itself, not just to validate the downstream adaptation. | Add this experiment to the required-ablations list. | **YES** |

**Gap count: 16 (G-1 through G-16). Implementation/validity-blocking: 13. Non-blocking (wording/claims precision only): 3 (G-9, G-11, G-15).**

---

## 🚨 Critical Flags — Research Decisions Required

Per the freeze rule, these are **not** silently resolved here. Each genuinely could change the shape of the research question, and each matches one of the example triggers given for this audit.

### 🚨 Flag 1 — DSS cannot currently be mathematically defined as written (Gap G-3, G-4)

The abstract's DSS definition is qualitative only, and one of its three named candidate metrics (CKA) is not valid in its standard form for the proposed unpaired source-vs-target comparison. **Options the team must choose between** (not chosen here):
- (a) Drop CKA from the candidate list and proceed with cosine distance and MMD only, both of which *are* directly applicable to unpaired sample comparison.
- (b) Keep CKA but adopt an explicitly two-sample-adapted variant (e.g., comparing kernel matrices computed separately per domain, rather than assuming row-paired samples) — this changes what "CKA" means in this project relative to its textbook usage, and that redefinition needs to be a deliberate, documented team decision, not an implementation detail decided in passing.
- (c) Defer CKA to a later phase and validate the method first with cosine/MMD only.

### 🚨 Flag 2 — The dataset pair may not support the stated research question (Gap G-1, G-2, G-6, G-7, G-8)

LoveDA → DeepGlobe, as named in the abstract, has not been checked against the abstract's own "critical rule." Based on general knowledge of these two benchmarks (explicitly **not re-verified this session** — this needs an actual check, not a recollection), they likely differ in sensor, geography, *and* class-label taxonomy simultaneously. This means:
- The pair may not isolate "cross-sensor" shift specifically, undermining the title's scope.
- If label taxonomies differ, segmentation accuracy across the pair may not be well-defined without an explicit, currently-unplanned class-remapping step.

**Per instructions, no new dataset is chosen here.** The team must decide: verify and fix this specific pair (confirm bands/labels/resolution match closely enough, or define a remapping), or restrict the first phase of experiments to a cleaner, same-sensor pair (e.g., LoveDA's own Urban↔Rural split, which was designed for controlled domain-adaptation study) with cross-sensor validation added as a later, separate phase.

### 🚨 Flag 3 — Selective layer adaptation cannot currently be fairly evaluated with the proposed baselines (Gap G-10, G-16)

As written, Section 9 (Baselines) and Section 10 (Experiments E1–E12) do not include a random-K-layer-selection control or a source-vs-source null baseline. Without these, DSSA's central hypothesis — that *which* layers are chosen matters, not just *how many* — cannot be distinguished from a much weaker, less interesting claim ("adapting some subset of layers, chosen almost any way, captures most of the benefit"). **This report recommends adding both as baselines**, but per the freeze rule, this is surfaced as a decision for team approval rather than silently added to the frozen spec.

---

## 5. Mathematical Gaps

Restated precisely, without inventing a solution:

- **DSS:** No formula given beyond "a distance/similarity statistic." Undefined: pooling strategy (per-token vs. per-image-pooled representations), sample-aggregation strategy (mean pairwise distance vs. distance-of-centroids — these are statistically very different and can give opposite conclusions), and whether/how DSS is normalized across layers before ranking.
- **Cosine distance:** Well-defined for unpaired comparison in principle, but needs an explicit choice of (a) per-vector normalization order and (b) an epsilon-guard for zero vectors — neither specified.
- **MMD:** Needs a kernel and bandwidth choice (neither specified); sensitive to sample size, and the abstract does not specify the expected probe-set size, so estimator stability cannot currently be assessed.
- **CKA:** See Flag 1 above — the standard formulation assumes paired samples; our use case is unpaired. This is not a minor detail, it changes what number would even be computed.
- **Source-target comparability:** Whether source and target representations are comparable at all depends on (a) matched preprocessing pipelines (not confirmed) and (b) — per Flag 2 — matched or reconciled input bands (not confirmed).
- **Layer/token-count alignment:** If source and target images have different spatial resolutions (explicitly named as a domain-shift factor in §2), their token grids will differ in size at a given layer unless pooled to a fixed-size representation first — not addressed in the abstract.

**Status: marked as implementation-blocking ambiguity, not resolved here, per instructions.**

---

## 6. Experimental Gaps

| Required control | Present in abstract's plan (§9, §10)? |
|---|---|
| Source-only baseline | Yes — E1 |
| Uniform LoRA | Yes — E3 |
| DSSA (Top-K by DSS) | Yes — E7 |
| **Random-K selection** | **No — missing (Flag 3)** |
| Different K values | Yes — E8 |
| Different DSS metrics | Yes — E9 |
| Different random seeds | **No — not mentioned anywhere** |
| **Source-vs-source null baseline** | **No — missing (Flag 3, Gap G-16)** |
| Fixed early/middle/late layer controls | Yes — E4, E5, E6 |
| Cross-domain validation | Yes — E10 |
| Explicit target probe/train/val/test split | **No — not specified (Gap G-12)** |
| K/metric selection protocol (validation-only, not test) | **No — not specified (Gap G-13)** |
| Parameter-budget-matched comparison (DSSA vs. uniform LoRA) | **No — not addressed (Flag 3)** |

---

## 7. Dataset Gaps

**No new dataset is chosen here — only what must be verified before the current pair can be used, per the abstract's own rule (§8).**

- Confirm LoveDA and DeepGlobe use the same or reconcilable **class-label taxonomies**; if not, define an explicit class-remapping and assess how much label-definition noise that remapping introduces.
- Confirm **band count and ordering compatibility** with Prithvi-EO-2.0's expected input, for both LoveDA and DeepGlobe.
- Confirm **spatial resolution** compatibility, or define a resizing/resampling policy and assess whether it introduces its own artifact into DSS (a resizing-induced representation difference is not "domain sensitivity").
- Confirm **licensing** permits the intended use (abstract already flags this as a requirement, §8).
- Confirm whether the shift between LoveDA and DeepGlobe is best characterized as sensor shift, geographic shift, or both simultaneously — and whether that matches what the title ("Cross-Sensor") promises.

---

## 8. Novelty Audit

**Already existing (established in prior work, including the two comparison papers used in a later session — SPECTRA, CrossEarth-Gate):**
- Using a pretrained geospatial foundation model as an adaptation backbone.
- LoRA as a parameter-efficient adaptation mechanism.
- The general idea of *selective* (not uniform) adaptation across a model's components — CrossEarth-Gate already does a form of this for remote-sensing segmentation specifically.
- Using an importance/sensitivity score to decide what to adapt — both SPECTRA (transferability score) and CrossEarth-Gate (Fisher Information) already do this.
- Comparing source vs. target representations to characterize domain shift — a long-standing idea in general domain-adaptation literature.

**Potentially new combination (per the abstract's own framing, not yet independently verified against the broader literature):**
- The specific DSS formulation (once mathematically finalized — see Flag 1).
- Using **unlabeled** target data as the *only* input to the selection signal (SPECTRA needs labeled target data; CrossEarth-Gate needs source labels or target pseudo-labels).
- Computing the signal **once, before** any adaptation training begins, rather than repeatedly during training (CrossEarth-Gate recomputes its signal during training).
- Selecting at **individual transformer-layer** granularity rather than stage (SPECTRA) or module-type (CrossEarth-Gate) granularity.

**Is novelty A) clearly defined, B) partially defined, or C) insufficiently defined?**

**B — partially defined.** The abstract itself already states the correct posture (§6: "not a guaranteed novel contribution... a final targeted novelty audit... is required"). The distinction from the two specific papers checked so far (SPECTRA, CrossEarth-Gate) is real and articulable — it is not vacuous. But:
- That check covered only two papers, found in one later session, not "the latest literature" broadly, as the abstract's own requirement specifies.
- The abstract itself contains no related-work citations at all (§17 lists "Related Work" only as a chapter topic to be filled in later).

Evidence, not judgment: the novelty claim is neither established nor disproven by what currently exists — it is **under-audited relative to what the abstract itself requires**, which is a precise, checkable gap (G-9), not a verdict on whether the idea is or isn't novel.

---

## 9. Claims That Must Be Rewritten

Exact recommended wording (not applied automatically, per instructions):

1. **Current (implicit, via §5 architecture and headline framing):** "DSSA adapts a target domain using unlabeled target data."
   **Recommended:** "DSSA's *layer-selection step* uses only unlabeled target data; the subsequent LoRA fine-tuning step uses labeled target-domain data, as any supervised adaptation would."

2. **Current (§1):** "...substantially reducing trainable parameters and computational cost compared with full fine-tuning and uniform PEFT."
   **Recommended:** "...substantially reducing trainable-parameter count and optimizer/GPU-memory footprint compared with full fine-tuning and uniform PEFT; forward-pass compute is not expected to drop proportionally, since the full frozen backbone is still evaluated on every step."

3. **Current (implicit throughout):** references to "domain shift" and "cross-sensor" used interchangeably.
   **Recommended:** state explicitly, per experiment, which shift type(s) (sensor / geography / season / resolution / atmosphere / spectral) are actually being varied and controlled for, rather than using "domain shift" as a catch-all.

---

## 10. Implementation-Blocking Decisions

Only decisions that must be resolved before any coding begins:

1. Final DSS mathematical definition: formula, pooling, aggregation, normalization (Gap G-3, G-5).
2. CKA: adopt a two-sample-adapted variant, or drop it (🚨 Flag 1).
3. Dataset pair: verify or restrict scope (🚨 Flag 2).
4. Band-alignment strategy, if the eventual pair has mismatched bands (Gap G-8).
5. Add random-K and source-vs-source-null as required baselines/experiments (🚨 Flag 3).
6. Target-side data-split policy: probe / train / validation / test (Gap G-12).
7. K/metric selection protocol: validation-only (Gap G-13).
8. LoRA rank policy and which weight matrices receive LoRA (Gap G-14).

---

## 11. Freeze Candidate

## PROPOSED DSSA RESEARCH SPECIFICATION

- **Problem:** Geospatial foundation-model segmentation accuracy degrades under domain shift (sensor, region, season, resolution, atmosphere, or spectral differences between training and deployment imagery); conventional fixes (full fine-tuning, uniform PEFT) may spend trainable capacity on layers not meaningfully affected by that shift.
- **Input:** Labeled source-domain segmentation data; unlabeled target-domain images for the selection step; labeled target-domain data for the subsequent adaptation step.
- **Backbone:** Prithvi-EO-2.0 (initial choice), frozen except where selectively adapted.
- **Representation:** Per-transformer-layer hidden representations, extracted from the frozen backbone, pooling and aggregation strategy to be finalized (Gap G-3).
- **DSS:** A per-layer statistic quantifying source-vs-target representation drift, computed once, before adaptation, from unlabeled target data and labeled source data — exact formula pending resolution of Flag 1 and Gap G-3/G-5.
- **Layer selection:** Rank layers by (normalized) DSS; select Top-K or threshold; K/threshold protocol chosen on a held-out validation split only (Gap G-13).
- **Adaptation:** LoRA inserted only into selected layers; all other backbone layers remain frozen; segmentation decoder always trainable; rank/matrix policy pending (Gap G-14).
- **Baselines:** Source-only, full fine-tuning, uniform LoRA, adapters, visual prompt tuning (if compatible) — **plus random-K layer selection and a source-vs-source null baseline, pending team approval (Flag 3)**.
- **Evaluation:** Segmentation quality (mIoU, per-class IoU, F1, pixel accuracy); efficiency (trainable parameters, GPU memory, training time, inference time) reported as **separate, distinct quantities**, not bundled (Gap G-15).

This specification is a **candidate**, not yet frozen — see `DSSA_PROJECT_FREEZE.md` for exactly which parts are frozen and which remain open.
