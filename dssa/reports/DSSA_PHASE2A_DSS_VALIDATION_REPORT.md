# DSSA Phase 2A — DSS Extraction and Layer-Selection Validation Report

**No LoRA trained. No segmentation trained. No labels used. No optimizer, no gradients. This report computes and reports numbers only — it does not select a final K, does not claim any layer is "important," and does not claim DSSA works.**

Full artifacts: `dssa/artifacts/dss/phase2a_dss_results.json`, `dssa/artifacts/dss/phase2a_run.log`. Code: `dssa/sanity/run_phase2a_dss.py`, `dssa/sanity/mmd.py`.

---

## 1. Objective

Determine whether the frozen source-vs-target representation-drift procedure (DSS) produces a **stable, well-defined layer-level signal**, meaningfully different from the source-vs-source null, before any adaptation training is attempted. This is a validation of the *mechanism*, not of the *hypothesis* that selective adaptation improves segmentation — that question is out of scope until Phase 2B.

## 2. Frozen DSS Definition Used

Exactly as specified in `DSSA_PROJECT_FREEZE.md` §F/O-C/O-D and `DSSA_IMPLEMENTATION_FREEZE.md` §6 — unmodified:

- Pooling: mean over patch tokens per layer (cls token excluded), one vector per image.
- Source centroid: mean of pooled source vectors.
- Raw DSS: mean cosine distance from each target image's pooled vector to the source centroid.
- Normalization: z-score against a **source-vs-source null distribution**.
- Primary metric: **cosine**. MMD: comparison/ablation only, never substituted as primary.
- Tie-breaking: descending normalized DSS, ties within 1e-6 broken by lower layer index.
- Checkpoint, Strategy C coefficients, T=1, band mapping: all reused unchanged from the already-fitted, already-frozen Phase 1B artifacts. **Strategy C was not refit.**

**One definition, implemented more fully than in Phase 1B:** the frozen spec (§O-C) calls for the null to be a *bootstrap-estimated distribution*, not a single draw. Phase 1B's sanity check used a single null draw as an explicitly-flagged simplification (too little data at the time to bootstrap meaningfully). This phase implements the full bootstrap: 40 resampled 8-vs-8 splits of a 16-file null pool per probe, per layer, giving a real mean/std to z-score against. This is not a new criterion — it is the already-frozen definition, executed to its actual specification now that real data volume permits it.

## 3. Dataset / Sample Definition

Three **deterministic** probe configurations, fixed before any results were seen, testing stability along two independent axes:

| Probe | Source (Potsdam) | Target (Vaihingen) | Null pool (Potsdam, disjoint from source) | Crop location |
|---|---|---|---|---|
| **A** | files[0:16] | files[0:16] | files[16:32] | top-left (0,0) |
| **B** | files[0:16] *(same as A)* | files[0:16] *(same as A)* | files[16:32] *(same as A)* | **bottom-right** (per-image `H−224, W−224`) |
| **C** | **files[6:22]** *(shifted)* | **files[6:22]** *(shifted)* | **files[22:38]** *(remaining)* | top-left (0,0) |

Probe A vs. B isolates **spatial crop-location sensitivity** (same files, same content pool, different 224×224 window). Probe A vs. C isolates **file/content sensitivity** (same crop rule, different tiles). All crops are native-resolution, no resizing — the same fixed-window tiling used in Phase 1B. 144 real forward passes total (48 per probe), zero labels loaded, zero gradients computed.

## 4. 24-Layer DSS Results (raw)

Full per-layer raw DSS, null mean/std, and normalized DSS for all three probes are recorded in Section 8 of `phase2a_dss_results.json` and reproduced in full below (nothing hidden, including the negative values in Probe B):

**Probe A** — raw DSS ranges 0.145 (L23) to 0.245 (L0); broadly declines with depth but not monotonically (local peaks around L12–L14 and L9–L11).
**Probe B** — raw DSS ranges 0.127 (L23) to 0.228 (L0); a similar declining-with-depth shape to Probe A, but the *null mean is larger than the raw DSS at every single layer* (see Section 5).
**Probe C** — raw DSS ranges 0.199 (L23) to 0.321 (L0); uniformly higher in absolute terms than A and B, same declining shape.

(Full 24-row tables for all three probes are in the JSON artifact — omitted here in full for length, quoted selectively in Sections 5–7 where the pattern matters.)

## 5. Source-vs-Source Null

The null (40-resample bootstrap, per layer, per probe) is **not flat across depth** — it shrinks substantially with layer depth in every probe. Probe A: null mean falls from 0.202 (L0) to 0.085 (L23); null std falls from 0.041 (L0) to 0.016 (L23). Probes B and C show the same declining-null-variance shape.

**This is a load-bearing, must-flag observation:** later layers have a *smaller baseline null* (lower natural source-vs-source spread), not necessarily a *larger raw cross-domain drift*. In Probe A, raw DSS at L23 (0.145) is actually **lower** than at L0 (0.245) — yet L23's normalized score (+3.76) is far higher than L0's (+0.99), purely because L23's null is so much smaller. **The normalized-DSS ranking is therefore driven substantially by how naturally stable/noisy each layer is (the null), not purely by the magnitude of cross-domain drift.** This is exactly the kind of confound flagged as a risk in `DSSA_ABSTRACT_GAP_ANALYSIS.md` (RM-2/RM-3) — here it manifests as *late layers being naturally low-variance*, which is a different specific mechanism than originally speculated (high-variance layers dominating), but the same category of risk: the null-normalization step is doing real, non-trivial work in determining the final ranking, and that work is not obviously "domain sensitivity."

## 6. Normalized DSS

Reported in full in the JSON artifact. Two things stand out, neither hidden:

- **Probes A and C**: normalized DSS is positive at every layer, generally increasing with depth, peaking around L18–L23 (up to +3.76 in A, +5.29 in C).
- **Probe B**: normalized DSS is **negative at every single layer** (range ≈ −0.32 to −1.18). At this crop location, source and target pooled representations are *closer to each other* than two random source-only splits are to each other — the raw target-vs-source distance is smaller than the null mean throughout. This was not filtered, adjusted, or explained away — it is reported exactly as computed. A plausible but **unverified** explanation: the bottom-right region of these specific tiles may contain more visually similar content across the two cities than the top-left region does (real content effect), or the null estimate itself may behave differently at that crop location. This was not investigated further, per instruction not to introduce new methodology in response to an unexpected result — it is recorded as an open question (Section 15).

## 7. Layer Ranking

Per-probe rankings (most-to-least sensitive by normalized DSS), deterministic tie-break applied (no ties within 1e-6 tolerance occurred in this run):

- **Probe A:** `[23, 22, 19, 21, 20, 18, 17, 16, 11, 10, 15, 14, 13, 12, 9, 8, 1, 7, 6, 2, 0, 5, 3, 4]`
- **Probe B:** `[23, 22, 19, 18, 20, 21, 17, 10, 16, 11, 1, 15, 14, 12, 13, 9, 0, 2, 8, 7, 6, 5, 3, 4]`
- **Probe C:** `[22, 20, 19, 21, 23, 18, 17, 16, 10, 15, 7, 11, 6, 8, 9, 14, 13, 12, 1, 5, 2, 3, 4, 0]`

**This is a ranking, not a claim of importance.** No layer is described here as "important," "optimal," or "should be adapted" — that determination is explicitly out of scope for this phase.

## 8. Stability Analysis

**Top-6 (illustrative K=6) is identical across all three probes:** `{18, 19, 20, 21, 22, 23}` in every probe. Pairwise Jaccard overlap A–B, A–C, B–C = **1.0** in all three comparisons.

**🚨 This must be stated plainly, not buried:** `{18,19,20,21,22,23}` is *exactly* the "late" fixed-position control defined in Section 11 (the last 6 layers, by construction). **In this data, at this K, the cosine-DSS-based Top-K selection is indistinguishable from a naive "always pick the last 6 layers" heuristic.** Perfect Top-K stability across probes is a genuine positive finding for the *reproducibility* of the selection step — but it does **not**, by itself, provide any evidence that DSS is selecting layers for a domain-sensitivity reason rather than a simple, fixed, depth-based reason. Distinguishing these two explanations requires an actual adaptation experiment comparing DSSA against the Late control specifically — this is now the single most important comparison for Phase 2B, elevated in priority by this finding.

**Rank stability is not uniform across depth.** Layers 17 and 19 have *perfectly* stable rank position across all three probes (std = 0.0). Layers 22–23 are nearly perfectly stable (std ≈ 0.5–1.9). By contrast, early/middle layers show substantial rank churn: L6, L7 range over 8–9 rank positions across the three probes (std ≈ 3.4–3.9), and L0, L1 are similarly unstable. **The layers that dominate the Top-K are also the most rank-stable ones; the layers DSSA would *not* select under this K are also the least reproducibly ranked.** This is a real, structural finding worth carrying into any future K-sensitivity analysis.

**Absolute magnitude/sign is not stable across crop location** (Section 6, Probe B) even though the *relative ordering* among layers largely is. This dissociation — unstable magnitude, stable top-end ranking — is reported as observed, not explained.

## 9. Random-K Control

Definition only (fixed seed 42, K=6): **`[0, 3, 7, 8, 19, 20]`**. Only layer 19 overlaps with the cosine Top-6. This is the layer set that will need to be run through actual LoRA adaptation in Phase 2B to test whether DSS-guided selection outperforms an arbitrary same-size selection — not run here.

## 10. Lowest-DSS Control

Definition only, from Probe A's ranking (bottom 6): **`[0, 2, 3, 4, 5, 6]`** — notably, this is close to (though not identical to) the "early" control below, since Probe A's lowest-normalized-DSS layers are concentrated at the start of the network, the mirror image of the late-layer-dominated Top-6.

## 11. Early / Middle / Late Controls

Fixed by depth position, K=6: **Early** `[0,1,2,3,4,5]`, **Middle** `[9,10,11,12,13,14]`, **Late** `[18,19,20,21,22,23]`. As noted in Section 8, **Late is identical to the cosine Top-6 in this run.**

## 12. K=0 and K=all

**K=0:** empty layer set — the decoder-only degenerate baseline (per `DSSA_PROJECT_FREEZE.md` §G, a legitimate control, not an error state). **K=all:** all 24 layers, `[0..23]` — equivalent in layer coverage to uniform LoRA.

## 13. MMD Comparison

Computed for Probe A only, biased RBF-kernel MMD², median-heuristic bandwidth (comparison metric, never substituted for cosine as primary):

**MMD Top-6:** `[3, 4, 5, 6, 11, 19]` — versus **cosine Top-6:** `[18, 19, 20, 21, 22, 23]`. **Overlap: exactly 1 layer (19).** Rank-order correlation between the two full 24-layer rankings: **−0.146** (essentially uncorrelated, slightly negative).

**This is a significant, not-to-be-downplayed finding.** The two candidate metrics frozen for this project (§N-1) produce **nearly disjoint** pictures of which layers are most domain-sensitive in this data — MMD's top layers cluster in the early-middle of the network (3–6, 11), almost the opposite region from cosine's late-layer cluster. Neither metric is favored or selected here; this result is reported exactly as the ablation instruction required, without picking "the more convenient" one. It means: **the choice of DSS metric is highly consequential to the resulting layer selection, and this has not been resolved.**

## 14. Red-Team Interpretation

Read against `DSSA_ABSTRACT_GAP_ANALYSIS.md` and `DSSA_RED_TEAM_REPORT.md` directly:

- **RM-2 / "DSS may reflect general layer variance, not domain sensitivity"** — partially substantiated, in a specific form: Section 5 shows the normalized ranking is heavily shaped by each layer's *null* (baseline) variance shrinking with depth, not purely by raw drift magnitude. Not disproven, not confirmed as fatal — a real, now-quantified mechanism, not a hypothetical one.
- **"Does DSS just rediscover a fixed early/middle/late pattern?" (Gap G-10/G-16, the random-K/fixed-position controls)** — Section 8's finding (cosine Top-6 = Late control, exactly, in every probe) is direct evidence that **this specific risk is live, not merely theoretical**, in the current data/config. It does not prove DSS is *only* rediscovering depth — but it means this data cannot currently distinguish the two explanations, and Phase 2B's Late-vs-DSSA adaptation comparison is now the load-bearing experiment, not an optional extra.
- **CKA/metric-choice risk (Flag 1, deferred)** — not directly tested (CKA remains deferred, per freeze), but the cosine-vs-MMD near-zero correlation (Section 13) shows the *general* concern — that metric choice could substantially change conclusions — is real and observable even between the two metrics that *are* implemented.
- **Random-K as the essential control (Flag 3)** — reaffirmed: Section 9's Random-K set shares only 1 layer with cosine's Top-6, underscoring that "was the selection non-arbitrary" is a genuinely open, unanswered question at this stage, not a formality.

## 15. Limitations

- Sample sizes are small (16 source / 16 target / 16 null files per probe, one crop each) — appropriate for a mechanism-validation phase per the frozen "small batch" sanity-check spec, but not large enough to treat any single probe's exact numbers as a stable population estimate.
- Probe B's uniformly negative normalized DSS is reported but not explained — a genuine open question, not resolved here, and not something this phase is authorized to chase by inventing new methodology.
- Only one crop per file was used; multi-crop-per-file averaging was not attempted (would require a documented, pre-registered protocol of its own, not introduced ad hoc here).
- CKA remains deferred (frozen decision, unchanged) — no CKA-vs-cosine comparison exists yet.
- Bootstrap null uses 40 resamples from a 16-file pool (limited by real file availability, not by choice) — a larger null pool, if more data becomes available, would tighten these estimates.
- These numbers describe **this specific probe design** on **this specific dataset pair**. Nothing here has been tested for generalization to a different domain shift (that is Experiment E10 / cross-domain validation, not run).

## 16. Decision Gate for Phase 2B

**The DSS mechanism is well-defined, computable, deterministic, and produces a finite, non-degenerate, reproducible Top-K ranking under the probe variations tested here (Jaccard = 1.0 across all three).** That is a genuine, positive, mechanism-level result: the pipeline validated in Phase 1B (GREEN) extends to producing a *stable selection signal*, not just non-degenerate representations.

**This does not establish that DSSA works, and two specific findings raise the stakes on the controls already planned for Phase 2B, rather than lowering them:**

1. The stable Top-6 coincides exactly with the naive Late-layer control in every probe tested. **The Late-vs-DSSA-selected adaptation comparison is now the single most decisive experiment remaining** — without it, "DSS selects sensible layers" and "DSS just picks late layers" are indistinguishable claims given current evidence.
2. Cosine and MMD rankings are nearly uncorrelated. Any future claim about "which layers matter" must specify which metric it used, and the metric-ablation experiment (E9, already planned) should be treated as similarly decisive, not a minor sensitivity check.

**Recommendation, not a decision:** proceeding to Phase 2B's controlled adaptation experiments is reasonable *specifically because* these open questions can only be resolved by running them — Phase 2A has done what a mechanism-validation phase can do (confirm the signal is real, computable, and reproducible) and has surfaced, honestly, exactly which downstream comparisons matter most. It has not shown DSSA is right, and it has not shown DSSA is wrong. **No GREEN/YELLOW/RED verdict is issued for this phase — that scale was defined for pipeline-validity checks (Phase 1/1B), not for a scientific-mechanism validation, and applying it here would imply a pass/fail judgment about DSSA's hypothesis that this phase is explicitly not authorized to make.**

**Stopping here, per instruction. Phase 2B (any LoRA training, segmentation training, or performance experiment) is not begun and requires separate, explicit authorization.**
