# DSSA Sanity Execution Report

**Scope:** Phase 1 only — the seven pre-registered non-degeneracy checks (`DSSA_PREIMPLEMENTATION_CALIBRATION.md` §7). Not training. Not LoRA. Not layer selection. Not segmentation. This report supersedes `DSSA_SANITY_CHECK_REPORT.md` (prior attempt) with real, executed environment and checkpoint work — the dataset blocker that stopped that report is unchanged here.

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

## 18. Final Verdict

## 🟡 YELLOW — execution blocked/incomplete without changing criteria

**What changed since `DSSA_SANITY_CHECK_REPORT.md`:** the checkpoint ambiguity is resolved (backbone frozen to 300M), a real isolated environment now exists, the real checkpoint is downloaded and verified byte-for-byte (config, weight shapes, revision hash, checksum), and a real known-good HLS reference sample has been identified, downloaded, and forward-passed successfully with sane, finite, non-collapsed representations recorded at all 24 layers.

**What has not changed:** ISPRS Potsdam and Vaihingen IRRG data are still not present in this environment. All seven officially pre-registered checks remain **not executed** on the actual frozen dataset pair, because none was substituted, fabricated, or approximated. This is the same category of blocker as before — a missing external artifact — reported the same way, with no criteria loosened to compensate.

### What would need to happen for this to become GREEN or RED

1. Obtain ISPRS Potsdam and Vaihingen IRRG imagery (via the ISPRS access process) and place it at `dssa/data/potsdam_irrg/` and `dssa/data/vaihingen_irrg/`.
2. Re-run `dssa/sanity/run_sanity_check.py` — the `NotImplementedError` currently raised in that branch marks exactly where real-data wiring needs to be completed (radiometric fitting → input construction → the seven checks against real files), deliberately left unfilled rather than written blind against data that doesn't exist yet.
3. The result of that run — not this one — determines GREEN vs. RED.

No claim is made here about DSSA's hypothesis, layer sensitivity, segmentation accuracy, LoRA effectiveness, or superiority over Random-K. This phase only concerns whether the frozen pipeline can produce valid, non-degenerate representations — and even that has only been shown for the HLS reference sample, not yet for Potsdam or Vaihingen.

**Per instruction: this phase stops here. The next phase (obtaining data and completing the real-data run) requires separate authorization.**
