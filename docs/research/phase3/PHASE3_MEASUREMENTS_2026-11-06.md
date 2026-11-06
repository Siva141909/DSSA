# Phase 3: bounded measurements A and B (2026-11-06)

Both were authorised as engineering measurements. **They are not scientific runs and are not part of
the Stage C or D counts.**
- **Code location:** disposable scripts in the session scratch folder (`phase3_measure/measure_a.py`,
  `measure_b.py`). They import project modules read-only, with bytecode writing disabled.
- **Project state:** no files were written in the project, no `__pycache__` was created, and the
  `dssa/phase2d` code hash and frozen artifacts were unchanged.
- **Restricted data:** no Potsdam labels, no test imagery, no LoveDA, and no checkpoints read or
  written.

## Measurement A: Potsdam memory and evaluation throughput
- **Tile.** `top_potsdam_2_10_IRRG.tif`, 6000 × 6000 × 3, uint8, 103 MB. It is first in sorted order,
  so it is a training tile under the proposed positional split.
- **Path.** The Phase 2D evaluation path: `evaluation.window_logits` (224 windows, stride 112, averaged
  logits), with the frozen backbone and a randomly initialised decoder.
  - Forward only.
  - The full-tile Strategy C float64 calibration is used, as in `train.evaluate`.
- **Safety.** A sampler aborted at 11.0 GB. The full tile was run only after the partial-region
  projection was below 90% of 11.5 GB.

| Run | Region | Time | Throughput | Peak footprint (increment) | MPS driver peak |
|---|---|---|---|---|---|
| 1 | 1344² (1.81 MP) | 5.4 s | 2.98 s/MP | 3,414 MB (+165) | 2,124 MB |
| 2 | 2688² (7.23 MP) | 22.2 s | 3.08 s/MP | 4,073 MB (+645) | 2,132 MB |
| 3 | **6000² (36.0 MP)** | **116 s** | **3.22 s/MP** | **8,187 MB (+4,131)** | 2,132 MB |

- **Baselines.** The frozen model loaded in 3,170 MB of footprint (2,089 MB MPS driver). With the image
  loaded, 3,249 MB.
- **The linear projection undershot.** It predicted a +3,194 MB increment (+2,638 MB from analytic
  buffers); the measured value was **+4,131 MB**, about 30% higher, likely from float64 copies inside
  the calibration, padding and six-band construction. After the full tile the residual footprint was
  6,666 MB: the allocator did not return the memory.
- **Training cache for 20 Potsdam tiles.** Images 20 × 103 MB, plus labels 20 × 34.3 MB uint8. The label
  figure is **analytic: no label was read**. Total **2,747 MB**.

## Measurement B: uniform-LoRA timing
- **Configuration.**
  - LoRA rank 8 on Q/V in **all 24 blocks**: 786,432 LoRA parameters + 2,766,726 decoder parameters =
    3,553,158 trainable.
  - The Phase 2D recipe: AdamW 1e-3, warm-up cosine schedule, batch 8, crop 224, gradient clipping
    1.0, CE + Dice loss.
  - Seed 1000.
  - **50 steps, no evaluation, no checkpoint.**
- **Data.** Vaihingen **training** tiles only (labels already used in Phase 2D), under the project's
  `install_tile_allowlist`. Tiles opened: exactly the 20 training tiles.

| Item | Value |
|---|---|
| First 5 steps | 3.16, 1.62, 1.87, 1.33, 1.08 s (warm-up) |
| Steady state (steps 6–50) | **0.836 s per step** (min 0.814, max 1.144) |
| Projected 2,000-step training time | **1,673 s** = **1.10 ×** the Phase 2D L0 training time (1,521 s); v2 assumed 1.15 × |
| Peak footprint | **6,750 MB** (training only; Vaihingen cache 391 MB, all 20 tiles cached) |
| Peak MPS driver | 5,341 MB |
| Stability | Loss 2.587 → 1.648; maximum gradient norm 13.0 before clipping; no non-finite steps |

The uniform r1 arm has the same computation graph with smaller LoRA matrices, so its cost is ≤ the r8
figure (not measured separately).

## Memory verdict for Potsdam (11.5 GB limit)
| Process design | Projected or measured peak | Verdict |
|---|---|---|
| Training, worst case (uniform r8): 6,750 − 391 (Vaihingen cache) + 2,747 (Potsdam cache) | **≈ 9,100 MB** (projected) | **Safe** (≈ 2.4 GB margin) |
| Training with in-process Potsdam evaluation: + 4,131 | **≈ 13,200 MB** | **Unsafe** |
| Evaluation-only process, one full tile | **8,187 MB** (measured) | Safe for one tile |

**Consequence (D22).** Phase 3 must evaluate in a **separate process after training**, as reload
verification already does in Phase 2D. Training processes must never evaluate Potsdam tiles.

**Not measured:** the footprint of an evaluation process that runs **8 or 10 tiles sequentially**.
The residual 6.7 GB after one tile suggests the allocator retains memory. Before Stage C, either:
- run one bounded measurement of a 2-tile sequential evaluation (training tiles only, forward only); or
- evaluate one tile per process, at the cost of a model load per tile.

The Phase 2D reload overhead suggests about 0.5 min per load; this is unmeasured.
