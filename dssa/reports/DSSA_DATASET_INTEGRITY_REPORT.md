# DSSA Dataset Integrity Report — Phase 1B, Step 1

**Scope:** locate, verify, and stage the official ISPRS Potsdam and Vaihingen imagery. No Strategy C fitting. No sanity checks run. No labels touched by the sanity pipeline. Stops after this audit, per instruction.

---

## 1. Source Directories (as delivered)

| Dataset | Source | Size |
|---|---|---|
| Potsdam | `dssa/Data/Potsdam/` (+ `Potsdam.zip`, unopened) | ~26 GB extracted contents |
| Vaihingen | `dssa/Data/Vaihingen/` (+ `Vaihingen.zip`, unopened) | ~1.8 GB extracted contents (plus the large source zip) |

Both delivered under `dssa/Data/` — the official ISPRS download structure, confirmed by filenames matching the ISPRS 2D Semantic Labeling release convention exactly (`N_<description>.zip` for Potsdam; named component archives for Vaihingen).

## 2. Directory/File Structure Found

**Potsdam** (`dssa/Data/Potsdam/`): ten top-level archives —
`1_DSM_normalisation.zip`, `1_DSM.rar`, `2_Ortho_RGB.zip`, **`3_Ortho_IRRG.zip`**, `4_Ortho_RGBIR.zip`, `5_Labels_all_noBoundary.zip`, `5_Labels_all.zip`, `5_Labels_for_participants_no_Boundary.zip`, `5_Labels_for_participants.zip`, `assess_classification_reference_implementation.tgz`.

**Vaihingen** (`dssa/Data/Vaihingen/`): a mix of loose files and directories — `3DLabeling/`, `ALS/` (LAS point clouds), `DSM/`, `dsm_09cm_matching_area11.tif`, `Images/` (25 raw, un-orthorectified flight-strip captures, ~857 MB each — **not** the TOP product), `ISPRS_semantic_labeling_Vaihingen_ground_truth_COMPLETE.zip`, `ISPRS_semantic_labeling_Vaihingen_ground_truth_eroded*.zip` (×2), **`ISPRS_semantic_labeling_Vaihingen.zip`**, `Overview_Vaihingen_DMC.pdf`, `Ortho/TOP_Mosaic_09cm.tif` (a single, full-city, un-tiled mosaic — a different product from the standard 33-tile release), `Reference_3d_reconstruction/`, `Reference_object_detection/`, `Vaihingen_dsm_tiles_geoinfo.zip`.

## 3. Identifying the Required Imagery — Resolved, With One Genuine Ambiguity Investigated and Cleared

### Potsdam: unambiguous by filename
`3_Ortho_IRRG.zip` — name matches the required "IRRG orthophoto" exactly, and is clearly distinct from `2_Ortho_RGB.zip`, `4_Ortho_RGBIR.zip`, and the `5_Labels_*.zip` files by filename alone. Listed (not extracted) first to confirm internal naming: 38 members matching `3_Ortho_IRRG/top_potsdam_<row>_<col>_IRRG.tif`, each with a `.tfw` world-file sidecar.

### Vaihingen: **not** unambiguous by filename alone — investigated before acting

Vaihingen has three candidate "imagery-looking" sources, and this dataset has a well-known naming trap: its ground-truth label rasters are named with the *identical* `top_mosaic_09cm_area<N>.tif` pattern as the real imagery. Filename alone cannot distinguish them. Three candidates were compared:

1. `Ortho/TOP_Mosaic_09cm.tif` — a single 1.3 GB file. This is the full, un-tiled city-wide mosaic — a different, non-standard product, not the tile set virtually every published benchmark uses.
2. `Images/*.tif` (25 files, ~857 MB each) — inspected by name and file size: these are raw, un-orthorectified flight-strip captures (named by flight/strip codes, e.g. `10030060.tif`), not the orthorectified TOP product at all.
3. **`ISPRS_semantic_labeling_Vaihingen.zip`**, containing three subfolders: `dsm/` (34 entries, elevation), `gts_for_participants/` (17 entries, **filenames identical in pattern to the imagery** — `top_mosaic_09cm_area<N>.tif`), and `top/` (34 entries, same filename pattern again).

Because two of these three subfolders share the exact same filename pattern, **filenames could not settle which was imagery and which was ground truth.** Per instruction, this was not guessed — one file from `top/` and the correspondingly-numbered file from `gts_for_participants/` (both `area1.tif`) were extracted (read-only, from the zip, without modifying the original archive) and inspected pixel-by-pixel:

| | `top/top_mosaic_09cm_area1.tif` | `gts_for_participants/top_mosaic_09cm_area1.tif` |
|---|---|---|
| Shape | (2569, 1919, 3) | (2569, 1919, 3) — identical, confirming same tile |
| dtype | uint8 | uint8 |
| Unique values, band 0 | 241 (broad, continuous) | **2** |
| Unique values, band 1 | 239 | **2** |
| Unique values, band 2 | 238 | **2** |

A band with only 2 distinct 8-bit values across an entire 2569×1919 tile is a flat, small-palette label mask (ISPRS's fixed 6-class RGB color code), not photographic imagery. **`gts_for_participants/` is ground truth; `top/` is the real imagery.** This resolved the ambiguity with direct pixel evidence rather than an assumption.

**Conclusion:** the required Vaihingen imagery is `top/top_mosaic_09cm_area<N>.tif` inside `ISPRS_semantic_labeling_Vaihingen.zip` — 33 files, matching the official, standard, widely-used Vaihingen tile release exactly (area numbers 1–38 with known gaps at 9, 18, 19, 25, 36).

## 4. Full Verification (all files, not a sample)

All 38 Potsdam files and all 33 Vaihingen files were individually opened (not just listed) and checked:

| | Potsdam | Vaihingen |
|---|---|---|
| Files found | 38 / 38 expected | 33 / 33 expected |
| TIFF readable | 38/38 | 33/33 |
| Channels | 3 (all files) | 3 (all files) |
| dtype | `uint8` (all files) | `uint8` (all files) |
| Shape | `(6000, 6000, 3)`, identical across all 38 tiles | Variable per tile, from `(1281, 2336, 3)` to `(3313, 1917, 3)` — expected, matches the official spec ("resolutions ranging from 1996×1996 to 3816×2550") |
| Global value range | 1–255 | 0–255 |
| Bulk label-mask check (subsampled, every file, every band) | 0 suspicious bands (threshold: <20 unique values in a subsampled band) | 0 suspicious bands |
| Corrupted/unreadable files | None | None |

No corrupted files. No unexpected shapes. No accidental label files among the 71 staged files.

## 5. Files Explicitly Excluded From the Sanity Pipeline

| Category | Examples | Reason |
|---|---|---|
| RGB / RGBIR orthophotos | `2_Ortho_RGB.zip`, `4_Ortho_RGBIR.zip` | Frozen spec requires IRRG specifically |
| DSM / nDSM (elevation) | `1_DSM*.zip`, `Vaihingen/DSM/`, `dsm/` (inside the Vaihingen zip) | Not imagery; not part of the frozen input contract |
| Labels / ground truth | `5_Labels_*.zip` (Potsdam), `ISPRS_..._ground_truth*.zip`, `gts_for_participants/` (inside the Vaihingen zip) | **The sanity pipeline must not consume labels — confirmed none were extracted or staged** |
| Raw flight-strip captures | `Vaihingen/Images/*.tif` | Not the orthorectified TOP product |
| Full city mosaic (non-tiled) | `Vaihingen/Ortho/TOP_Mosaic_09cm.tif` | A different product from the standard tile release the frozen design and prior literature use |
| Point clouds / 3D reference | `Vaihingen/ALS/*.LAS`, `Vaihingen/3DLabeling/`, `Vaihingen/Reference_3d_reconstruction/`, `Vaihingen/Reference_object_detection/` | Different task entirely, not 2D imagery |
| World files, docs | `*.tfw`, `Overview_Vaihingen_DMC.pdf`, `*.dat`, `*.txt` | Georeferencing/documentation, not pixel imagery; not needed for the sanity pipeline |
| Reference implementation tooling | `assess_classification_reference_implementation.tgz` | Not data |

## 6. Staged Location

| | Path | Contents |
|---|---|---|
| Potsdam IRRG | `dssa/data/potsdam_irrg/` | 38 files, `top_potsdam_<row>_<col>_IRRG.tif` only (no `.tfw`) |
| Vaihingen TOP | `dssa/data/vaihingen_irrg/` | 33 files, `top_mosaic_09cm_area<N>.tif` only |

Files were **copied** (extracted fresh from the original zip archives) — the original downloads under `dssa/Data/` were not modified (verified: source zip modification timestamps unchanged, `2022-01-11`, before and after this operation). No file was moved or deleted from the original download.

## 7. Confirmation Against the Frozen Specification

| Frozen requirement (`DSSA_IMPLEMENTATION_FREEZE.md` §1) | Verified |
|---|---|
| Dataset pair: ISPRS Potsdam (IRRG) → ISPRS Vaihingen (IRRG) | ✅ Both confirmed as genuine IRRG/TOP imagery, not RGB/RGBIR/DSM/labels |
| No labels consumed | ✅ Zero label files extracted, staged, or opened by the imagery pipeline (the one `gts_for_participants` file opened was for the disambiguation check in Section 3 only, discarded immediately after, never staged) |
| Potsdam: 3-band, 8-bit | ✅ Confirmed, 38/38 files |
| Vaihingen: 3-band, 8-bit, NIR/R/G | ✅ Confirmed, 33/33 files (band-order/identity as NIR-R-G is the official ISPRS description of this exact TOP product; not independently re-verified spectrally in this step, consistent with the frozen radiometric contract which treats this as the given band identity) |

**No mismatch found. The discovered data satisfies the frozen specification.**

## 8. Not Done in This Step (by design)

- Strategy C affine transform was **not** fit.
- The seven pre-registered sanity checks were **not** run.
- No DSS computation of any kind occurred.
- No layer selection, LoRA, or training occurred.

---

**Step 1 (and its associated integrity audit) is complete. Stopping here, per instruction. Phase 1B Steps 3–6 (Strategy C fitting, the seven checks, and the final report update) require the next explicit authorization.**
