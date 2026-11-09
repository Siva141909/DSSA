"""Lower-memory replica of phase2d/evaluation.eval_tile (approved 2026-11-06 after K0
evaluation processes reached 10.14 GB). Same windows (224, stride 112, reflect padding),
same batch order, same averaged logits, same argmax:
  - the uint8 tile is reflect-padded and each window is calibrated on its own. Padding only
    copies pixels and Strategy C is per pixel, so every window is bit-identical to the
    window cut from the padded float64 calibrated tile (no full-tile float64 copies);
  - the logit sums are divided in place;
  - cross-entropy is summed over row chunks (CE only; changes by float rounding).
Verified against the original evaluator on all 24 K0 tile evaluations before use."""
from __future__ import annotations

import numpy as np
import torch
import torch.nn.functional as F

import tiling
from metrics import ConfusionMatrixAccumulator


def window_logits_u8(model, img_u8: np.ndarray, coeffs, device: str, batch_size: int = 8) -> torch.Tensor:
    h, w, _ = img_u8.shape
    h_pad, w_pad = tiling._padded_size(h), tiling._padded_size(w)
    padded = np.pad(img_u8, ((0, h_pad - h), (0, w_pad - w), (0, 0)), mode="reflect")
    s = torch.zeros((tiling.NUM_CLASSES, h_pad, w_pad), dtype=torch.float32)
    c = torch.zeros((1, h_pad, w_pad), dtype=torch.float32)
    ys, xs = list(range(0, h_pad - tiling.CROP + 1, tiling.STRIDE)), list(range(0, w_pad - tiling.CROP + 1, tiling.STRIDE))
    wins = [(y, x) for y in ys for x in xs]
    model.eval()
    with torch.no_grad():
        for b in range(0, len(wins), batch_size):
            batch = wins[b:b + batch_size]
            xb = torch.cat([tiling.dssa_prep.build_prithvi_input(coeffs.apply(padded[y:y + 224, x:x + 224, :].astype(np.float64))) for y, x in batch], dim=0).to(device)
            lg = model(xb).detach().cpu()
            for (y, x), l in zip(batch, lg):
                s[:, y:y + 224, x:x + 224] += l
                c[:, y:y + 224, x:x + 224] += 1.0
    del padded
    s.div_(c.clamp_(min=1.0))
    del c
    return s[:, :h, :w]


def eval_tile_u8(model, img_u8, coeffs, lab: np.ndarray, device: str, rows: int = 500):
    lg = window_logits_u8(model, img_u8, coeffs, device)
    pred = lg.argmax(dim=0).numpy().astype(np.int64)
    a = ConfusionMatrixAccumulator()
    a.update(pred, lab)
    del pred
    ce = 0.0
    for r in range(0, lab.shape[0], rows):
        ce += F.cross_entropy(lg[:, r:r + rows].unsqueeze(0), torch.from_numpy(lab[r:r + rows]).unsqueeze(0), reduction="sum").item()
    return a.matrix.copy(), ce
