# Phase 3: current-state audit

Date: 2026-11-06. Read-only audit: no training, no inference experiment, no access to locked test
data, and no implementation change. Labels used in this document:
- **[V]** verified from primary project evidence, with the file reference given;
- **[D]** a discrepancy between sources;
- **[U]** could not be verified.

## 1. Repository and evidence base
- [V] Git: `main` = `807b187` (pushed to the private `origin`), 21 commits. The only untracked file is
  `docs/MID_PHASE_REVIEW_SCRIPT.md`. The local branch `research-red-team` (`f56588b`) holds a
  pre-implementation red-team report dated Sept 2026; it is not merged.
- [V] Evidence was read from:
  - `dssa/phase2d/*.py`: `gate2_analysis.py`, `oracle_analysis.py`, `gate0_dss.py`, `common.py`,
    `run_one_v2.py`
  - `dssa/train/lora.py`
  - `dssa/config/phase2b_training_protocol.json`
  - `dssa/artifacts/phase2d/gate2/gate2_analysis.json` and `GATE2_FINAL_REPORT.md`
  - `PILOT_STATISTICAL_AUDIT.md`
  - `dssa/artifacts/phase2d/gate0/frozen_rankings.json`
  - `dssa/artifacts/splits/vaihingen_target_split_manifest.json`
  - `dssa/artifacts/radiometric_transform.json`
  - manifests v1–v12
  - `dssa/phase2d/PHASE2D_ADDENDUM*.md`
  - `DSSA_PROJECT_FREEZE.md`, `DSSA_IMPLEMENTATION_FREEZE.md`, `DSSA_ABSTRACT_GAP_ANALYSIS.md`
  - `DSSA_Final_Project_Abstract.pdf`
  - `docs/organization/04_VERSION_REGISTER.md`

## 2. Experimental setup
| Item | Status | Evidence |
|---|---|---|
| Backbone Prithvi-EO-2.0-300M, 24 blocks, 303,886,336 frozen backbone parameters | [V] | `train_result.parameter_counts` in run results; `common.py` |
| Potsdam (source) → Vaihingen (target), IRRG | [V] | Split manifest; `gate0_dss.py` |
| LoRA rank 8 on the **Q and V slices of the fused `qkv` linear**; 32,768 trainable parameters per block; B initialised to zero | [V] | `train/lora.py` lines 2–49 |
| Decoder reads the **final block (L23) only**: 4-block conv upsampler to 6 classes, 2,766,726 parameters | [V] | `DSSA_PHASE2B_B_TRAINING_PROTOCOL_FREEZE.md`; parameter counts |
| Single-block (K = 1) oracle; seeds 1000, 2000, 3000 | [V] | `common.PILOT_SEEDS`; manifests |
| 2,000 steps, batch 8, 224-px random crops; geometric augmentation only | [V] | Protocol JSON; `common.simulate_data_stream(steps=2000, batch=8)` |
| Validation: 5 tiles, sliding window with stride 112 and averaged logits | [V] | Protocol JSON (crop_and_tiling) |
| Locked test: 8 Vaihingen tiles, 0 opened (82 records checked) | [V] | `GATE2_FINAL_REPORT.md` §1; `G10.locked_test_untouched` |
| Phase 2D: 75 completed runs = 12 pilot (K0, L0, L12, L23 × 3 seeds) + 63 oracle (21 blocks × 3); all pass result, checkpoint and reload integrity | [V] | `gate2_analysis.json` (integrity_problems = []); `06_INTEGRITY_VERIFICATION.md` |

## 3. Data and DSS details
| Item | Status | Evidence |
|---|---|---|
| All 38 Potsdam IRRG tiles used to fit the fixed radiometric transform (0 Vaihingen files) | [V] | `radiometric_transform.json`: `n_potsdam_files_used` = 38 |
| All 38 Potsdam tiles used for the source-vs-source null | [V] | `gate0_dss.py:190`: `null_matched(X9[:38], 16, 5, …)` |
| R2 source centroid uses the **first 16** Potsdam tiles in sorted order | [V] | `gate0_dss.py:191`: `D(X9[:16], X9[38:43])` |
| R2 target = **5 probe tiles**: areas 1, 10, 11, 12, 13, all inside the 20 training tiles | [V] | Split manifest (probe rule: "first 5 files (lexicographic) of target_train"); `gate0_dss.py:44` |
| R2 uses images only, no labels | [V] | `gate0_dss.py` docstring ("No labels, no training"); split manifest `labels_accessed: false` |
| DSS = mean cosine distance of target pooled features to the source centroid, z-scored against a matched source-vs-source null | [V] | `gate0_dss.py:82–88`, 190–191 |
| Validation (areas 30–34) and test tiles separate from training and probe | [V] | Split manifest; 15 + 5 + 5 + 8 = 33 |

## 4. Utility definition (from the analysis code)
[V] `gate2_analysis.py` (frozen before any Gate 2 training; hash recorded in manifests v4–v12):
- For each run, it takes the per-tile 6×6 confusion matrices of the **final evaluation**, checking
  that the last eval step is 2,000 (`last_eval_2000`).
- It **sums them over the 5 validation tiles** (pooled) and computes the **6-class mIoU** (nan-mean of
  per-class IoU).
- **U(ℓ, s) = mIoU6(ℓ, s) − mIoU6(K0, s)**, the same-seed decoder-only baseline.
- The per-layer mean is taken over the 3 seeds.
- The 5-class (no clutter) version is secondary.
- [V] The stored and recomputed mIoU agree exactly (maximum difference 0.0).

## 5. Phase 2D findings (from `gate2_analysis.json`)
| Claim | Status | Value |
|---|---|---|
| Utility varies across blocks | [V] | Range −0.0073 (L0) to +0.0372 (L16); Kendall W across seeds 0.73 |
| Peak around L11–L17; L16 highest | [V] with a wording caveat (see D2) | L16 +0.0372; L13 0.0357; L11 0.0354; L17 0.0341; L15 0.0322; **L12 0.0263**; L14 0.0301 |
| L0 negative; L23 low | [V] | L0 −0.0073; L23 +0.0146 (rank 21 of 24) |
| R2 Spearman with utility | [V] | 0.420 (seed-resampled 95% [0.23, 0.56]; tile-resampled [−0.15, 0.69]) |
| Late rule Spearman | [V] | 0.422 |
| R2 partial correlation given depth | [V] | 0.076 (linear-depth partial, as implemented in `oracle_analysis.partial_spearman`) |
| R2 vs depth | [V] | ρ = 0.941 (`frozen_rankings.json` `depth_spearman`) |
| R2 top-k vs random | [V] | Tile-resampled random percentile of regret_sum: @1 0.67, @3 0.37, @5 0.61; not better than random |
| Utility vs depth shape | [V] | Quadratic fit R² 0.82; linear R² 0.26 (inverted U) |
| **RAW_R2** (unnormalised distance, a frozen secondary selector) | [V] | Spearman 0.414, **partial 0.494**, but top-1 = L0 (the worst block). One of 6 selectors examined: exploratory |
| MMD_R2 | [V] | Spearman −0.077 |
| Precision | [V] | Pooled σ_c = 0.0099 (df 48); per-layer df-2 median half-width 0.034; per-arm residual SD 0.001–0.012 (equal variance doubtful) |
| Original hypothesis not supported | [V] | `GATE2_FINAL_REPORT.md` §8 |

## 6. Discrepancies (recorded, not silently reconciled)
- **D1. The Middle selector was pre-registered, not post hoc.** The rule `Middle = sorted by |ℓ − 11.5|`
  is in `oracle_analysis.py:57`. That file's hash (`31ede6fe…`) is identical in pilot manifest v1 and
  Gate 2 manifest v4, so it was frozen **before any training**. Middle's results were therefore a
  **prospective, pre-specified comparison**: Spearman 0.632, partial 0.728, the best of all rules.
  - What *is* post hoc: the "L11–L17" band, and describing the curve as an inverted U.
  - The presentation and the Gate 2 report describe middle-layer selection as purely exploratory.
    That understates its pre-registered status.
  - However, it was one of several pre-specified comparison rules, not the primary hypothesis.
- **D2. Plateau wording in the final report.** `GATE2_FINAL_REPORT.md` §5 says "plateau at L11–L17
  (+0.030 to +0.037)", but L12 = +0.0263. Meanwhile L8 (0.0310), L18 (0.0310) and L19 (0.0309) exceed
  L12 and L14. The seven best blocks are {8, 11, 13, 15, 16, 17, 18}. The frozen report is not edited;
  Phase 3 documents use exact values.
- **D3. Framing of the research question.**
  - `DSSA_Final_Project_Abstract.pdf` §3 asks for adaptation "**without** full fine-tuning **or labeled
    target-domain data**".
  - The frozen design (`DSSA_PROJECT_FREEZE.md` §A–B) and the implementation are **target-supervised**;
    only the layer selection is label-free.
  - The abstract also lists a "Source training" stage, which was never implemented.
  - Any paper must use the frozen framing.
- **D4. Partial-correlation definition.** The "depth-controlled" partial correlation controls for
  **linear** depth only. Utility is strongly non-monotone in depth (quadratic R² 0.82), so a linear
  partial correlation is not a complete depth control. Phase 3 must pre-register a non-linear depth
  control.
- **D5. Decoder confound (design fact, not an error).** The decoder reads L23 only. Adapting block ℓ
  reaches the decoder only through blocks ℓ+1 … 23. The utility curve may partly reflect this decoder
  design rather than intrinsic layer "adaptability". The protocol froze this deliberately, but it limits
  generalisation.
- **D6. Scale mismatch (design fact).** Prithvi-EO-2.0 was pretrained on 30 m HLS data
  (Szwarcman et al., arXiv 2412.02732) and is applied here at 5–9 cm with 3 of 6 bands. Block-wise
  behaviour may not transfer to settings closer to the pretraining domain.
- **D7. CrossEarth-Gate venue.** The prompt describes it as CVPR 2026. The arXiv listing (v3, 17 Jun
  2026) carries no venue comment [U].

## 7. What must remain frozen
- Manifests v1–v12 and the version register.
- All 85 run folders, including checkpoints, `hashes.json` and the incident records.
- `gate0/frozen_rankings.json`, `baseline_hashes.json`, the split manifest and the radiometric
  transform.
- `gate2_analysis.py`, `oracle_analysis.py`, `gate2_analysis.json` and `GATE2_FINAL_REPORT.md`.
- The `dssa/phase2d/` code hash. Adding files there breaks run verification.
- The Phase 2C artifacts.
- The 8 locked Vaihingen test tiles and their labels: zero access until the opening rule in
  `PHASE3_EXPERIMENTAL_PROTOCOL.md` §9 is met.

## 8. Unused assets relevant to Phase 3 (inventory only, not opened)
- [V] `dssa/Data/Potsdam/5_Labels_all.zip` and `5_Labels_all_noBoundary.zip` (Potsdam labels) and
  `4_Ortho_RGBIR.zip` exist locally. **Potsdam labels have never been opened by this project**
  (Potsdam was used as images only).
- [V] Phase 2D K0 decoder checkpoints (`best` and `final` per seed) exist. They could initialise cheap
  gradient-based calibration signals without new training.
