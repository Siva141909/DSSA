"""
DSSA Phase 2C - evaluation metrics.

Frozen metric set (DSSA_PHASE2B_B_TRAINING_PROTOCOL_FREEZE.md Step 10):
mean IoU, per-class IoU, macro F1, pixel accuracy. Confusion matrix is
accumulated per-image over the full tiled/stitched prediction, then summed
across all images in the split before computing metrics.
"""
from __future__ import annotations

import numpy as np

NUM_CLASSES = 6


class ConfusionMatrixAccumulator:
    def __init__(self, num_classes: int = NUM_CLASSES):
        self.num_classes = num_classes
        self.matrix = np.zeros((num_classes, num_classes), dtype=np.int64)

    def update(self, pred: np.ndarray, target: np.ndarray) -> None:
        """pred, target: (H,W) int arrays of class indices."""
        p = pred.reshape(-1)
        t = target.reshape(-1)
        valid = (t >= 0) & (t < self.num_classes) & (p >= 0) & (p < self.num_classes)
        p, t = p[valid], t[valid]
        idx = t * self.num_classes + p
        counts = np.bincount(idx, minlength=self.num_classes ** 2)
        self.matrix += counts.reshape(self.num_classes, self.num_classes)

    def compute(self) -> dict:
        cm = self.matrix.astype(np.float64)
        tp = np.diag(cm)
        fp = cm.sum(axis=0) - tp
        fn = cm.sum(axis=1) - tp
        denom_iou = tp + fp + fn
        per_class_iou = np.where(denom_iou > 0, tp / np.maximum(denom_iou, 1e-12), np.nan)
        mean_iou = float(np.nanmean(per_class_iou))

        precision = np.where((tp + fp) > 0, tp / np.maximum(tp + fp, 1e-12), 0.0)
        recall = np.where((tp + fn) > 0, tp / np.maximum(tp + fn, 1e-12), 0.0)
        denom_f1 = precision + recall
        per_class_f1 = np.where(denom_f1 > 0, 2 * precision * recall / np.maximum(denom_f1, 1e-12), 0.0)
        macro_f1 = float(np.mean(per_class_f1))

        pixel_accuracy = float(tp.sum() / max(cm.sum(), 1e-12))

        return {
            "mean_iou": mean_iou,
            "per_class_iou": [None if np.isnan(v) else float(v) for v in per_class_iou],
            "macro_f1": macro_f1,
            "per_class_f1": [float(v) for v in per_class_f1],
            "pixel_accuracy": pixel_accuracy,
            "confusion_matrix": cm.astype(int).tolist(),
        }
