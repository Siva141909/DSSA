# DSSA Prithvi-EO-2.0 Compatibility Audit

**Candidate under audit:** ISPRS Potsdam (IRRG) → ISPRS Vaihingen (IRRG)
**Method:** exact architectural facts below were pulled from the raw `config.json` of the actual Hugging Face checkpoints (`ibm-nasa-geospatial/Prithvi-EO-2.0-300M` and `-600M`), fetched directly in this session — not summarized, not from memory — plus TerraTorch's documented band-adaptation mechanism (the official IBM/NASA fine-tuning toolkit for this model family). Where something could not be verified this way, it is marked unverified.

No code was written. No hypothesis, DSS definition, or LoRA setting was modified.

---

## 1. Exact input specification (verified)

| Property | Prithvi-EO-2.0-300M | Prithvi-EO-2.0-600M | Source |
|---|---|---|---|
| `in_chans` | **6** | **6** | Raw `config.json`, both checkpoints, fetched directly this session |
| `bands` (order) | `["B02","B03","B04","B05","B06","B07"]` | identical | Raw `config.json` |
| Band identity (HLS-harmonized naming, confirmed against a separate, independent source describing the same model) | **Blue, Green, Red, Narrow NIR, SWIR1, SWIR2** — in that order | identical | Cross-confirmed: raw config band codes + independent web-search summary of the HF model card stating "six bands in the following order: Blue, Green, Red, Narrow NIR, SWIR, SWIR 2" |
| `patch_size` (t, h, w) | `[1, 16, 16]` | `[1, 14, 14]` | Raw `config.json` |
| `img_size` | 224 | 224 | Raw `config.json` |
| `num_frames` (temporal) | 4 | 4 | Raw `config.json` |
| `embed_dim` / `depth` / `heads` | 1024 / 24 / 16 | 1280 / 32 / 16 | Raw `config.json` (capacity differs by variant; input spec does not) |
| Per-band normalization `mean` | `[1087.0, 1342.0, 1433.0, 2734.0, 1958.0, 1363.0]` (Blue…SWIR2) | identical | Raw `config.json` |
| Per-band normalization `std` | `[2248.0, 2179.0, 2178.0, 1850.0, 1242.0, 1049.0]` | identical | Raw `config.json` |

**Note on band naming:** an earlier fetch in this audit initially mislabeled B05/B06/B07 as "Red Edge / SWIR-1 / SWIR-2," which would be correct for *raw ESA Sentinel-2* band numbering but is **wrong** for this model — Prithvi-EO-2.0 uses the *HLS-harmonized* band-numbering convention, where B02–B07 are re-mapped to the six bands common to both Landsat and Sentinel-2 (dropping Sentinel-2's red-edge bands, which Landsat doesn't have). This was caught and corrected by cross-referencing the raw config against an independent source before relying on it — flagged here so the correction itself is auditable.

**Input tensor shape, full form:** `(Batch, 6, 4, 224, 224)` — (channels, time, height, width), per the fetched config. Both checkpoint sizes share this input contract; they differ only in internal capacity.

The normalization mean/std values (~1000–2700 range) are consistent with Sentinel-2/HLS **reflectance-scaled integer digital numbers** (typically ×10000 reflectance, truncated/scaled to this kind of range) — **not** typical 8-bit (0–255) aerial-photography digital numbers. This is a separate, load-bearing finding — see Section 5.

## 2. Can Potsdam/Vaihingen IRRG be passed directly?

**No**, on three independent counts:

1. **Band count/identity:** IRRG provides 3 bands (aerial broadband near-infrared, Red, Green); the model expects 6 specific bands (Blue, Green, Red, Narrow-NIR, SWIR1, SWIR2), in that exact order, feeding a patch-embedding layer with a fixed `in_chans=6` weight tensor.
2. **Radiometric scale:** Potsdam/Vaihingen pixel values are standard aerial digital-camera output (documented elsewhere in this project's materials as 8-bit imagery); the model's normalization statistics are calibrated to a Sentinel-2/HLS reflectance-DN scale roughly 4–10× larger in magnitude with a different physical basis entirely. Feeding raw 0–255 values through those statistics unmodified would produce wildly out-of-distribution normalized inputs, independent of the band-count problem.
3. **Temporal dimension:** the model expects 4 time steps per sample (`num_frames=4`); Potsdam and Vaihingen are single-acquisition (one timestamp per tile), not time series.

None of these three is optional — all three must be resolved for the pair to be usable at all, not just the band-count issue the earlier dataset audit focused on.

## 3. Reconciliation approaches — enumerated and scored

Evaluated in the required priority order: **pretrained-weight preservation → scientific validity → source/target symmetry → reproducibility → implementation complexity.**

### Approach A — Zero-fill unavailable bands in the original 6-channel patch embedding (equivalently: slice out only the pretrained weight-channels for available bands)

**What it is:** Keep the pretrained `in_chans=6` patch-embedding layer **entirely unmodified** — every weight, exactly as pretrained. Construct the input so that:
- Green slot (band index 1) = real Vaihingen/Potsdam Green channel
- Red slot (index 2) = real Red channel
- Narrow-NIR slot (index 3) = real aerial-IR channel (**approximate** correspondence — see caveat below)
- Blue slot (0), SWIR1 slot (4), SWIR2 slot (5) = the dataset's own per-band **mean** value, fed in *before* normalization, so that after the standard `(x − mean) / std` step each of these three channels becomes exactly zero.

Because a convolution's contribution from a channel whose input is exactly zero is exactly zero regardless of that channel's weights, this is mathematically identical to using only the pretrained weight-slices for Green/Red/Narrow-NIR and discarding the other three — a real 3-effective-channel patch embedding, built entirely from unmodified pretrained parameters, with zero weights reinitialized or invented.

| Dimension | Assessment |
|---|---|
| Changes pretrained patch embedding? | **No structural change** — same layer, same shape, same weights, untouched. |
| Requires replacing/reinitializing weights? | **No.** Nothing is reinitialized or randomly set. |
| Uses synthetic/missing bands? | Blue/SWIR1/SWIR2 are **absent, not synthesized** — they contribute zero, not a fabricated value. Narrow-NIR slot uses a **real but spectrally approximate** substitute (aerial broadband IR, not satellite narrowband NIR). |
| Changes the pretrained representation space? | **Partially, but deterministically and symmetrically** — the patch embedding now operates on less information than it was trained with, but the exact same constrained function is applied to every input, source and target alike. Everything downstream of the patch embedding (all 24 or 32 transformer layers) is completely untouched and processes whatever token embeddings result, exactly as it would for any other input. |
| Introduces an additional confound? | One, explicitly named: the aerial-IR↔Narrow-NIR substitution is spectrally approximate, not exact (different sensor technology and bandwidth). This is a **known, bounded, explicitly documented** limitation, not an unknown one. |

### Approach B — Replace the patch embedding with a freshly-initialized 3-channel layer

Instantiate a new `in_chans=3` Conv3d patch embedding with random (or otherwise newly-initialized) weights, discard the pretrained 6-channel layer entirely, keep the rest of the network pretrained/frozen.

| Dimension | Assessment |
|---|---|
| Changes pretrained patch embedding? | **Yes, completely replaced.** |
| Requires replacing/reinitializing weights? | **Yes** — the entire first layer starts untrained. |
| Uses synthetic/missing bands? | No missing-band problem (matches available data exactly), but at the cost of point below. |
| Changes the pretrained representation space? | **Severely.** The very first layer of the network — the one every subsequent layer's representation depends on — is no longer pretrained. Every downstream layer's output becomes a function of this untrained entry point, contaminating the "frozen pretrained backbone" premise the entire DSSA methodology depends on. |
| Introduces an additional confound? | **Yes, a severe one:** DSS would no longer be measuring drift through a pretrained model at all — it would be measuring drift through a randomly-initialized-then-implicitly-shaped function, which defeats the purpose of using a foundation model's pretrained representations in the first place. |

**Rejected** on the very first evaluation criterion (pretrained-weight preservation) before scientific validity is even considered.

### Approach C — Channel duplication (feed Red into the Blue slot, IR into SWIR1/SWIR2 slots, etc.)

| Dimension | Assessment |
|---|---|
| Changes pretrained patch embedding? | No structural change (same as Approach A). |
| Requires replacing/reinitializing weights? | No. |
| Uses synthetic/missing bands? | **Yes** — actively feeds spectrally incorrect data (e.g., visible-Red reflectance into a slot the model was trained to interpret as SWIR reflectance) rather than leaving it absent. |
| Changes the pretrained representation space? | **Unpredictably.** Unlike Approach A's zero-contribution (a well-understood null), duplicated channels contribute a *systematically wrong, non-zero* signal through weights calibrated for a physically different quantity — the effect on the resulting representation is not analytically characterizable the way Approach A's is. |
| Introduces an additional confound? | **Yes, and it is harder to reason about than Approach A's** — Approach A's deficiency (missing information) is at least well-understood and symmetric; Approach C's deficiency (actively wrong information) could interact with source/target content differently in ways that are difficult to predict or bound. |

**Rejected** — strictly worse than Approach A on scientific validity, for no gain in weight preservation (both preserve weights equally) or symmetry (both are equally applicable to source and target).

### Approach D — Synthetic band estimation (predict plausible Blue/SWIR values from available R/G/IR via a separate model)

| Dimension | Assessment |
|---|---|
| Changes pretrained patch embedding? | No. |
| Requires replacing/reinitializing weights? | No (for Prithvi itself), but introduces a **second model** with its own weights, training data, and assumptions. |
| Uses synthetic/missing bands? | **Yes, explicitly** — fabricated band values, by construction. |
| Changes the pretrained representation space? | Unpredictably, and in a way that now depends on a **third data distribution** (whatever the band-synthesis model was itself trained on), on top of source and target. |
| Introduces an additional confound? | **Yes, the largest of any approach** — a learned synthesis step is very unlikely to behave identically on Potsdam vs. Vaihingen imagery (violating source/target symmetry), and its own domain dependence would be entangled with the domain shift DSSA is trying to measure, making the resulting DSS uninterpretable without a whole separate validation of the synthesis model itself. |

**Rejected** — worst option evaluated on scientific validity and symmetry, and adds implementation complexity beyond every other option.

## 4. Which approach preserves the pretrained representation as much as possible?

**Approach A.** It is the only option that modifies zero pretrained weights, uses no fabricated data (only documented absence, which a linear layer handles as a clean zero-contribution rather than an unpredictable wrong signal), and — critically — is trivially and exactly identical whether applied to Potsdam or Vaihingen, since **both datasets natively provide the same three bands (IR, R, G) in the IRRG modality.** This last point is a specific strength of this dataset pair: no source-side/target-side asymmetry needs to be introduced by the reconciliation itself, because IRRG availability is symmetric by construction.

## 5. Is DSS, computed under Approach A, still scientifically interpretable?

**Yes, with an explicit scope restriction that must be stated in any write-up:**

DSS would measure representation drift **as seen through the model's 3-effective-channel operating view**, not through its native 6-channel view. This is not a fatal flaw, for a specific reason worth stating plainly: **the exact same 3-channel constraint applies at every stage of the eventual pipeline** — the DSS computation step and the final LoRA-adapted segmentation step both see the same Green/Red/approximate-NIR-only information. DSS is therefore measuring drift in *exactly the representation space the downstream task will actually use*, not some inaccessible, hypothetical full-band space. This is a coherent, internally consistent scope restriction, not a mismatch between what is measured and what is used.

What must be stated as an honest limitation, not glossed over: since three of six channels contribute nothing, DSS computed this way could plausibly **understate** true domain sensitivity, if the discarded spectral regions (Blue, SWIR1, SWIR2) would have carried a large share of the genuine cross-domain signal. There is no way to rule this out without the missing bands — it is a real, named limitation of using an aerial IRRG pair with a satellite-multispectral-pretrained backbone, not specific to Potsdam/Vaihingen as a city pair.

## 6. Does the same transformation apply identically to source and target?

**Yes.** Potsdam (used in its IRRG modality, one of its three official releases) and Vaihingen (IRRG is its *only* modality) both natively provide Infrared, Red, Green. Approach A's channel mapping (IR→Narrow-NIR slot, R→Red slot, G→Green slot, zero elsewhere) requires **no dataset-specific branching** — the identical function is applied to both. This is a genuine point in favor of this specific pair relative to, for example, a pair where one side had true RGB and the other had IRRG (which would force asymmetric handling).

## 7. What would invalidate the experiment — enumerated

1. **Radiometric scale mismatch, unresolved.** Prithvi's normalization statistics are calibrated to Sentinel-2/HLS reflectance-scaled digital numbers (~1000–2700 range); Potsdam/Vaihingen are standard 8-bit (0–255) aerial imagery. Approach A's zero-fill logic depends on being able to normalize the *live* channels sensibly — if the live-channel values are fed through Prithvi's pretrained mean/std without first being rescaled to a comparable range, the "live" channels would be as out-of-distribution as the zero-filled ones, defeating the purpose of preserving them. **This is not yet resolved by this audit and must be, before implementation** — see open item below.
2. **Unverified temporal-dimension handling.** Whether the actual model code accepts `num_frames=1` (a single timestamp) or strictly requires 4, and if the latter, whether naive replication of one image across all 4 temporal slots produces sensible representations (as opposed to an artifact the pretrained temporal-attention components were never designed to see) — **not verified in this audit**, would need direct inspection of the model's forward-pass code or a working test run.
3. **Unverified spectral plausibility of the aerial-IR↔Narrow-NIR substitution**, beyond the conceptual argument made above — whether the pretrained Narrow-NIR weight channel produces sensible (not degenerate/saturated) activations when fed aerial CIR data is an empirical question, not something resolvable from documentation alone.
4. **If any of 1–3 turn out to produce degenerate representations** (e.g., activations dominated by the zero-filled channels' bias terms, or a temporal-replication artifact that swamps the genuine signal) **once actually tested**, that would be new evidence this audit could not anticipate from specification alone, and would warrant reopening this compatibility question specifically — not necessarily the dataset-pair decision itself, since Approach A's logic would apply identically to any RGB/IRRG-only remote-sensing pair, not just this one.

## 8. Open items this audit surfaces but does not resolve

Per instruction, these are **not** silently decided:

- **Radiometric rescaling method** (item 1 above) — options include: rescale Potsdam/Vaihingen DNs to approximate the Sentinel-2 reflectance-DN range Prithvi expects (e.g., via a documented linear or histogram-based mapping), or compute fresh mean/std statistics from Potsdam/Vaihingen itself for the three live channels instead of reusing Prithvi's pretrained statistics (a departure from "use the model as pretrained expects" in its own right, since the model was calibrated to its own specific statistics). **This is a decision the team must make**, not one this audit chooses.
- **Temporal-dimension handling** — replicate the single image 4×, or investigate whether the codebase supports `num_frames=1`. **Not decided here.**

---

## Final Status

## 🟡 YELLOW — compatible with explicitly documented transformations

Potsdam(IRRG) → Vaihingen(IRRG) is **not** disqualified from use with Prithvi-EO-2.0. A defensible reconciliation (Approach A) exists that preserves 100% of the pretrained patch-embedding weights, invents no data, and applies with perfect source/target symmetry — a direct consequence of both datasets natively sharing the same IRRG band set. This is the strongest possible outcome available to *any* RGB/IRRG-only dataset against this particular 6-band backbone; no dataset considered in the prior audit would have scored better on the band-preservation criterion specifically, since none provide all 6 native Prithvi bands.

This is **not GREEN**, because real, non-trivial, currently-unresolved work remains: a radiometric rescaling decision, a temporal-dimension decision, and empirical (not just documentary) verification that the resulting representations are non-degenerate. All three are ordinary, boundable engineering/calibration questions — not indications that the pretrained representation is being substantially destroyed — which is why this does **not** rise to RED and does **not** trigger reopening the dataset decision.

**The dataset decision is not reopened.** The two open items in Section 8 should be resolved (as explicit, documented decisions) before implementation begins.
