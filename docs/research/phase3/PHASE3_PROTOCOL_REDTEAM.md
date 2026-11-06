# Phase 3: protocol red-team (revision 1 of the 2026-11-06 drafts)

Scope: a documentation and read-only audit.
- No training, inference experiment or label access.
- The only computation was arithmetic on stored Phase 2D outputs (`gate2_analysis.json`,
  `frozen_rankings.json`, run timing records, and the tile shapes of non-test tiles from
  `dataset_integrity_raw.json`).
- The original six documents are kept unchanged; revisions are in `PHASE3_EXPERIMENTAL_PROTOCOL_v2.md`,
  `PHASE3_DECISION_REGISTER.md` and `PHASE3_EXECUTIVE_RECOMMENDATION_v2.md`.

## Evidence computed for this review (reproducible from stored outputs)
- **E1. Runtime.** Phase 2D runtime records, means over 3 seeds:
  - training seconds (excluding validation): K0 761, L0 1,521, L10 1,184, L19 900, L21 829; the
    single-block mean is 1,145;
  - total training 23.5 h over 75 runs;
  - validation 729 s per run = **10 evaluations** (steps 200–2,000) × ≈ 73 s on **22.7 MP** of
    validation tiles, which is **≈ 3.2 s per MP**;
  - validation was **≈ 39%** of total compute.
- **E2. Seed noise.** Per-block seed SD of utility: median **0.0136**, range 0.0048–0.0212, pooled
  0.0141. (σ_c = 0.0099 is the two-way residual for *paired between-arm* differences; the per-block
  utility SD also contains seed-by-arm variation.)
- **E3. The frozen quadratic depth prior** from Phase 2D:
  p(ℓ) = −1.8386e-4·ℓ² + 4.9992e-3·ℓ − 4.1343e-4. R² 0.82; peak at ℓ* = 13.6.
- **E4. Residual association against the frozen prior,** r_res = Spearman(s, z(Ū) − z(p)), on the
  Phase 2D data:

  | Selector | r_res |
  |---|---|
  | DSS-R2 | −0.02 |
  | **RAW_R2** | **−0.27** |
  | Middle | −0.19 |
  | Late | −0.11 |

  RAW_R2's earlier "partial 0.494" was produced by **linear** depth control. It does not survive a
  non-linear prior.
- **E5. Simulated stability of the screening statistics** (Gaussian seed noise at the Phase 2D
  per-block SD, 4,000 replicates):
  - SD of Spearman(DSS-R2, Ū): 0.126 (3 seeds), 0.107 (5), 0.086 (10);
  - SD of r_res: 0.15, 0.14, 0.12;
  - **an uninformative selector passes r_res ≥ 0.30 in 7.2% (3 seeds), 7.6% (5) and 8.4% (10) of
    replicates**. Extra seeds do not reduce the false passes, because the limit is the finite,
    depth-structured set of 24 blocks.
- **E6. Leave-one-seed-out on Phase 2D.**
  - R2 Spearman: 0.34, 0.36, 0.54.
  - Middle: 0.66, 0.69, 0.62.
  - The top-5 sets overlap substantially: {16, 13, 11, 17, 8}, {13, 17, 16, 18, 8} and
    {11, 16, 15, 19, 13}.

## Issue 1: Potsdam independence
- **Original issue.** The v1 protocol called Vaihingen → Potsdam a "primary independent" setting.
- **Evidence.** The Gate 0 DSS used Potsdam imagery:
  - all 38 tiles for the radiometric fit and the source-vs-source null;
  - 16 tiles for the R2 centroid;
  - pooled features of all 38 are stored in `gate0/features_pre.npz`.

  The selector candidates were also designed with full knowledge of the Phase 2D results on the same
  pair.
- **What is new:**
  - Potsdam **labels**, never opened;
  - Potsdam as the **adaptation target**: a new training objective and a new utility oracle;
  - new Potsdam validation and test tiles as evaluation units;
  - the opposite resolution direction (9 → 5 cm).
- **What is not new:**
  - the Potsdam images;
  - the domain pair;
  - the frozen backbone features of those images;
  - the investigators' knowledge of the pair.
- **Revised decision.** Call it **"a new-target, new-label replication within the ISPRS pair"**, not an
  independent image-domain replication.
  - **LoveDA becomes mandatory** for any claim of generalisation beyond the ISPRS pair and for any
    Path 1 (method) claim.
  - Without LoveDA, the paper is restricted to "both directions of one dataset pair".
- **Remaining uncertainty.** LoveDA's RGB-only band mapping changes the Prithvi input contract, so a
  LoveDA failure may reflect the mapping rather than the selector.
- **Approval required:** yes (LoveDA licence and download).

## Issue 2: Fisher and LogME definitions
- **Original issue.** v1 proposed both "the Phase 2D K0 decoder checkpoint" and "a new Potsdam K0
  warm-up" without saying which applies where.
- **Evidence.**
  - LoRA initialises B = 0 with a seeded A (`train/lora.py`), so ∂L/∂A = 0 at initialisation and
    gradient information exists only through B.
  - The **best** checkpoints were chosen with validation labels; the **final** (step 2,000) checkpoints
    were not.
- **Revised decision** (fully specified in protocol v2 §4):
  - **Settings.** On Potsdam (prospective), Fisher uses the **final** checkpoint of the **new Potsdam
    K0 run** for each seed. On Vaihingen (development only), it uses the Phase 2D K0 **final**
    checkpoints.
  - **Model.** LoRA is inserted in all 24 blocks with that seed's LoRA-A initialisation and B = 0.
  - **Scores.** Fisher_ℓ = mean over 64 training batches (same data stream as seed s) of the summed
    squared gradients with respect to B_q and B_v of block ℓ, using **target-train labels only**. It is
    averaged over the 3 seeds.
  - **LogME is decoder-free.** It uses frozen backbone patch tokens of block ℓ for 2,000 random 224²
    crops from the target-train tiles (probe tiles included: they are training tiles). Labels are
    16×16 patch majority classes, keeping patches with purity ≥ 0.8. Stratification and the cap of
    20,000 patches are fixed in advance.
  - Validation and test labels are never read by any selector.
- **Remaining uncertainty.** Fisher depends on the random A; averaging over seeds mitigates this.
  LogME on patch tokens with a 1,024-dimensional feature is a modelling choice. SPECTRA's purity
  threshold is unreported.
- **Approval required:** yes (part of the protocol).

## Issue 3: Stage D run accounting
- **Original issue.** v1 estimated "≈ 85 runs, 60–70 h" with an inconsistent formula.
  - It omitted the LogME-3 arm.
  - It used 5 random draws × 5 seeds (25 runs).
  - It did not state that the K0 baseline can be reused.
  - It **omitted test-evaluation compute entirely**.
  - It assumed 10 evaluations per run, as in Phase 2D.
- **Evidence:** E1. With **one evaluation at step 2,000**, a run costs training(earliest adapted block)
  + 922 s (8 Potsdam validation tiles × 36 MP × 3.2 s/MP) + 90 s overhead.
- **Revised decision.** An explicit table in protocol v2 §6. Stage D = **77 new runs, ≈ 47.6 h**,
  reusing 3 K0 runs from Stage C. The test opening costs a further ≈ 25.6 h.
- **Remaining uncertainty:**
  - the overhead factor for uniform LoRA on 24 blocks (assumed 1.15 × L0);
  - Potsdam evaluation I/O and memory on 6000² tiles;
  - the caching of 20 Potsdam training tiles (≈ 2.2 GB uint8) against the 11.5 GB footprint limit
    (Phase 2D peak 8.3 GB). This is new risk R22.
- **Approval required:** yes (budget).

## Issue 4: Statistical design
- **Original issue.** v1's screening rule (partial ρ ≥ 0.30 with a seed-resampled CI) used linear depth
  control, treated 24 blocks as if they supported n = 24 inference, and relied on a 3-seed bootstrap
  that has only 10 distinct resamples.
- **Evidence:** E4 (linear control is inadequate), E5 (a ~7–8% false pass per candidate regardless of
  seeds; about 20% across three candidates) and E6.
- **Revised decision:**
  1. **Blocks are not independent observations.** No p-values over blocks. Rank statistics are
     *descriptive* of a fixed set of 24 blocks; their uncertainty comes from measurement noise (seeds,
     tiles), not from sampling blocks.
  2. **Depth control is a frozen, non-linear prior** (E3), applied unchanged with no refit on new data.
     The screening statistic is r_res = Spearman(s, z(Ū) − z(p)) together with top-3 regret relative to
     the prior's top-3 {14, 13, 15}.
  3. **Uncertainty is reported separately:**
     - *training seed* (3-seed leave-one-out, plus a parametric resample using the new setting's pooled
       per-block seed SD);
     - *validation tile* (bootstrap of the 8 validation tiles conditional on the trained models);
     - *ranking* (both, reported per component).
  4. **The screening gate is acknowledged as non-inferential,** with a known ~7% per-candidate false
     pass. It only decides which single candidate enters Stage D. Inference rests on (a) Stage D paired
     contrasts with 10 seeds, evaluated on the **Potsdam test**, and (b) for any method claim, the
     candidate must also pass the gate on **LoveDA**. Two independent gates give about 0.5% joint false
     pass.
  5. **Fewer candidates.** Label-free: DSS-R2 (original) and GSD-perturbation sensitivity (new).
     Input-output similarity and activation norm are eligible literature baselines with no novelty
     claim. RAW_R2 and MMD are dropped as candidates (E4) and reported descriptively.
- **Stronger alternative considered.** Five seeds in Stage C (+50 runs, ≈ +30 h) improve r_res
  precision only marginally (SD 0.15 → 0.14, E5) and do not reduce false passes. **Rejected.** Seeds go
  to the Stage D confirmatory arms instead.
- **Remaining uncertainty.** With one or two settings, between-setting variance cannot be estimated.
  Generalisation claims stay qualitative ("replicated in two settings").
- **Approval required:** yes.

## Issue 5: Test-opening rules
- **Original issue.** v1 proposed opening the Vaihingen locked test for "Stage D configurations", but
  Stage D trains on **Potsdam**, so Vaihingen test tiles cannot evaluate those models. v1 also called
  both tests "confirmatory" without precedence.
- **Revised decision** (protocol v2 §9):
  - **The Potsdam test is the only confirmatory test.** It is opened once, after all Stage D runs
    finish, on all 80 Stage D models, with a hashed script and a pre-registered analysis.
  - **The Vaihingen locked test is secondary.** It is opened once, on the 75 existing Phase 2D final
    checkpoints, to check the Phase 2D single-block findings on held-out tiles. It is opened only
    **after** the Stage B scores and all Stage C and D thresholds are hashed, so it cannot influence
    selector design.
  - **Neither test may select a method, a K, a threshold or a candidate.**
  - **Contradictions** between tests are reported, and the confirmatory claim follows the Potsdam
    test.
  - **Accidental early access** downgrades that setting to development; claims then need LoveDA's
    held-out split.
- **Approval required:** yes.

## Other findings
- **F1.** The v1 executive recommendation named RAW as "the strongest exploratory label-free
  candidate". This is **withdrawn** (E4).
- **F2.** Evaluating only at step 2,000 removes "best checkpoint" selection by validation, which
  reduces validation-label leakage into checkpoint choice. This is a deliberate improvement over Phase
  2D, where the primary metric already used the step-2,000 checkpoint.
- **F3.** The radiometric transform for Vaihingen → Potsdam: refit it on the new source (Vaihingen
  training images only) to keep the "source-fit-only" principle. Using Potsdam images (the target)
  would change that principle. This needs a decision (D4 in the register).
