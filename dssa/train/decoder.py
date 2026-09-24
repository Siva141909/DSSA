"""
DSSA Phase 2C - segmentation decoder.

Exact architecture frozen in DSSA_PHASE2B_B_TRAINING_PROTOCOL_FREEZE.md
Step 2 / dssa/config/phase2b_training_protocol.json architecture.decoder:
4-block progressive-upsampling convolutional head (SETR-PUP-style),
consuming ONLY the final transformer layer (index 23, post-closing-
LayerNorm) with the CLS token excluded. Identical across every
experimental condition (K=0 through K=24). Total parameters must equal
exactly 2,766,726 - verified by test, not just by construction.
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F

EXPECTED_DECODER_PARAMS = 2_766_726


class ConvUpBlock(nn.Module):
    def __init__(self, in_ch: int, out_ch: int):
        super().__init__()
        self.conv = nn.Conv2d(in_ch, out_ch, kernel_size=3, padding=1, bias=True)
        self.norm = nn.GroupNorm(32, out_ch)
        self.act = nn.ReLU(inplace=True)

    def forward(self, x):
        x = self.conv(x)
        x = self.norm(x)
        x = self.act(x)
        x = F.interpolate(x, scale_factor=2, mode="bilinear", align_corners=False)
        return x


class SegDecoder(nn.Module):
    """
    Input: (B, num_patches, 1024) final-layer patch tokens (CLS already
    excluded by the caller). num_patches must be a perfect square (H/16)^2.
    Output: (B, 6, H, W) raw logits (no final activation).
    """

    def __init__(self, embed_dim: int = 1024, num_classes: int = 6):
        super().__init__()
        self.embed_dim = embed_dim
        self.block1 = ConvUpBlock(1024, 256)
        self.block2 = ConvUpBlock(256, 128)
        self.block3 = ConvUpBlock(128, 64)
        self.block4 = ConvUpBlock(64, 64)
        self.final_conv = nn.Conv2d(64, num_classes, kernel_size=1, bias=True)

    def forward(self, patch_tokens: torch.Tensor) -> torch.Tensor:
        b, n, c = patch_tokens.shape
        side = int(round(n ** 0.5))
        if side * side != n:
            raise ValueError(f"num_patches={n} is not a perfect square; cannot reshape to a spatial grid")
        x = patch_tokens.transpose(1, 2).reshape(b, c, side, side)  # (B, 1024, side, side)
        x = self.block1(x)
        x = self.block2(x)
        x = self.block3(x)
        x = self.block4(x)  # 16x total upsample matches patch_size=16
        x = self.final_conv(x)
        return x


def count_params(module: nn.Module) -> int:
    return sum(p.numel() for p in module.parameters())
