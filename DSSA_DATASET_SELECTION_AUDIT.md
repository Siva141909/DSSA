# DSSA Dataset Selection Audit

**Frozen research question under test:**
> Can layer-wise representation drift from a frozen geospatial foundation model, using unlabeled target-domain data, identify which transformer layers are worth adapting, such that selective LoRA is competitive with uniform LoRA/full fine-tuning while using fewer trainable parameters?

Note this question does **not** require "cross-sensor" specifically — it requires *some* honest, well-characterized domain shift. That reframes the search: the goal is the cleanest available shift, not necessarily the one matching the project's title.

**Method:** every dataset below was checked against live, sourced information (search results with links, quoted where load-bearing), not memory. Where a fact could not be confirmed, it is marked unconfirmed rather than assumed. No dataset is selected. No methodology or hypothesis is changed.

---

## Candidate 1 — LoveDA → DeepGlobe *(the abstract's original pairing — re-included for reference)*

```
Sensor:            Google Earth platform composite  →  WorldView-3 satellite (different acquisition systems)
Bands:              RGB (3)  →  RGB (3)   — matched to each other, mismatched to Prithvi (needs 6)
Resolution:         0.3 m  →  0.5 m   — close to each other (~1.7x), both ~60-100x finer than Prithvi's 30 m
Classes:            background/building/road/water/barren/forest/agricultural  →  urban/agriculture/rangeland/forest/water/barren/unknown — STRUCTURALLY DIFFERENT taxonomies
Geography:          3 Chinese cities  →  Thailand/Indonesia/India
Labels:             Pixel-level, 7 classes each (different schemas)
Train size:         LoveDA: 2522 train / 1669 val / 1796 test.  DeepGlobe: 803 train / 171 val / 172 test (2448x2448 tiles)
Target-probe feasibility:    Good — DeepGlobe train imagery usable unlabeled.
Target train/val/test feasibility:  Good — official splits exist, but accuracy evaluation is only meaningful after resolving the class mismatch.
Prithvi compatibility:       Poor as-is — 3-band RGB vs. 6-band expected input; ~60-100x resolution gap to pretraining scale.
Required transformations:    Class remapping (lossy — LoveDA splits building/road, DeepGlobe merges into "urban"; DeepGlobe has rangeland/unknown with no LoveDA equivalent) AND a band/resolution-handling strategy for Prithvi.
Major confounds:             Sensor + geography + class-taxonomy + severe resolution/band mismatch against the backbone, all simultaneously.
Domain shift type:           Sensor + geographic + class-distribution, entangled and not separable with this pair.
Cross-sensor defensible:     Partially — a real sensor difference exists, but it cannot be isolated from the class-taxonomy confound.
Research risk:               High — a positive or negative DSSA result on this pair could always be attributed to the taxonomy mismatch rather than to the DSS mechanism itself.
```

**Classification: 🔴 RED — should not be used for the primary experiment**, for the reasons already detailed in `DSSA_PROJECT_FREEZE.md` §P. Kept here only as the reference point the other candidates are compared against.

---

## Candidate 2 — LoveDA Urban → LoveDA Rural (same dataset, official UDA split)

```
Sensor:            Google Earth platform composite  →  same (identical source)
Bands:              RGB (3)  →  RGB (3)   — identical, still mismatched to Prithvi (needs 6)
Resolution:         0.3 m  →  0.3 m   — identical
Classes:            background/building/road/water/barren/forest/agriculture (7)  →  IDENTICAL taxonomy, same 7 classes
Geography:          Urban districts of Nanjing/Changzhou/Wuhan  →  Rural districts of the same 3 cities
Labels:             Pixel-level, 7 classes, identical schema both sides
Train size:         Urban: 1156 train / 677 val / 820 test.  Rural: 1366 train / 992 val / 976 test.
                     (LoveDA's creators define Urban→Rural and Rural→Urban as the dataset's own official UDA benchmark tasks.)
Target-probe feasibility:    Excellent — rural-train imagery usable unlabeled, ample volume.
Target train/val/test feasibility:  Excellent — official, pre-defined splits, directly usable, no remapping needed.
Prithvi compatibility:       Same as Candidate 1 — still 3-band RGB at 0.3 m against a 6-band/30 m backbone. This problem is identical in both directions of Urban↔Rural and does not change with this dataset choice; it is a backbone-vs-data-class issue, not a source-vs-target issue.
Required transformations:    Band/resolution-handling strategy for Prithvi only (same requirement as any other 3-band, sub-meter dataset) — no class remapping needed.
Major confounds:             Content/scene shift (urban infrastructure density vs. agricultural/rural land use) is deliberate and is the entire point of this benchmark — not an accidental confound, but it should be named precisely as "content/geographic shift within one country, one sensor," not "cross-sensor."
Domain shift type:           Geographic + content/scene shift. Explicitly NOT sensor shift, NOT resolution shift, NOT class-distribution shift (classes match exactly, though pixel *frequency* per class will differ between urban/rural — a form of class-imbalance shift, distinct from class-taxonomy mismatch).
Cross-sensor defensible:     No — same sensor both sides. Any write-up must not claim "cross-sensor" for this pair.
Research risk:               Low for the DSS mechanism itself — this is the cleanest possible test of "does representation drift track a real, deliberate, well-documented content shift," with almost every other variable held constant. Risk is only that a positive result here would not, by itself, demonstrate cross-sensor generalization (that would still require a separate pair, e.g., as a later cross-domain validation step).
```

**Classification: 🟢 GREEN — directly supports the frozen research question**, with the explicit caveat that it tests *content/geographic* domain shift, not *sensor* shift. It does not touch the "cross-sensor" framing in the project's title at all.

---

## Candidate 3 — ISPRS Potsdam → ISPRS Vaihingen

```
Sensor:            Airborne camera survey over Potsdam, Germany  →  airborne camera survey over Vaihingen, Germany (different flight campaigns, different camera systems)
Bands:              Available as IRRG, RGB, or RGBIR (4-band)  →  IRRG only (3-band; Vaihingen has NO blue band at all)
Resolution:         5 cm/pixel  →  9 cm/pixel  — differ by ~1.8x from each other, both ~60-100x finer than Prithvi's 30 m
Classes:            impervious surfaces, building, low vegetation, tree, car, clutter/background (6)  →  IDENTICAL taxonomy, same 6 classes
Geography:          Potsdam, Germany  →  Vaihingen, Germany (same country, different towns)
Labels:             Pixel-level, 6 classes, identical schema both sides
Train size:         Potsdam: 38 tiles, 6000x6000 px.  Vaihingen: 33 tiles, ~2000-3800 px per side. (Official ISPRS train/test splits exist; exact train/val counts depend on the specific split convention used — several are common in the literature.)
Target-probe feasibility:    Good — held-out Vaihingen tiles usable unlabeled.
Target train/val/test feasibility:  Good — official ISPRS splits exist and are widely used.
Prithvi compatibility:       Poor as-is — same order-of-magnitude band/resolution mismatch as Candidates 1-2 (3-4 bands vs. 6 expected, sub-decimeter vs. 30 m).
Required transformations:    Band-composition reconciliation (Potsdam must be restricted to its IRRG modality to match Vaihingen's available bands, since Vaihingen has no blue channel at all) + a band/resolution-handling strategy for Prithvi. No class remapping needed — taxonomies already match.
Major confounds:             Genuine sensor/camera difference (different flight campaigns) entangled with a real band-availability difference (Potsdam has blue, Vaihingen doesn't) unless explicitly restricted to the shared IRRG bands. This band restriction is a well-established practice in the domain-adaptation literature for this exact pair (multiple published cross-domain task definitions use IRRG-to-IRRG specifically to control for this).
Domain shift type:           Sensor (different camera/flight) + minor resolution shift, with matched class taxonomy. This is the closest candidate to a "clean cross-sensor" test found in this audit.
Cross-sensor defensible:     Yes, more defensible than Candidate 1 — genuinely different acquisition systems, and (unlike LoveDA→DeepGlobe) not confounded by a class-taxonomy mismatch. Still airborne-to-airborne, not satellite-to-satellite, and both far from Prithvi's native satellite/HLS domain — "cross-sensor" here means "different aerial camera systems," which is a narrower claim than the title's general "cross-sensor remote sensing" framing might suggest.
Research risk:               Medium — well-precedented in prior literature (this exact pair is used by CrossEarth-Gate, among many others, which gives a point of external comparison), but the necessary IRRG-only band restriction must be applied consistently and documented, or a residual band-availability confound sneaks back in.
```

**Classification: 🟡 YELLOW — usable, with an explicit, manageable confound (band-availability restriction to IRRG must be applied and documented).** This is the strongest **genuinely cross-sensor** candidate found, at the cost of a small, well-understood, literature-precedented adjustment.

---

## Candidate 4 — DynamicEarthNet, cross-region split (e.g., source AOIs from one continent, target AOIs from another)

```
Sensor:            Planet Labs PlanetFusion daily composite  →  same product, different geographic AOIs
Bands:              Blue, Green, Red, Narrow-NIR (4)  →  identical — and these 4 bands match, in the same order, the FIRST 4 of Prithvi-EO-2.0's 6 expected bands (Blue, Green, Red, Narrow NIR, SWIR1, SWIR2). Only the two SWIR bands are absent.
Resolution:         ~3 m/pixel  →  ~3 m/pixel  — identical to each other, and only ~10x finer than Prithvi's 30 m pretraining scale (versus ~60-100x for every sub-meter dataset above) — by far the closest resolution match to the backbone found in this audit.
Classes:            impervious, agriculture, forest, wetlands, bare soil, water, snow/ice (7)  →  IDENTICAL taxonomy (one dataset, one label scheme, applied globally)
Geography:          75 areas of interest across six continents — a source/target split would select disjoint AOI subsets from different continents/regions.
Labels:             Monthly pixel-wise labels; daily unlabeled imagery per AOI (2018-2019/2020).
Train size:         75 AOIs total, 1024x1024 px each, daily imagery (~700+ daily frames per AOI over the 2-year span), ~24 monthly labeled frames per AOI. Full archive ≈524 GB (GeoTIFF); a manageable subset (e.g., a handful of AOIs per continent) is sufficient for a single project and does not require downloading the full archive.
Target-probe feasibility:    Excellent, structurally — the daily-unlabeled / monthly-labeled design means abundant unlabeled imagery is available per region essentially "for free," a natural fit for DSSA's target-probe requirement.
Target train/val/test feasibility:  Good, but labeled volume per AOI is modest (≈24 monthly frames/AOI over the archive's span) — sufficient for the small-scale, Kaggle/Colab-appropriate experiments this project targets, but not large by general deep-learning standards. Selecting several AOIs per region increases labeled volume roughly linearly.
Prithvi compatibility:       Best found in this audit — 4 of 6 expected bands present in matching order; ~10x resolution gap (not ~60-100x) to pretraining scale. Still not a drop-in match (2 SWIR bands absent, 10x is not 1x), but a categorically smaller adaptation than any of Candidates 1-3.
Required transformations:    A documented strategy for the 2 missing SWIR channels (e.g., patch-embedding restricted to the 4 available bands, or explicit zero-fill with that artifact acknowledged) + a resizing/patch-handling strategy for the remaining ~10x resolution gap. Smaller-magnitude versions of the same two decision types every other candidate also needs.
Major confounds:             Content/scene shift across continents (different urban morphology, vegetation, climate zones) is deliberate and is the shift being studied — should be named as geographic + content shift, not sensor shift (same sensor/product throughout). Seasonal/temporal misalignment between AOIs is possible if source and target AOI subsets aren't matched on acquisition months — should be controlled for explicitly (e.g., compare same-month labels across regions) or documented as an additional, acknowledged variable.
Domain shift type:           Geographic + content shift, same sensor, same bands, same resolution, same taxonomy — the cleanest isolation of "shift" from "confound" of any candidate in this audit, at the cost of not being a sensor-shift test.
Cross-sensor defensible:     No — same sensor/product throughout. Not a substitute for Candidate 3 if a sensor-shift claim specifically is required.
Research risk:               Low for the DSS mechanism itself (very clean isolation of the variable under study); the main risks are practical/unverified rather than scientific: (a) the exact license terms of the original (non-video-repackaged) dataset were not fully confirmed in this audit — only a CC-BY-4.0-licensed repackaged version was confirmed; (b) labeled volume per AOI is modest, so the effective target-train/val/test sizes depend on how many AOIs are selected; (c) the SWIR-band-handling decision, while smaller in magnitude than other candidates' band gaps, is still undocumented anywhere in our materials.
```

**Classification: 🟢 GREEN, with two items requiring direct confirmation before use** (exact license terms of the original dataset; a documented SWIR-band-handling decision) — scientifically the cleanest shift isolation found, and by a wide margin the closest match to Prithvi-EO-2.0's native input scale of any candidate audited.

---

## Candidate 5 — Prithvi-native single-task benchmarks (e.g., NASA HLS Multi-Temporal Crop Classification) — considered, not detailed

Prithvi-EO-2.0's own paper validates on several HLS-native, genuinely band/resolution-matched downstream datasets: Sen1Floods11 (flood), HLS Burn Scars / Burn Intensity (fire), Landslide4Sense (landslide), and Multi-Temporal Crop Classification (US crop types). These would require **no** band or resolution adaptation at all — the best possible backbone compatibility of any option considered.

They are not detailed to the same depth here because most are **binary** (flood/no-flood, burn/no-burn, landslide/no-landslide) rather than general multi-class land-cover segmentation, which is a task-granularity mismatch with the segmentation framing (mIoU across multiple land-cover classes) the rest of this project's materials assume. Multi-Temporal Crop Classification is multi-class but single-country (US only), which narrows what a "geographic shift" claim could mean (regional variation within the US, not cross-country). No specific source→target pair within this category was verified in enough depth for a full entry.

**Classification: not scored (insufficiently specified as a concrete pair) — flagged as worth a dedicated follow-up search if the team wants a zero-band-adaptation option and is willing to reframe the task as binary/narrow-class rather than general land-cover segmentation.**

---

## Synthesis — 2-3 Scientifically Defensible Candidates and Their Tradeoffs

**No winner is selected. The three candidates below are all defensible; they are defensible for different, mutually exclusive reasons, and picking between them is a values decision (clean isolation vs. sensor-shift authenticity vs. backbone fidelity), not a factual one.**

| | LoveDA Urban→Rural | Potsdam→Vaihingen (IRRG) | DynamicEarthNet cross-region |
|---|---|---|---|
| What it cleanly tests | Content/geographic shift | Sensor shift (camera/flight) | Content/geographic shift |
| Class taxonomy | Matched | Matched | Matched |
| Backbone (Prithvi) compatibility | Poor (same issue as the original pair) | Poor (same issue as the original pair) | Best of all candidates found — ~10x gap vs. ~60-100x, 4/6 bands present |
| "Cross-sensor" claim defensible? | No | **Yes** | No |
| External precedent in prior literature | Yes (official LoveDA UDA benchmark) | Yes (used by CrossEarth-Gate and others) | Less common as a DA benchmark specifically (used more for change detection) |
| Main open item before use | Backbone band/resolution handling still undecided | IRRG-restriction must be applied and documented | License of original (non-repackaged) dataset unconfirmed; SWIR-handling undecided |
| Research risk profile | Low — cleanest possible isolation, but never touches "cross-sensor" | Medium — well-precedented, one restriction to enforce | Low scientifically, some practical unknowns to close out |

**The tension in one sentence:** the pair that best matches the *backbone's* native input (DynamicEarthNet) is not a sensor-shift test; the pair that best matches the *title's* "cross-sensor" framing (Potsdam→Vaihingen) has the same severe backbone mismatch as the original candidate; and the pair with the strongest existing benchmark precedent for exactly this kind of study (LoveDA Urban→Rural) is also not a sensor-shift test. No candidate satisfies all three simultaneously — and manufacturing one that did would risk being "optimized to make DSSA look good" rather than scientifically interpretable, which this audit was explicitly told not to do.

---

**STOP.** No dataset has been selected. No methodology, hypothesis, or frozen specification has been modified. No implementation code was written. This audit is ready for team review and decision.
