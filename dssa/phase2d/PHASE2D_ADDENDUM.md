# DSSA Phase 2D Addendum (Draft 2)

Applies the research lead's conditional authorization to Protocol Draft 1. It
does not change `dssa/config/phase2b_training_protocol.json`, the split manifest,
frozen DSS results, or any Phase 2C artifact. Authorization covers Gate 0 and
12 pilot runs only.

## 1. Effect size and replication
- delta = 0.010 pooled validation mIoU is the provisional minimum effect of
  interest. It is a research judgement, fixed in advance: one percentage point,
  the same order as the lead reported by CrossEarth-Gate over its next-best
  method. Pilot results never change it.
- Draft 1's rule (delta_final = max(0.010, 2 sigma)) with r derived from
  delta_final was circular and always gave r = 1. It is withdrawn.
- The pilot estimates precision only. For arm a, seed s:
  mIoU(a,s) = arm + seed + residual, residual SD sigma_e with 6 df.
  sigma_c = sqrt(2) sigma_e is the SD of a same-seed difference between arms.
- Seeds for a 95% half-width of delta on one contrast:
  r_prec = ceil((1.96 sigma_c / delta)^2).
- Seeds for 80% power at delta: r_pow = ceil(((1.96 + 0.84) sigma_c / delta)^2).
- Both are normal approximations and are also reported at the upper 95% limit
  of sigma_c (factor 2.20 at df 6).

## 2. Uncertainty sources kept separate
- Seed: changes training crops, augmentation, decoder init and LoRA A together.
  Three seeds give a preliminary, imprecise estimate with 6 df.
- Tile: resampling tiles within one fixed trained model. Conditional on these
  five tiles and models.
- Crop: applies to DSS only, via crop resampling in `frozen_rankings.json`.
- Sources are reported side by side and are not added together.

## 3. R2 status
R2 is an exploratory signal choice, made after inspecting preliminary DSS
variants. Its crops, ranking and scores, and the analysis scripts, are frozen by
hash before training. Only the later oracle evaluation is prospective.

## 4. MMD
MMD_R2 is a secondary exploratory selector: biased RBF MMD^2 with median
bandwidth on the same pre-norm, 9-crop file vectors and same files as R2, with a
matched 16-vs-5 null of 10,000 draws. It enters the Gate 3 comparison.

## 5. Scope of conclusions
All Phase 2D conclusions apply only to the L23-only decoder architecture. No
claim extends to multi-tap or other decoders.

## 6. K0_s1000 versus run000
`gate0_setup.py` verifies: code identical to git HEAD for all training modules;
`train.run_training` called unchanged; K=0 uses the unchanged build path; seed,
steps, checkpoint schedule, optimizer constants, library versions; evaluator
predictions pixel-identical to `tiling.py`. The OS differs (26.6.2 vs 26.7.1) and
is recorded. Data order and augmentation follow from the unchanged dataset class
and seed, and are replayed at each run. The outcome test is exact comparison of
the 10 validation points and training losses.

## 7. Permitted write paths
- `dssa/phase2d/`: code and this addendum.
- `dssa/artifacts/phase2d/`: all generated evidence.
- `.gitignore`: one appended rule for `**/*.pt` and `**/*.npz` under Phase 2D.
Writes elsewhere in the project are refused at runtime. The off-machine backup
goes outside the project.

## 8. Memory stops
Stop if process footprint exceeds 11.5 GB, swap grows by more than 512 MB within
a run, or macOS memory pressure is critical. Warning-level pressure is recorded.

## 9. Runtime
Provisional per-run estimate: 1472 + 34.6 x (24 - layer) seconds, 1467 s for K0;
total 6.0 h. Run-level limit is 1.5 x that estimate, from process start. Measured
Draft 1 step times imply a bottom-up figure 6-10% above the fit, and post-run
reload adds about 1 min per run. Final values come from the pilot.

## Evaluation
Primary utility is pooled 6-class mIoU at fixed step 2000, relative to same-seed
K0. 5-class pooled mIoU, tile mIoU over classes present in the tile, and
validation cross-entropy are secondary. Best-checkpoint values are secondary.

## Decision aid after the pilot (recommendation to the research lead only)
- Proceed with one seed: r_prec point estimate is 1, and the layer contrast is
  not contradicted by tile or seed uncertainty.
- Add seeds: r_prec point estimate is 2 to 4.
- Stop or redesign: r_prec point estimate above 4, or integrity failure.
Whether 0.010 is resolvable is stated with the upper-limit figures alongside.
