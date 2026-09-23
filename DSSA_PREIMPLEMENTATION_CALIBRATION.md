# DSSA Pre-Implementation Calibration Audit

**Candidate dataset (unchanged, not reopened unless Section 11 says otherwise):** ISPRS Potsdam (IRRG) → ISPRS Vaihingen (IRRG)

All facts below are pulled from primary sources fetched directly in this session: the official ISPRS dataset description pages, the NASA HLS Product User Guide, and — critically — the **actual Prithvi-EO-2.0-600M model source code** (`prithvi_mae.py`, fetched raw from Hugging Face) and an **official NASA-IMPACT downstream fine-tuning config** (`burn_scars.py`, fetched raw from GitHub). Not summarized, not from memory. No code written for DSSA itself. No frozen research decision (DSS, hypothesis, layer selection, LoRA rank/matrices, baselines, ablations, split protocol) modified.

---

## 1. Radiometric Facts

| Property | Value | Source |
|---|---|---|
| Potsdam TOP (True OrthoPhoto) format | **8-bit** TIFF, per-channel | ISPRS official Potsdam benchmark page, fetched this session |
| Potsdam available compositions | IRRG (3 ch.), RGB (3 ch.), RGBIR (4 ch.) — all 8-bit | ISPRS official page |
| Vaihingen TOP format | **8-bit** TIFF, 3 bands: near-infrared, red, green | ISPRS official Vaihingen benchmark page |
| Nature of the imagery | **Rendered, orthorectified photogrammetric mosaic** ("True OrthoPhoto") — a processed visualization/mapping product, not a raw sensor digital number and not a calibrated physical-reflectance product | ISPRS official pages; no atmospheric-correction or reflectance-calibration step is documented anywhere in the official ISPRS materials found |
| Official reflectance conversion for Potsdam/Vaihingen | **None found.** These are a photogrammetry/segmentation contest benchmark, not a calibrated remote-sensing reflectance product. | Searched directly; no such document located |
| Prithvi-EO-2.0 expected input, precise nature | **Calibrated surface reflectance** from the HLS product. HLS stores surface reflectance as **int16, scaled ×10000** (i.e., divide by 10000 to recover a 0–~1 reflectance fraction) | NASA LP DAAC HLS Product User Guide, fetched this session: "surface reflectance data uses a scale factor of 10000 to save as int16" |
| Confirmation, from actual downstream fine-tuning code | The official NASA-IMPACT `burn_scars.py` config's `img_norm_cfg` uses means/stds in the **0.03–0.23 range** (e.g., mean `[0.033, 0.057, 0.059, 0.232, 0.197, 0.119]`) — i.e., statistics computed **after** dividing raw HLS int16 values by 10000, confirming normalization is defined in **reflectance-fraction space**, not raw-DN space. (The earlier-fetched pretraining `config.json`'s means, ~1000–2700, are the same physical quantity expressed in the *pre-division* int16-scaled space — same calibration, two different points in one pipeline.) | Raw `burn_scars.py`, NASA-IMPACT/hls-foundation-os, fetched this session |

**Conclusion of fact-finding:** Prithvi-EO-2.0 expects a specific, physically calibrated quantity (atmospherically-corrected surface reflectance) that Potsdam/Vaihingen's 8-bit rendered orthophotos do not provide and cannot be exactly converted into — the calibration information needed (original radiometric response, atmospheric conditions, and whatever contrast-stretching produced the 8-bit rendering) is not recoverable from the published product. **No strategy below claims to recover true reflectance.** The question is which approximation introduces the fewest additional assumptions and the least risk to DSS's validity — not which one is "correct," because a fully correct conversion is not achievable with the available documentation.

## 2. Radiometric Strategies Considered

| Strategy | Preserves pretrained assumptions | Source/target symmetry | Leakage risk | Effect on DSS | Reproducibility | Scientific defensibility | Complexity |
|---|---|---|---|---|---|---|---|
| **A. Fixed global linear scaling** (e.g., 0–255 → an arbitrary fixed numeric range) | Low — arbitrary, no radiometric basis | High (identical formula both sides) | None | Neutral-to-uncertain — symmetric distortion, doesn't erase signal, but doesn't recover meaningful structure either | High | Low-moderate — honest but crude | Low |
| **B. Per-channel fixed scaling** | Low (same core issue as A, just per-band constants) | High | None | Same as A | High | Low-moderate | Low |
| **C. Source-derived scaling, applied unchanged to target** | Low (still an approximation, not true reflectance) — but **methodologically standard**: fit only on source, freeze, apply to target — the textbook-correct way to avoid any train/test (here, source/target) leakage in preprocessing | High — one fixed, frozen formula, identical for both | **Lowest of all strategies** — by construction, target data (labeled or not) never informs the transform | Preserves the signal DSS needs to detect; does not artificially force source and target to look alike | High | **Highest of the approximation-based strategies** — standard ML preprocessing discipline | Low-moderate |
| **D. Dataset-specific (per-domain) normalization** | Low | Formally symmetric (same procedure), but **substantively asymmetric** — each domain is normalized to look like itself | Uses target *statistics* (not labels), but see next column | **Actively dangerous**: normalizing each domain to its own zero-mean/unit-variance **erases exactly the between-domain differences DSS is designed to measure**, before DSS ever runs | High | **Not defensible for this application** (though it would be reasonable practice in a context that didn't care about preserving between-domain signal) | Low |
| **E. Percentile / contrast-stretch normalization** | Low | If fit **per-image or per-dataset**: same problem as D, at an even finer (per-image) grain — a common, easy-to-reach-for default that would be scientifically damaging here | If fit on target: uses target statistics in a signal-erasing way | Same risk as D, potentially worse if applied per-image (a very common but here-inappropriate remote-sensing preprocessing habit) | High | **Not defensible**, unless restricted to a source-fit-only variant (which collapses into Strategy C) | Low-moderate |
| **F. Histogram matching (target matched to source, or vice versa)** | Low | The *technique itself* is designed to make one domain's histogram resemble the other's | None (no labels), but **defeats the measurement's purpose** | **Most severe signal-erasure risk of all strategies** — histogram matching's entire point is to eliminate exactly the distributional difference DSS exists to detect | High | **Not defensible for DSS specifically** | Moderate |
| **G. Official documented radiometric conversion** | Would be highest, if it existed | N/A | N/A | N/A | N/A | **Not available** — searched directly, no such ISPRS-published conversion was found | N/A |

## 3. Selected Radiometric Strategy

**Strategy C — a fixed, affine, per-channel transform fit once on Potsdam (source) statistics only, frozen, and applied identically to Vaihingen (target) without ever being refit.**

**Exact operational contract:**
1. From a sample of Potsdam IRRG source images (unlabeled use is sufficient — no labels needed for this step), compute per-channel statistics (e.g., mean and standard deviation, or a percentile-based range) for each of the three available channels (IR, R, G), **using only Potsdam data**.
2. Define one fixed per-channel affine map: `x_calibrated = (x_8bit − source_stat_offset) × source_stat_scale`, chosen so the resulting distribution's central tendency and spread approximate the pretrained model's expected per-band range for the corresponding slot (Green→Green, Red→Red, aerial-IR→Narrow-NIR — the band mapping already fixed in `DSSA_PRITHVI_COMPATIBILITY_AUDIT.md`).
3. Freeze these coefficients. Apply the identical formula to **every** Potsdam and **every** Vaihingen image, with no per-image or per-dataset refitting, ever.
4. Feed the result through the standard `(x − pretrained_band_mean) / pretrained_band_std` normalization step using Prithvi's own published per-band statistics (Section 1), consistent with `DSSA_PRITHVI_COMPATIBILITY_AUDIT.md`'s zero-fill design for the unavailable Blue/SWIR1/SWIR2 channels.

**What this does not claim:** that the resulting values are true physical surface reflectance. What it does guarantee: zero target-derived information enters preprocessing, the exact same deterministic function is applied to both domains, and no step of this transform works to suppress or exaggerate genuine distributional differences between Potsdam and Vaihingen — it is radiometrically approximate but not signal-erasing, and it is the only evaluated strategy that satisfies the required leakage constraint (Part D) by construction rather than by discipline.

---

## 4. Temporal Architecture Facts

Directly from the actual model source, `prithvi_mae.py` (Prithvi-EO-2.0-600M, fetched raw this session):

- **`PatchEmbed`** is a plain `nn.Conv3d(in_chans, embed_dim, kernel_size=patch_size, stride=patch_size)`. Its `forward()` reads `B, C, T, H, W = x.shape` directly from the input tensor at call time — **there is no hardcoded assumption of T=4 anywhere in this layer.** Any T divisible by `patch_size[0]` (which is 1) works, including T=1.
- **Positional embeddings are sinusoidal** (`get_3d_sincos_pos_embed`, a deterministic sin/cos function of grid position), **not a learned lookup table**. This matters directly: a learned table tied to exactly 4 temporal slots would make T≠4 architecturally awkward; a sinusoidal function does not have this problem.
- **The codebase contains an explicit, dedicated mechanism for exactly this situation.** In `_interpolate_pos_encoding`:
  ```
  if t_patches != grid_size[0]:
      # Re-compute pos embedding to handle changed num_frames
      new_grid_size = (t_patches, *grid_size[1:])
      new_pos_embed = get_3d_sincos_pos_embed(pos_embed.shape[-1], new_grid_size, add_cls_token=True)
  ```
  When the number of input frames differs from the pretrained default, the positional embedding is **exactly recomputed** from the same deterministic formula used at pretraining time — not interpolated, not approximated. (Only the *spatial* H/W dimensions use bicubic interpolation, when resolution changes — the temporal dimension is handled by exact recomputation.)
- **`TemporalEncoder`** is a *separate*, optional component that encodes real calendar date metadata (`temporal_coords`: year and day-of-year), independent of the positional-grid encoding above. It is only active if the model config enables coordinate encoding. The pretrained `config.json` for both the 300M and 600M checkpoints (fetched in the prior audit) specifies **`"coords_encoding": []`** — empty, i.e., **date-based temporal encoding is disabled in the released pretrained checkpoints.** No placeholder acquisition-date decision is needed.
- **Official precedent for `num_frames=1`:** the NASA-IMPACT `burn_scars.py` downstream fine-tuning config (an official example in the Prithvi ecosystem, same architectural family) sets `num_frames = 1` explicitly and uses it in production fine-tuning, with `tubelet_size = 1` (temporal patch kernel of 1, matching the pretrained `patch_size[0]`). This confirms single-frame use is a real, supported, previously-exercised path — not a hypothetical.

## 5. Temporal Strategies Considered

| Strategy | Pretrained-weight preservation | Representation integrity | Source/target symmetry | Reproducibility | Scientific validity |
|---|---|---|---|---|---|
| **A. True `num_frames=1`** | **Excellent** — no weights touched; uses the model's own built-in, purpose-built recomputation path for a changed frame count | High — positional embedding is exactly (not approximately) recomputed for T=1 via the same deterministic formula used at pretraining; `TemporalEncoder` is inactive regardless (disabled by config) | Perfect — identical, content-free structural setting for both domains | High — fully deterministic given the published code | High — precedented by an official downstream config in the same model family |
| **B. Replicate one image 4×** | Good on weights (none touched), but forces `t_patches == grid_size[0]`, so the recompute path is never triggered — each of the 4 identical frames still receives a **different** temporal positional encoding, creating a token sequence that structurally *asserts* temporal variation (via position) where none exists in content. This is a real, avoidable artifact Option A does not have. | Lower — an unforced mismatch between "what the positional encoding implies" (4 distinct moments) and "what the content actually is" (1 moment, repeated) | Perfect (identical procedure both sides), but the artifact itself is unnecessary | High | Lower — introduces a signal with no documented precedent or architectural justification, when a cleaner path (A) exists |
| **C. "Official single-frame adaptation mechanism"** | Same as A | Same as A | Same as A | Same as A | Same as A — **this is Option A**, once the actual code was inspected; they are the same mechanism, not two separate options |

## 6. Selected Temporal Strategy

**Option A — true `num_frames=1`.** Directly supported by the model's own code (exact positional-embedding recomputation, not an interpolation hack), unaffected by the disabled `TemporalEncoder`, and precedented by an official NASA-IMPACT downstream config. No pretrained weights are touched. This is a stronger, better-evidenced conclusion than the prior audit's "unverified, needs code inspection" status — the code has now been inspected directly.

---

## 7. Non-Degeneracy Sanity Test — specification only, not executed

Per instruction, this section **designs** the smallest possible forward-pass-only check. It is not run in this session; no training, no optimization, no target labels, no DSS tuning occurs here or in the proposed script.

**Scope:** a small batch (order of 8–16 tiles) of Potsdam-source and Vaihingen-target images, transformed per Sections 3 and 6, passed once through the frozen backbone in `torch.no_grad()` / eval mode. No gradients computed. No labels loaded (see Part D).

| # | Check | Pre-defined objective criterion | If it cannot be fully pre-defined |
|---|---|---|---|
| 1 | Model accepts the transformed input | A forward pass through patch embedding + all transformer blocks completes without a shape/dtype exception, for every sanity-batch sample, both domains. | Fully pre-definable (binary pass/fail). |
| 2 | No NaNs/Infs | `torch.isfinite(representation).all() == True` for every extracted layer's output, every sample. Zero tolerance — any non-finite value is a fail. | Fully pre-definable. |
| 3 | Activation magnitudes are finite (not exploding/collapsing) | Run **one known-good, natively-scaled HLS reference sample** (any publicly available Prithvi demo/example tile) through the same frozen model first, and record each layer's mean token-wise L2 norm as a reference scale. Require every layer's Potsdam/Vaihingen-derived activation norm to fall within **two orders of magnitude** of that reference layer's norm. | The *absolute* magnitude a "healthy" activation should have cannot be pre-defined from documentation alone (it depends on the specific checkpoint's learned scale) — this is why the criterion is defined **relative to a reference forward pass**, not as an arbitrary absolute number. The two-orders-of-magnitude tolerance is deliberately generous, since the entire point of the experiment is to detect *real* distributional shift, which this check must not itself flag as failure. |
| 4 | Representations are not collapsed (not constant across different inputs) | Per layer, cross-sample variance of pooled representations (across the sanity batch) must exceed a near-zero numerical noise floor (e.g., > 1e-6). | Fully pre-definable — this threshold only needs to distinguish "genuinely constant output" from "any real variation at all," which is a very low bar to set precisely. |
| 5 | Source and target produce distinguishable but non-degenerate representations | Using the **already-frozen** DSS definition (cosine distance, per `DSSA_PROJECT_FREEZE.md` §O-D) as a diagnostic only (not for layer selection at this stage): every layer's raw DSS value must be finite and non-zero, **and** its null-baseline-normalized value (§O-C) must be finite (not NaN, not infinite). | The *specific magnitude* that would count as "scientifically meaningful" domain sensitivity cannot be pre-defined here without circularity — determining how much drift is meaningful is the actual experiment this whole project exists to run. This check only verifies the DSS computation itself produces sane, finite numbers, not that the numbers are "big enough" in any particular sense. |
| 6 | Layer-wise representations can be extracted | Confirm a forward hook (or equivalent) successfully captures an output tensor of the expected shape (`num_tokens × embed_dim`, computed from the actual T=1,H,W and the checkpoint's `embed_dim`) at every one of the model's transformer blocks (24 for the 300M variant, 32 for 600M), with none silently skipped. | Fully pre-definable. |
| 7 | DSS can be computed without labels | Procedural, not numerical: audit the sanity script's data-loading calls and confirm zero references to any Potsdam/Vaihingen ground-truth label path are made anywhere in the run. | This is verified by code/data-access inspection, not a runtime numerical assertion — stated explicitly rather than forced into a numerical form it doesn't naturally take. |

**This test has not been run.** It is fully specified and ready to execute as the first concrete implementation action, before any LoRA code is written.

---

## 8. Leakage Audit

| Stage | Uses target labels? | Uses target validation/test data or statistics? | Uses target-probe (unlabeled)? |
|---|---|---|---|
| Radiometric preprocessing (Strategy C) | No | **No** — by construction, the transform is fit on source only and applied frozen to target. This is stricter than the frozen split policy strictly requires (which would permit unlabeled target-probe use here); the extra caution is deliberate and simplifies the leakage argument to "zero target information of any kind." | No |
| Temporal preprocessing (`num_frames=1`) | No | No — purely structural, identical setting for both domains, no data-dependent fitting at all | No |
| DSS computation (frozen definition, unchanged here) | No | No — governed by the already-frozen split policy (`DSSA_PROJECT_FREEZE.md` §J/R): target-probe only, never target-validation or target-test | Yes, by design (this is what target-probe is for) |
| Non-degeneracy sanity check (Section 7) | **No** — explicitly audited in check 7 above | No | Yes (uses probe-equivalent images only, no optimization performed on them) |

**No leakage identified across any of the three preprocessing/verification stages.** The radiometric strategy is in fact more conservative than the frozen split policy requires.

---

## 9. Exact Preprocessing Contract

For every Potsdam and Vaihingen image, in order:

1. Load the IRRG 8-bit tile (3 channels: aerial-IR, Red, Green).
2. Apply the frozen, source-fit affine transform (Section 3) per channel.
3. Normalize using Prithvi's published per-band mean/std for the Green, Red, and Narrow-NIR slots (Section 1's table; exact values already recorded in `DSSA_PRITHVI_COMPATIBILITY_AUDIT.md`).
4. Zero-fill the Blue, SWIR1, SWIR2 channels in normalized space (i.e., feed each band's own pretrained mean pre-normalization, so it becomes exactly 0 post-normalization) — unchanged from the prior compatibility audit.
5. Assemble the 6-channel tensor, shape `(6, 1, H, W)` per image (T=1, per Section 6).
6. Tile/crop to the model's expected spatial patch grid (standard tiling, same procedure both domains — not re-derived here, follows ordinary practice).
7. Forward through the **entirely unmodified, frozen** pretrained patch embedding and transformer stack.

This contract is deterministic and identical for source and target, satisfying Section 8's symmetry requirement by construction.

## 10. Remaining Assumptions

Stated plainly, none hidden:

- The source-fit affine radiometric transform (Strategy C) is an **approximation**, not a recovery of true reflectance — permanent, not resolvable with the data available, and already the least-assumption-laden option found.
- The aerial-IR → Narrow-NIR band correspondence remains spectrally approximate (carried over from `DSSA_PRITHVI_COMPATIBILITY_AUDIT.md`, unchanged by this audit).
- DSS computed under zero-filled Blue/SWIR1/SWIR2 may understate true domain sensitivity if those discarded bands would have carried a large share of the real cross-domain signal (unchanged limitation, restated for completeness).
- The non-degeneracy sanity check (Section 7) is designed but **not yet executed** — its outcome is not yet known.

## 11. Final Implementation Readiness

## 🟡 YELLOW — one clearly bounded issue remains

Every open question this audit was asked to resolve **has** been resolved with primary-source evidence: the radiometric strategy is selected and justified (Section 3), the temporal strategy is not just selected but confirmed directly against the actual model code with an exact, non-approximated mechanism (Section 6), and no leakage exists in the resulting design (Section 8). The dataset is **not reopened** — a scientifically defensible, symmetric, leakage-proof path to valid input exists, which is the only condition under which reopening was authorized.

The one remaining bounded issue is procedural, not scientific: **the non-degeneracy sanity check (Section 7) is fully specified but has not been executed.** Nothing found in this audit suggests it will fail — the temporal mechanism is now confirmed at the code level, not just inferred, and the radiometric strategy is the most conservative, leakage-proof option evaluated — but per this project's consistent standard throughout every prior document, a check that has not been run is not yet a check that has passed. Running it is the correct, minimal first action of implementation, not a further research question.

**Recommended next step:** execute Section 7's sanity check exactly as specified, with no modification to its pre-registered criteria based on the results. If it passes, the project has no remaining known blockers to implementation. If it fails, return to Sections 3–6 of this document — not to the dataset-selection question — since a failure would implicate the calibration choices audited here, not the underlying dataset pair.
