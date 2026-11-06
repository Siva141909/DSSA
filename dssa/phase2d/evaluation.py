"""Per-tile validation. Replicates tiling.sliding_window_predict exactly and also
keeps the averaged logits, so tile confusion matrices and validation CE exist.
Gate 0 proves pixel-identical predictions against the Phase 2C function."""
from __future__ import annotations

import numpy as np
import torch
import torch.nn.functional as F

import tiling
from metrics import ConfusionMatrixAccumulator


def window_logits(model, cal: np.ndarray, device: str, batch_size: int = 8) -> torch.Tensor:
    h, w, _ = cal.shape
    h_pad, w_pad = tiling._padded_size(h), tiling._padded_size(w)
    padded = np.pad(cal, ((0, h_pad - h), (0, w_pad - w), (0, 0)), mode="reflect")
    s = torch.zeros((tiling.NUM_CLASSES, h_pad, w_pad), dtype=torch.float32)
    c = torch.zeros((1, h_pad, w_pad), dtype=torch.float32)
    ys, xs = list(range(0, h_pad - tiling.CROP + 1, tiling.STRIDE)), list(range(0, w_pad - tiling.CROP + 1, tiling.STRIDE))
    wins = [(y, x) for y in ys for x in xs]
    model.eval()
    with torch.no_grad():
        for b in range(0, len(wins), batch_size):
            batch = wins[b:b + batch_size]
            xb = torch.cat([tiling.dssa_prep.build_prithvi_input(padded[y:y + 224, x:x + 224, :]) for y, x in batch], dim=0).to(device)
            lg = model(xb).detach().cpu()
            for (y, x), l in zip(batch, lg):
                s[:, y:y + 224, x:x + 224] += l
                c[:, y:y + 224, x:x + 224] += 1.0
    return (s / c.clamp(min=1.0))[:, :h, :w]


def eval_tile(model, cal, lab, device):
    lg = window_logits(model, cal, device)
    pred = lg.argmax(dim=0).numpy().astype(np.int64)
    a = ConfusionMatrixAccumulator()
    a.update(pred, lab)
    ce = F.cross_entropy(lg.unsqueeze(0), torch.from_numpy(lab).unsqueeze(0), reduction="sum").item()
    return pred, a.matrix.copy(), ce
