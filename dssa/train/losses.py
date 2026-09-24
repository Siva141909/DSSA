"""
DSSA Phase 2C - loss function.

Frozen in DSSA_PHASE2B_B_TRAINING_PROTOCOL_FREEZE.md Step 8: unweighted
CrossEntropy + Dice, 1:1 sum. No class weights (Dice is inherently
imbalance-robust; combining avoids a separately-tuned class-weight
hyperparameter as a hidden free parameter).
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F

NUM_CLASSES = 6


def dice_loss(logits: torch.Tensor, target: torch.Tensor, eps: float = 1e-6) -> torch.Tensor:
    """logits: (B,C,H,W), target: (B,H,W) int64. Macro-averaged (mean over
    classes) soft Dice loss on softmax probabilities."""
    probs = F.softmax(logits, dim=1)
    target_onehot = F.one_hot(target, num_classes=logits.shape[1]).permute(0, 3, 1, 2).float()
    dims = (0, 2, 3)
    intersection = (probs * target_onehot).sum(dims)
    union = probs.sum(dims) + target_onehot.sum(dims)
    dice_per_class = (2 * intersection + eps) / (union + eps)
    return 1.0 - dice_per_class.mean()


class CEDiceLoss(nn.Module):
    def __init__(self):
        super().__init__()
        self.ce = nn.CrossEntropyLoss()

    def forward(self, logits: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        return self.ce(logits, target) + dice_loss(logits, target)
