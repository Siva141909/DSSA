"""
DSSA Phase 2C - sliding-window inference (validation/test).

Frozen policy (DSSA_PHASE2B_B_TRAINING_PROTOCOL_FREEZE.md Step 10):
224x224 windows, stride 112 (50% overlap), reflect-padded to a size that
tiles exactly, overlapping logits averaged (not majority vote) before a
single final argmax over the 6 classes.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sanity"))
import preprocessing as dssa_prep  # noqa: E402

CROP = 224
STRIDE = 112
NUM_CLASSES = 6


def _padded_size(size: int, crop: int = CROP, stride: int = STRIDE) -> int:
    if size <= crop:
        return crop
    extra = size - crop
    steps = -(-extra // stride)  # ceil division
    return crop + steps * stride


def sliding_window_predict(model, calibrated_irrg: np.ndarray, device: str, batch_size: int = 8) -> np.ndarray:
    """
    calibrated_irrg: (H, W, 3) float array, already through Strategy C
    (SourceFitAffine.apply), channel order (IR, R, G).
    Returns: (H, W) int64 predicted class-index array, same size as input
    (padding cropped back out before returning).
    """
    h, w, _ = calibrated_irrg.shape
    h_pad, w_pad = _padded_size(h), _padded_size(w)
    pad_h, pad_w = h_pad - h, w_pad - w
    padded = np.pad(calibrated_irrg, ((0, pad_h), (0, pad_w), (0, 0)), mode="reflect")

    sum_logits = torch.zeros((NUM_CLASSES, h_pad, w_pad), dtype=torch.float32)
    counts = torch.zeros((1, h_pad, w_pad), dtype=torch.float32)

    ys = list(range(0, h_pad - CROP + 1, STRIDE))
    xs = list(range(0, w_pad - CROP + 1, STRIDE))
    windows = [(y, x) for y in ys for x in xs]

    model.eval()
    with torch.no_grad():
        for batch_start in range(0, len(windows), batch_size):
            batch = windows[batch_start:batch_start + batch_size]
            crops = [padded[y:y + CROP, x:x + CROP, :] for y, x in batch]
            tensors = [dssa_prep.build_prithvi_input(c) for c in crops]  # each (1,6,1,224,224)
            x_batch = torch.cat(tensors, dim=0).to(device)
            logits = model(x_batch)  # (B,6,224,224)
            logits_cpu = logits.detach().cpu()
            for (y, x), lg in zip(batch, logits_cpu):
                sum_logits[:, y:y + CROP, x:x + CROP] += lg
                counts[:, y:y + CROP, x:x + CROP] += 1.0

    avg_logits = sum_logits / counts.clamp(min=1.0)
    avg_logits = avg_logits[:, :h, :w]
    pred = avg_logits.argmax(dim=0).numpy().astype(np.int64)
    return pred
