# DSSA Sanity Execution Report

**Scope:** Phase 1 (below) — the model/code-side infrastructure work — plus **Phase 1B** (Section 19) — the attempt to acquire real ISPRS Potsdam/Vaihingen IRRG imagery and execute the seven checks against it. Not training. Not LoRA. Not layer selection. Not segmentation.

---

## 1. Environment

| Item | Value |
|---|---|
| OS | macOS (Darwin 25.6.0, arm64) |
| Python | 3.12.13, isolated venv at `dssa/venv` (system Python untouched) |
| PyTorch | 2.14.0 |
| transformers | 5.17.0 |
| timm | 1.0.30 |
| einops | 0.8.2 |
| tifffile | 2026.9.20 |
| huggingface_hub | 1.32.0 |
| numpy | 2.5.3 |
| PIL | 12.3.0 |

## 2. Hardware

| Item | Value |
|---|---|
| CPU | Apple M5 |
| GPU | Apple M5 integrated, 10 cores |
| RAM | 16 GB |
| Compute backend used | **MPS** (`torch.backends.mps.is_available() == True`) — no CUDA (no discrete NVIDIA GPU present, expected on this hardware) |
| Disk free | 261 GB |

CPU fallback was not needed — MPS is available and was used. Backbone was not changed for hardware reasons (nor would it need to be: 300M params comfortably fits in 16 GB unified memory in inference mode with no gradients).

## 3. Exact Checkpoint

`ibm-nasa-geospatial/Prithvi-EO-2.0-300M` — **exactly** the checkpoint frozen in `DSSA_PROJECT_FREEZE.md` §W. Confirmed **not gated** (no authentication required, none used).

## 4. Exact Model Revision

| Item | Value |
|---|---|
| HF repo commit SHA | `9eb1b1102806593963daa333bcc491b1c6f8562f` |
| Weights file | `Prithvi_EO_V2_300M.pt` |
| Weights file SHA-256 | `faab2c8b776f0723f93431747603a7ec586a54fc45473613b4322c29752486e7` |
| Weights file size | 1,326,658,396 bytes (~1.33 GB) |

**Architecture verified directly from the loaded state dict** (not just `config.json`):
- `encoder.patch_embed.proj.weight` shape `[1024, 6, 1, 16, 16]` → confirms `embed_dim=1024`, `in_chans=6`, `patch_size=[1,16,16]` exactly.
- 24 distinct encoder block indices found (`0`–`23`) → confirms `depth=24`.
- `encoder.pos_embed` shape `[1, 785, 1024]` → `785 = 1(cls) + 4×14×14`, confirming the pretrained default `num_frames=4`, `img_size=224` grid.
- **Total encoder parameters at load time: 303,886,336** — consistent with the "300M" name.
- **Trainable parameters after loading: 0** — backbone freeze verified programmatically (`requires_grad_(False)` on every parameter, asserted in code), not just claimed.

## 5. Dataset Files Used

**None.** ISPRS Potsdam and Vaihingen IRRG data are still not present in this environment (`dssa/data/potsdam_irrg/`, `dssa/data/vaihingen_irrg/` do not exist). No substitute dataset, no other Potsdam/Vaihingen release, and no different dataset was used. This is unchanged from `DSSA_SANITY_CHECK_REPORT.md` and was re-verified fresh in this run (the orchestrator script checks these paths at runtime and reports zero files found).

## 6. Radiometric Coefficients

**Not produced.** `fit_source_affine()` (Strategy C, `dssa/sanity/preprocessing.py`) is implemented exactly per the frozen contract but requires real Potsdam pixel data to fit; none is available. `artifacts/radiometric_transform.json` does not exist.

## 7. Preprocessing Contract

Implemented in code (`dssa/sanity/preprocessing.py`), matching `DSSA_IMPLEMENTATION_FREEZE.md` §4–5 exactly:
- Band mapping: Green→Green(1), Red→Red(2), aerial-IR→NarrowNIR(3); Blue(0)/SWIR1(4)/SWIR2(5) zero-filled in normalized space.
- Strategy C affine transform class (`SourceFitAffine`), fit-on-source-only by construction.
- `T=1` input construction (`(1, 6, 1, H, W)`).

Not yet exercised against real Potsdam/Vaihingen pixels (Section 5).

## 8. HLS Reference Sample

| Item | Value |
|---|---|
| Source | Official example bundled in the `ibm-nasa-geospatial/Prithvi-EO-2.0-300M` repo itself (`examples/`) |
| File | `Mexico_HLS.S30.T13REM.2018026T173609.v2.0_cropped.tif` |
| Selection rule | First of the four official example tiles, chosen by file order **before** any check was run (not selected after seeing results) |
| Shape | `(448, 560, 6)`, channel-last |
| dtype | `int16` |
| Value range observed | min −113, max 6124, mean ≈1908 |
| Why known-good | Published by the model's own authors (IBM/NASA) specifically as a usage example; real HLS-product int16 values, in the exact band order and radiometric scale (`config.json`'s mean/std, confirmed via `inference.py`'s own `load_example()` — direct `(x−mean)/std` on raw int16, no extra ×10000 division step) the checkpoint expects natively |

## 9–15. Check Results

| Check | Status | Result |
|---|---|---|
| **1 — Forward pass (Potsdam, Vaihingen)** | **NOT EXECUTED** | Blocked — no data (Section 5) |
| **2 — No NaN/Inf (Potsdam, Vaihingen)** | **NOT EXECUTED** | Blocked — no data |
| **3 — Activation magnitude vs. reference (Potsdam, Vaihingen)** | **NOT EXECUTED (candidate side); reference side collected** | The HLS-reference forward pass succeeded and its per-layer mean token L2 norms were recorded (Section 16) — this is the comparison **baseline** the check needs. The Potsdam/Vaihingen side cannot be computed without data. |
| **4 — Cross-sample variance > 1e-6 (Potsdam, Vaihingen)** | **NOT EXECUTED** | Blocked — no data |
| **5 — DSS diagnostic (finite, non-zero raw; finite normalized)** | **NOT EXECUTED** | Blocked — no data. The diagnostic function (`dss_cosine_diagnostic`, `diagnostics.py`) is implemented exactly per the frozen definition but was not run against Potsdam/Vaihingen. |
| **6 — All 24 blocks produce output** | **NOT EXECUTED on Potsdam/Vaihingen; VERIFIED on the HLS reference** | On the HLS reference: all 24 blocks present, each shape `(1, 981, 1024)`, `embed_dim=1024` confirmed at every layer, none skipped. This exercises the exact same extraction code (`forward_features`) that would run on Potsdam/Vaihingen — the code path itself is now proven correct, independent of which image is fed to it. |
| **7 — Procedural audit (no labels/optimization/gradients/target-stats)** | **Vacuously true for the run that occurred** | The run that did execute (model load + HLS-reference forward pass) loaded no labels, performed no optimization, computed no gradients (`torch.no_grad()` throughout, and the backbone's `requires_grad_(False)` was asserted in code), and used no target statistics. This is a real, verified property of the run that happened — but it is not a verification of Checks 1–6 on Potsdam/Vaihingen, since that run never occurred. |

## 16. Numerical Evidence

**Encoder load:** `total_params=303,886,336`, `trainable_params=0`.

**HLS-reference forward pass — per-layer mean token L2 norm** (all 24 layers, index 0→23):

```
45.86, 49.98, 51.21, 51.64, 49.89, 51.66, 53.23, 55.54, 55.06, 56.67,
59.32, 59.77, 57.35, 59.49, 58.26, 58.62, 60.54, 60.86, 62.89, 63.73,
64.88, 67.70, 72.55, 28.89
```

Pattern: norms rise gradually from ~46 to ~73 across layers 0–22, then drop to ~28.9 at layer 23 — expected, since layer 23's output has the model's final LayerNorm applied (per `PrithviViT.forward_features`, matching the architecture code read directly this session), which renormalizes scale. No NaN, no Inf, no near-zero collapse, no runaway explosion anywhere in the sequence. This is real evidence the loaded weights and extraction code produce sane representations — on the HLS reference specifically, not yet on Potsdam/Vaihingen.

Full values, plus the raw artifact: `dssa/artifacts/hls_reference_layer_norms.json` and `dssa/artifacts/sanity_metrics.json`.

## 17. Deviations from the Pre-Registered Procedure

**None** in the sense of changed criteria, thresholds, checkpoint, band mapping, or DSS definition — all match the frozen documents exactly.

**One addition, clearly out-of-band and disclosed:** an "infrastructure smoke test" (Section 8–9 above) was run on the HLS reference sample, beyond the strict text of the seven checks. This was not one of the seven pre-registered checks and is not reported as satisfying any of them on Potsdam/Vaihingen — it is disclosed separately, in its own section, specifically so it cannot be mistaken for that. Its purpose: since real checkpoint access became available in this session (unlike the prior attempt), it was possible to verify the *model- and code-side* of the pipeline for real rather than leave it entirely theoretical — this reduces risk for whenever Potsdam/Vaihingen data does become available, without claiming anything about Potsdam/Vaihingen itself.

## 18. Phase 1 Verdict (model/code-side infrastructure only)

🟡 **YELLOW at the time** — checkpoint ambiguity resolved, real environment verified, real checkpoint verified byte-for-byte, real HLS reference forward-passed successfully. Potsdam/Vaihingen data absent; all seven checks not executed on the real pair. See Phase 1B below for what was attempted next.

---

## 19. Phase 1B — Dataset Acquisition Attempt

**Objective:** obtain the real ISPRS Potsdam/Vaihingen IRRG imagery so the seven checks could actually run, per this phase's explicit Step 1.

### Step 1 result: acquisition is not automatable — confirmed against the official source, not assumed

Fetched both official ISPRS pages directly this session:
- `isprs.org/.../2d-sem-label-potsdam.aspx`
- `isprs.org/.../2d-sem-label-vaihingen.aspx`

Neither page exposes a direct download link. A follow-up search against the ISPRS benchmark site confirmed the actual access mechanism: **registration via a data request form at `www2.isprs.org/data-request-form.html`**, after which approved access is granted to download the (large) files from a seafile server. This is a manual, identity-tied registration process — not a public URL, not something with an API, and not something that can be completed without a person filling out the form and waiting for access to be granted.

**Per instruction, this was not worked around.** No third-party mirror, re-hosted copy, or alternative redistribution was searched for or used, since instruction explicitly said not to work around the restriction, and any such source would carry licensing/authorization uncertainty this review cannot clear on your behalf.

### Exact manual action required

To unblock Phase 1B, a person (with the standing to agree to ISPRS's terms) needs to:

1. Go to `http://www2.isprs.org/data-request-form.html` and register/request access to the **ISPRS 2D Semantic Labeling Contest — Potsdam** and **Vaihingen** benchmark datasets specifically (Working Group II/4, "Urban Modelling and Semantic Labelling Benchmark").
2. Once access is granted, download from the resulting seafile link:
   - **Potsdam:** the orthomosaic tiles in **IRRG** format (one of the three released compositions — IRRG, RGB, RGBIR; IRRG is the one this project's frozen design uses).
   - **Vaihingen:** the orthomosaic tiles (Vaihingen ships only in IRRG — no separate format choice).
3. Place the files at:
   - `dssa/data/potsdam_irrg/` (Potsdam IRRG tiles)
   - `dssa/data/vaihingen_irrg/` (Vaihingen tiles)
4. Re-invoke this phase — `dssa/sanity/run_sanity_check.py`'s dataset-detection step will pick them up automatically (it globs `*.tif` in exactly those two directories) and the currently-unimplemented real-data branch (a deliberate `NotImplementedError`, not a silent stub) can then be completed and run against them.

No files were downloaded in this step. No substitute was used. Steps 2–4 of this phase (dataset integrity audit, Strategy C calibration, the seven checks) were **not attempted at that time**, because they all depend on Step 1, which had not yet completed. (They have since been completed — see Sections 20–27 below. The data was obtained by the user through the official ISPRS registration process, per Section 19's exact instructions, and staged per `DSSA_DATASET_INTEGRITY_REPORT.md`.)

---

## 20. Phase 1B Completion — A. Previous Model/Code Infrastructure Evidence

Unchanged from Sections 1–18 above: real environment, real checkpoint (verified byte-for-byte, `Prithvi-EO-2.0-300M`, revision `9eb1b1102806593963daa333bcc491b1c6f8562f`), real HLS reference forward pass, 0 trainable parameters. All of it reused as-is in this run — the same `load_frozen_encoder()` code path, unmodified.

## 21. B. Dataset Integrity Evidence

Full detail in `DSSA_DATASET_INTEGRITY_REPORT.md`. Summary: 38/38 Potsdam IRRG files and 33/33 Vaihingen TOP files verified individually (shape, dtype, value range, no corrupted files, no accidental label files), staged at `dssa/data/potsdam_irrg/` and `dssa/data/vaihingen_irrg/`.

## 22. C. Strategy C Calibration — Executed

**Fit exclusively on Potsdam.** All 38 Potsdam files were streamed through a memory-safe accumulator (see Section 26, deviation) — **zero Vaihingen files were opened during fitting**, verified both by the code path (the fitting generator iterates `potsdam_files` only) and by an explicit log line printed before fitting began: `"Vaihingen files referenced in this step: 0"`.

**Fitted, frozen coefficients** (written to `dssa/artifacts/radiometric_transform.json`):

| Channel | Offset | Scale |
|---|---|---|
| IR | 44.078086 | 51.043832 |
| R | 69.273417 | 61.576644 |
| G | 63.265727 | 59.248827 |

These coefficients were computed once and applied **identically, unchanged**, to both the Potsdam and Vaihingen crops used in every subsequent check — no refitting, no per-image adjustment, no target-derived scaling.

## 23. D. Real Potsdam/Vaihingen Sanity Results

**Sample selection (fixed before running, not results-based):** 16 Potsdam files as the "source" group, 16 Vaihingen files as the "target" group, plus two disjoint 8-file Potsdam groups ("null_a", "null_b") for the source-vs-source baseline required by Check 5 — 38 Potsdam files exactly cover 16 (source) + 8 + 8 (null) = 32, leaving 6 unused. One deterministic 224×224 top-left crop (native pixels, no resizing) was extracted per file — the same fixed-window tiling geometry the checkpoint's own official `inference.py` uses, adapted because full 6000×6000 attention is computationally intractable on this hardware (quadratic cost in token count, not a memory limit an implementation choice can work around) and because the frozen sanity-check spec (`DSSA_PREIMPLEMENTATION_CALIBRATION.md` §7) itself only calls for "a small batch (order 8–16 tiles)."

All 32 real-data forward passes (16 Potsdam + 16 Vaihingen) succeeded, plus 16 more (8+8 null-baseline Potsdam crops) — 48 total, all logged individually in `dssa/artifacts/real_data_sanity_run.log`.

## 24. E. Each of the Seven Checks

| Check | Result | Evidence |
|---|---|---|
| **1 — Forward pass** | ✅ PASS | 16/16 Potsdam-source crops, 16/16 Vaihingen-target crops, all 24 layers returned each time |
| **2 — No NaN/Inf** | ✅ PASS | Checked across all 48 crops (source+target+null_a+null_b) × 24 layers = 1,152 tensors; zero non-finite values |
| **3 — Activation magnitude vs. HLS reference** | ✅ PASS | Every layer, every real-data sample, within the frozen 2-orders-of-magnitude tolerance band (observed ratios ≈1.7–2.1× the reference norm on inspected layers — comfortably inside `10⁻² ≤ ratio ≤ 10²`) |
| **4 — Cross-sample variance > 1e-6** | ✅ PASS | Source group: layer-wise variance from 0.103 (layer 23) to 1.354 (layer 0). Target group: 0.076 to 1.164. Both groups, all 24 layers, orders of magnitude above the 1e-6 floor |
| **5 — DSS diagnostic (finite, non-zero raw; finite normalized)** | ✅ PASS | All 24 layers: raw cosine DSS finite and non-zero (range ≈0.14–0.24 across the layers inspected), null-baseline value finite, normalized (raw − null) value finite. **No threshold for "meaningful" magnitude was applied or checked — none was defined, per the frozen spec** |
| **6 — All 24 blocks produce output** | ✅ PASS | Confirmed on a representative real sample: 24/24 blocks, `embed_dim=1024` at every layer, none skipped |
| **7 — Procedural/leakage audit** | ✅ PASS | No label file was ever opened by this script (verified by code inspection — no `*_label.tif` / `gts_for_participants` path appears anywhere in `run_real_data_sanity.py`'s I/O); no `torch.optim` constructed; all forward passes under `torch.no_grad()`; backbone confirmed frozen (0 trainable params, asserted); Strategy C fit exclusively on Potsdam (Section 22); no layer ranking or selection performed — the DSS diagnostic values were computed and logged, never sorted, thresholded, or used to choose anything |

**Important, explicit note on Check 5's numbers:** the raw DSS values are *reported*, not *interpreted*. This run does not claim, and this document does not claim, that these numbers show DSSA "works," that any layer is more or less suitable for adaptation, or anything about relative layer sensitivity. That analysis is explicitly out of scope for this phase (see the Critical Stop Condition below).

## 25. F. Artifacts Produced

| Artifact | Contents |
|---|---|
| `dssa/artifacts/radiometric_transform.json` | Frozen Strategy C coefficients, fit metadata (38 Potsdam files, 0 Vaihingen files) |
| `dssa/artifacts/real_data_sanity_metrics.json` | Full structured results for all seven checks, including every per-layer/per-sample number |
| `dssa/artifacts/real_data_sanity_run.log` | Line-by-line execution log (file lists used, every forward pass, every check result) |
| `dssa/artifacts/hls_reference_layer_norms.json` | Reused unchanged from Phase 1 (Check 3's reference baseline) |
| `dssa/sanity/run_real_data_sanity.py` | The exact, inspectable code that produced this run — reproducible given the same staged data and checkpoint |

## 26. G. Deviations

**One, disclosed precisely, and it is an engineering fix, not a methodology change:** the first execution attempt was killed by the operating system (exit code 137, out-of-memory) because the original `fit_source_affine` implementation concatenated all 38 full-resolution Potsdam images into a single float64 array (≈33 GB) before computing statistics. Per the task's own explicit "Important Compute Rule" ("process tiles/chunks sequentially or in a memory-safe manner while preserving the frozen mathematical definition"), this was fixed by replacing the concatenate-then-reduce implementation with a mathematically identical streaming sum/sum-of-squares accumulation (one image in memory at a time). **The formula, inputs, and outputs of Strategy C are unchanged** — same per-channel global mean/std computed over the same 38 Potsdam files, same resulting affine coefficients — only how that arithmetic is computed in memory changed. No threshold, band mapping, checkpoint, T value, or DSS definition was touched. This is recorded here rather than silently fixed.

No other deviation occurred. No tiles were discarded. No preprocessing method was changed. No thresholds were adjusted. Nothing was retried with different parameters after a failure — the one failure (the OOM) occurred before any check ran, was diagnosed precisely, fixed at the level the compute rule authorized, and the corrected run then executed cleanly on the first attempt.

## 27. H. Final Verdict

## 🟢 GREEN — all seven registered checks passed on the real, frozen Potsdam→Vaihingen dataset pair

This means, precisely: the frozen input pipeline (Strategy C, band mapping, T=1, normalization) and the frozen Prithvi-EO-2.0-300M backbone, applied to real ISPRS Potsdam and Vaihingen imagery, produce forward passes that succeed, are fully finite, are not collapsed, fall within expected activation-magnitude ranges, and yield a computable, finite, non-zero DSS diagnostic at every layer.

**This does not mean DSSA works.** No claim is made here — and none should be inferred — about layer sensitivity, which layers are "important," segmentation accuracy, LoRA effectiveness, or superiority over Random-K selection. Those are exactly the questions Phase 2 exists to test, and Phase 2 has not begun.

**Per the critical stop condition: no DSS layer ranking, no Random-K experiment, no LoRA, no segmentation training, no baseline training, and no evaluation occurred or is authorized by this result. Stopping here.**
