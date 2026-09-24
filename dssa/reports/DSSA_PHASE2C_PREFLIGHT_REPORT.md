# DSSA Phase 2C — Implementation Pre-Flight Report

**IMPLEMENTATION PREFLIGHT — NOT EXPERIMENTAL RESULT.** Every numeric result in this document (losses, validation mIoU, etc.) comes from a tiny, deliberately-underspecified dry run whose only purpose is to prove the training/evaluation code is correct. None of these numbers may be used in the paper, compared across conditions, or treated as evidence about DSSA, Early, Middle, Late, Lowest-DSS, or Random-K.

**Full 39-run training matrix is NOT yet authorized.**

---

## 1. Purpose and Scope

Per the Phase 2C authorization, this pre-flight implements the full training/evaluation infrastructure (dataset loader, decoder, fused-qkv Q/V-slice LoRA, loss, validation, sliding-window inference tiling, metrics, checkpoint management, experiment manifest, efficiency measurement) exactly per `DSSA_PHASE2B_B_TRAINING_PROTOCOL_FREEZE.md` and `dssa/config/phase2b_training_protocol.json`, then runs a tiny (2–4 step) implementation dry run to verify every required pre-flight condition before the real 39-run matrix is launched.

## 2. Environment

- Device: `mps` (Apple M5), PyTorch 2.14.0, Python 3.12.13
- Backbone: Prithvi-EO-2.0-300M, revision `9eb1b1102806593963daa333bcc491b1c6f8562f` (unchanged, frozen)
- New code this phase: `dssa/train/` (dataset.py, decoder.py, lora.py, losses.py, metrics.py, tiling.py, model_wrapper.py, manifest.py, checkpoint.py, efficiency.py, train.py, preflight.py)

## 3. Pre-Flight Checks (13/13 PASS)

| # | Check | Result | Detail |
|---|---|---|---|
| 1 | Experiment manifest matches frozen 42-slot/39-run accounting | PASS | Built programmatically from `phase2b_training_protocol.json`; 42 slots → 39 unique runs, 3 collisions, matching the frozen counts exactly |
| 2 | Decoder parameter count = 2,766,726 | PASS | Exact match |
| 3 | LoRA parameter count per selected block = 32,768 | PASS | Exact match |
| 4 | K=0 model contains decoder parameters only | PASS | trainable=2,766,726, zero LoRA modules created |
| 5 | K=8 model: LoRA only on selected Q/V slices, params match frozen accounting | PASS | total=306,915,206, trainable=3,028,870 (decoder=2,766,726, LoRA=262,144), frozen backbone=303,886,336 |
| 6 | Forward pass shape correct, loss finite, backward finite | PASS | logits shape (4,6,224,224); all 50 trainable tensors received finite gradients |
| 7 | Optimizer updates only intended trainable params; frozen backbone unchanged | PASS | A non-LoRA backbone weight and the frozen original `qkv` weight were bit-identical before/after one `optimizer.step()`; decoder and LoRA weights changed as expected |
| 8 | Checkpoint save/load reproduces predictions exactly | PASS | Max abs difference between pre-save and post-load logits on a fixed input = 0.00e+00 |
| 9 | target-train/validation partitions disjoint from target-test (test not loaded) | PASS | train=20, val=5, test=8; only filename lists were diffed — no test image or label content was ever read |
| 10 | Tiny end-to-end training run, K=0 (decoder-only path) | PASS | 2 steps, 1 validation pass, checkpoint saved |
| 11 | Tiny end-to-end training run, K=8 (LoRA path, includes checkpointing) | PASS | 4 steps, 2 validation passes, checkpoint saved |
| 12 | Validation metrics finite and valid across tiny runs | PASS | mIoU/F1/pixel-accuracy all finite; per-class IoU in [0,1] or `null` (class absent from the small eval crop) |
| 13 | Confusion matrix is valid (6×6, non-negative, correct pixel count) | PASS | Verified independently on a synthetic random prediction/target pair |

Full machine-readable results: `dssa/artifacts/phase2c/phase2c_preflight_report.json`.

**Preflight-only speed accommodations (disclosed, not used in real runs):** the tiny runs above used 2–4 training steps (vs. the frozen 2000), and validation was restricted to 1 target-validation file cropped to 448×448 (vs. all 5 full-size files) purely to bound dry-run wall-clock time. Neither accommodation touches any frozen scientific-protocol value — `train.py`'s real entry point defaults to the full 2000-step/200-step-checkpoint/all-5-validation-file protocol, and the real matrix will call it with no overrides.

## 4. Bug Policy — One Implementation Bug Found and Fixed

- **Symptom:** the K=8 tiny run's checkpoint file was 112.9 MB, roughly 10× the expected ~12.1 MB (2,766,726 decoder + 262,144 LoRA floats × 4 bytes ≈ 12.1 MB).
- **Root cause:** `LoRAQKV.state_dict()` (called naively by the first checkpoint implementation) also serializes the frozen `orig_qkv` `nn.Linear(1024, 3072)` submodule it wraps (≈3.15M frozen floats per wrapped block × 8 blocks ≈ 100.8 MB), because it is a PyTorch child module of the LoRA wrapper.
- **Affected component:** `dssa/train/checkpoint.py` only — no other module.
- **Correction:** `save_checkpoint`/`load_checkpoint` now explicitly save/load only the four LoRA tensors (`lora_A_q`, `lora_B_q`, `lora_A_v`, `lora_B_v`) per wrapped block, never `orig_qkv`'s weights (which are frozen, identical across every run, and reloaded fresh from the Prithvi checkpoint by `build_model()` regardless).
- **Was any already-produced result invalid?** No. This is a storage-efficiency bug, not a correctness bug — the checkpoint-roundtrip test (predictions identical, max abs diff = 0.00e+00) passed both before and after the fix. No experimental run had been executed yet (only preflight dry runs), so nothing needed to be invalidated or rerun for scientific reasons; the preflight was simply rerun to confirm the fix (all 13 checks still pass, K=8 checkpoint now 12.1 MB).
- This is a disclosed, transparent fix, not a silent protocol change — nothing in `DSSA_PHASE2B_B_TRAINING_PROTOCOL_FREEZE.md` or `phase2b_training_protocol.json` was touched.

No scientific-design questions were encountered; no frozen protocol value was found to be impossible to implement as written.

## 5. Architecture Findings Confirmed at Implementation Time

- `timm.layers.attention.Attention.forward` reshapes the fused `qkv` output as `(B, N, 3, num_heads, head_dim)` before `permute(2,0,3,1,4)` — confirming, by direct execution (not just source reading), that Q occupies output rows `0:1024`, K rows `1024:2048`, V rows `2048:3072`. This matches the Phase 2B-B resolution exactly.
- `SegDecoder`'s exact parameter count (2,766,726) and `LoRAQKV`'s exact parameter count (32,768/block) were verified by direct instantiation and counting, not just by hand arithmetic.

## 6. What Was NOT Done

- No experimental run (any of the 39 unique frozen-matrix runs) was executed.
- No target-test label was loaded, read, or evaluated against.
- No hyperparameter, architecture, loss, seed, or K-grid value was changed from the frozen protocol.
- No method was ranked or compared; the tiny-run numbers above are implementation-verification artifacts only, not results.

## 7. Files Created

- `dssa/train/dataset.py`, `decoder.py`, `lora.py`, `losses.py`, `metrics.py`, `tiling.py`, `model_wrapper.py`, `manifest.py`, `checkpoint.py`, `efficiency.py`, `train.py`, `preflight.py`
- `dssa/artifacts/phase2c/phase2c_preflight_report.json`
- `dssa/artifacts/phase2c/preflight_checkpoints/` (tiny dry-run checkpoints; gitignored — trainable-parameter-only `.pt` files, not source)
- `dssa/reports/DSSA_PHASE2C_PREFLIGHT_REPORT.md` (this document)

---

## PHASE 2C PRE-FLIGHT COMPLETE — FULL TRAINING NOT YET AUTHORIZED.
