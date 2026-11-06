# Phase 3: research direction

Labels: **[V]** verified evidence; **[L]** literature; **[H]** hypothesis; **[R]** recommendation.

## 1. Revised research question
[R] **Can the usefulness of adapting a given transformer block under domain shift be predicted before
fine-tuning, from frozen representations or lightweight calibration, better than by block depth
alone?**

Sub-questions:
- **RQ1.** In a new, independent setting, how much of single-block LoRA utility is explained by a
  pre-registered non-linear depth prior?
- **RQ2.** Does any **label-free** signal add predictive value beyond that prior?
- **RQ3.** Do cheap **label-using** signals (LogME, Fisher, relative gradient norm) add value beyond it,
  and how do they compare with label-free signals?
- **RQ4.** Do single-block utilities predict **joint** (K > 1) adaptation outcomes?
- **RQ5.** Is any selector advantage real in measured quality *and* cost, against uniform LoRA at a
  matched parameter budget?

Scope statement for every paper: **target-supervised segmentation with label-free (or explicitly
label-using) layer selection.** It is not unsupervised domain adaptation, not domain generalisation, and
not cross-domain zero-shot evaluation.

## 2. Competing explanations
| H | Statement | Supporting evidence | Contradicting evidence | Falsifying experiment | Label-free? | Practical? | Literature |
|---|---|---|---|---|---|---|---|
| A | Utility is mainly a (non-linear) function of depth | [V] quadratic R² 0.82; the pre-registered Middle rule had Spearman 0.632, the best of all rules; R2 ≈ depth (ρ 0.94) | [V] Monotone depth (Late) gives only 0.422; seed agreement W = 0.73, so some idiosyncrasy remains | In a new setting, a **frozen** depth prior (fitted on Phase 2D only) fails to predict utility, e.g. rank correlation < 0.3 or a different peak location | Yes (trivially) | Free | Surgical FT [L]: the best layers depend on shift type, **contradicting a universal depth prior** |
| B | Source-target discrepancy predicts utility **after** depth control | [V] RAW_R2 partial 0.494 (exploratory; one of 6 selectors) | [V] R2 partial 0.076; MMD −0.077; R2 top-k ≈ random | The pre-registered depth-residualised discrepancy has a non-linear-depth partial ρ ≤ 0.1 in the new setting | Yes | Cheap (one forward pass) | DDC [L] used discrepancy for placement; no depth-controlled test found |
| C | Within-domain sensitivity or input-output transformation predicts utility | None in DSSA | None in DSSA | Same test as B | Yes | Cheap | LS-LoRA, the LREC 2026 inter-layer-cosine work, Act-LoRA [L]: already used in NLP; Act-LoRA has a random-parity critique |
| D | Task-gradient or Fisher information predicts utility | None in DSSA | None in DSSA | A cheap Fisher or LogME per block (target-train labels only) fails to beat the depth prior | **No** (target labels) | Cheap if computed from the existing K0 decoder | CrossEarth-Gate (Fisher, during training), SPECTRA (LogME), Surgical FT (Auto-RGN) [L] |
| E | Interactions matter: single-block utility does not predict joint utility | [V] Phase 2C K = 2 runs exist (single seed, 5 runs); not analysed for this | — | Joint K = 3 of the top-3 single blocks is no better than the best single block, or the ranking of K = 3 sets disagrees with the summed single utilities | n/a | Moderate | General PEFT literature; not tested in DSSA |
| F | Utility depends on dataset pair, backbone or decoder | [V] D5 (L23-only decoder), D6 (scale mismatch) | — | The utility curve shape replicates across settings or decoders (so F is weak) or does not (F holds) | n/a | Expensive | Surgical FT; PEFT-for-GFM benchmark [L] (the decoder dominates) |
| G | No single label-free signal predicts utility reliably | [V] Phase 2D; [L] Act-LoRA random-parity report; CKA-gap non-prediction | — | Some label-free signal passes the pre-registered criteria in ≥ 2 independent settings | — | — | — |

[R] Treat **A vs B/C**, controlling for A, as the primary scientific test. Treat **D** as the
label-using reference point, **E** as the bridge to practical value, and **F and G** as what the
cross-setting replication decides.

## 3. Candidate selector signals
Notation:
- Block ℓ ∈ {0, …, 23}.
- f_ℓ(x) ∈ ℝ^1024: the per-image pooled token embedding at the output of block ℓ. This is the
  "pre-norm, 9-crop file vector" representation already used in Gate 0 (`gate0_dss.py`); its exact
  tensor is to be re-confirmed in Stage A.
- S = source images; T = target-probe images (unlabelled training subset).
- One forward pass over S ∪ T yields every label-free signal below.

| # | Signal | Definition | Labels? | Backward pass? | Cost | Depth confound | Status |
|---|---|---|---|---|---|---|---|
| 1 | DSS-R2 (original) | z_ℓ = (D_ℓ − μ_null,ℓ)/σ_null,ℓ, with D_ℓ = mean_{t∈T} [1 − cos(f_ℓ(t), c_S,ℓ)] and c_S,ℓ = the normalised mean of f_ℓ over 16 source tiles; null = matched 16-vs-5 source draws | No | No | 1 forward pass of 21 tiles × 9 crops; seconds to minutes | Severe (ρ 0.94) | Exists (frozen) |
| 2 | Depth priors | Late: s = ℓ. Early: s = −ℓ. **Middle (pre-registered): s = −\|ℓ − 11.5\|**. Plus a **frozen quadratic prior** fitted on Phase 2D utilities **only** and applied unchanged to new settings | No | No | Free | Is the confound | Middle is pre-registered (D1); the quadratic prior is new |
| 3 | Depth-residualised DSS | Residual of z_ℓ after regressing on depth and depth² across ℓ (fitted on the **scores**, never on utilities) | No | No | Free given #1 | Removed by construction, but the residual may be noise | New combination, trivial: test only as a falsifier of B |
| 4 | MMD / RAW distance | MMD² (RBF, median bandwidth) and RAW_R2 (unnormalised D_ℓ) | No | No | As #1 | MMD weak; RAW low-to-moderate | Exist (frozen). **RAW is the only label-free signal with a notable depth-adjusted association (0.494, exploratory)**, so it is the primary label-free candidate |
| 5 | Input-output similarity | 1 − mean_x cos(h_ℓ^in(x), h_ℓ^out(x)) over target-probe tokens | No | No | 1 forward pass | Likely strong (deeper blocks change less or more systematically) | **Established** (LS-LoRA, LREC 2026): include as a literature baseline, not a contribution |
| 6 | Representation statistics | Activation norm (Act-LoRA); effective rank of the target-probe token covariance | No | No | 1 forward pass | Likely strong | Activation norm established; effective rank: a minor variant |
| 7 | Perturbation sensitivity **[H]** | E_x ‖f_ℓ(g(x)) − f_ℓ(x)‖ / ‖f_ℓ(x)‖ for source images, with g = a **known domain-shift operator**: ground-sampling-distance resampling (5 → 9 cm and back) and a radiometric gain change | No (and no target data needed) | No | 2 forward passes per perturbation | Unknown | Not found in the literature read; plausible but **speculative**. Include at most one operator (GSD resampling) to avoid metric fishing |
| 8 | Fisher / gradient (label-using) | For LoRA-B of block ℓ (A is random and B = 0 at init, so ∂L/∂A = 0), with the **Phase 2D K0 decoder checkpoint** fixed: F_ℓ = mean over batches of ‖∂L/∂B_ℓ‖² on **target-train** batches; also Auto-RGN-style ‖∇‖/‖θ‖ | **Yes** (target train) | Yes | ~50–100 forward+backward batches per block-set; minutes to an hour | Unknown | Established (CrossEarth-Gate, Surgical FT); needed as the label-using reference |
| 9 | LogME per block (label-using) | LogME(f_ℓ(X_probe), Y_probe) with pixel or patch labels pooled to patches | **Yes** | No | 1 forward pass + LogME | Unknown | Established (SPECTRA uses it per stage) |
| 10 | Random | Uniform over blocks (≥ 5 draws, fixed seeds) | No | No | Free | None | Required baseline |
| 11 | Middle, Late, Early | As in #2 | No | No | Free | — | Required baselines |

**Rules for candidate signals:**
- **No composite scores.** A combination is allowed only if it is pre-registered with a stated reason
  and scored as one additional candidate.
- **Candidate count.** At most **3 label-free candidates** (RAW, #3 residual DSS, #7 GSD perturbation)
  plus the established baselines (#1, #5, #6) and the label-using references (#8, #9). This limits the
  multiple-comparison burden.

## 4. Recommended scientific contribution
[R] **"Is it depth? A pre-registered, oracle-validated evaluation of where to place LoRA in a
geospatial foundation model under domain shift."**
- **Core.** Phase 2D plus one independent replication: the single-block utility oracle, a
  depth-controlled test of label-free and label-using selectors, and joint K = 3 vs matched-budget
  uniform LoRA.
- **Method claim (conditional).** Only if a label-free candidate passes the pre-registered criteria in
  both settings.

## 5. Publication strategies
| Path | Novelty potential | Required experiments | Main risks | Contribution | Likely rejection reasons | Venue categories |
|---|---|---|---|---|---|---|
| **1. New method** (a validated label-free selector) | Moderate if it works; the space is crowded (§2 of the literature audit) | Stages A–E incl. two settings, joint K, cost measurements, ideally 2 backbones | **High chance of a null result** (Phase 2D prior); appears incremental next to CrossEarth-Gate and SPECTRA | A practical selector | "Gains within noise"; "depth explains it"; "one backbone"; "uniform LoRA at matched budget is as good" | RS journals (IEEE TGRS/JSTARS, ISPRS JPRS); CV main venues only with strong multi-setting results |
| **2. Systematic empirical study** | Moderate: the depth-controlled, oracle-based evaluation of selectors for a GFM is under-reported | Stages A–D on ≥ 1 independent setting + the Phase 2D data; label-free vs label-using comparison | Seen as "negative result only"; limited to 1–2 settings and 1 backbone | Evidence about whether layer-selection signals carry information beyond depth | "Too narrow"; "known that layers differ"; insufficient settings | RS journals and letters (IEEE GRSL, JSTARS); EarthVision-type CV workshops; negative-results or reproducibility tracks |
| **3. Broader framework** (selection + rank allocation + domain modules) | Low unless the components are individually validated; directly overlaps CrossEarth-Gate and SPECTRA | Everything above + rank allocation + module types | Complexity without evidence; direct comparison with stronger, better-resourced methods | Unclear | "Engineering combination of existing ideas" | Not recommended |

[R] **Primary: Path 2, with Path 1 nested as a pre-registered hypothesis.** If a label-free selector
passes in both settings, the paper becomes a method paper.
[R] **Fallback: a short Path-2 paper or letter** on Phase 2D + one replication (RQ1–RQ3 only), if
compute or time does not allow Stage D.
