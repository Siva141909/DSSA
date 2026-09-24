"""
DSSA Phase 2C - full segmentation model (frozen backbone + optional LoRA + decoder).
"""
from __future__ import annotations

import sys
from pathlib import Path

import torch
import torch.nn as nn

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sanity"))
import model as dssa_model  # noqa: E402

from decoder import SegDecoder  # noqa: E402
from lora import apply_lora_to_encoder  # noqa: E402


class DSSASegModel(nn.Module):
    """
    encoder: frozen Prithvi-EO-2.0-300M ViT (optionally LoRA-wrapped on
    selected blocks' qkv, per apply_lora_to_encoder).
    decoder: SegDecoder consuming only the final transformer layer (index 23,
    post-closing-LayerNorm), CLS token excluded.
    """

    def __init__(self, encoder, decoder: SegDecoder):
        super().__init__()
        self.encoder = encoder
        self.decoder = decoder

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: (B, 6, 1, H, W) preprocessed input. Returns (B, 6, H, W) logits."""
        feats = dssa_model.extract_layer_representations(self.encoder, x) if not self.training \
            else self.encoder.forward_features(x, temporal_coords=None, location_coords=None)
        final = feats[-1]           # (B, 1+num_patches, 1024) - last block, post closing-LayerNorm
        patch_tokens = final[:, 1:, :]  # CLS excluded
        logits = self.decoder(patch_tokens)
        return logits


def build_model(layer_indices: list[int], device: str, rank: int = 8, alpha: int = 16,
                 dropout: float = 0.0) -> tuple[DSSASegModel, list]:
    """
    Loads the frozen encoder (num_frames=1), applies LoRA to `layer_indices`
    (empty list = K=0 decoder-only baseline), attaches a fresh SegDecoder, and
    moves everything to `device`. Returns (model, list_of_lora_modules).
    """
    encoder = dssa_model.load_frozen_encoder(num_frames=1, device=device)
    lora_modules = apply_lora_to_encoder(encoder, layer_indices, rank=rank, alpha=alpha, dropout=dropout)
    decoder = SegDecoder(embed_dim=1024, num_classes=6)
    model = DSSASegModel(encoder, decoder).to(device)
    return model, lora_modules


def trainable_parameters(model: DSSASegModel):
    return [p for p in model.parameters() if p.requires_grad]


def count_trainable(model: DSSASegModel) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def count_total(model: DSSASegModel) -> int:
    return sum(p.numel() for p in model.parameters())
