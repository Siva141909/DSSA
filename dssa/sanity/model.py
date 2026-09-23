"""
DSSA sanity phase - model loading only.

Loads the FROZEN Prithvi-EO-2.0-300M encoder exactly as specified in
DSSA_IMPLEMENTATION_FREEZE.md. Does not modify pretrained weights. Does not
construct or load the MAE decoder (not needed - DSS only requires encoder
representations, and the decoder is not part of any frozen contract here).

This module never trains anything, never computes gradients, and always
loads in eval mode with parameters frozen (requires_grad_(False)).
"""
from __future__ import annotations

import sys
import hashlib
from pathlib import Path

import torch

CHECKPOINT_DIR = Path(__file__).resolve().parent.parent / "checkpoint"
sys.path.insert(0, str(CHECKPOINT_DIR))  # prithvi_mae.py lives here, as shipped by the checkpoint repo

from prithvi_mae import PrithviViT  # noqa: E402  (must follow sys.path insert)

FROZEN_MODEL_KWARGS = dict(
    img_size=224,
    patch_size=(1, 16, 16),
    in_chans=6,
    embed_dim=1024,
    depth=24,
    num_heads=16,
    mlp_ratio=4,
    coords_encoding=[],
)


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_frozen_encoder(num_frames: int = 1, device: str | torch.device = "cpu") -> PrithviViT:
    """
    Construct PrithviViT with the FROZEN architecture kwargs and num_frames=1
    (the frozen temporal contract), then load the checkpoint's encoder weights.

    Per the official inference.py reference implementation (same repo), the
    'pos_embed' buffer is excluded from the loaded state dict on purpose: it is
    a deterministic sin/cos function of (num_frames, grid_h, grid_w) computed
    fresh in PrithviViT.__init__ via initialize_weights(), not a learned
    parameter. Excluding it lets the freshly-constructed, correctly-shaped
    (num_frames=1) positional embedding stand, rather than trying to load a
    tensor shaped for num_frames=4. This does not modify any trained weight -
    pos_embed was never a trained parameter to begin with.
    """
    weights_path = CHECKPOINT_DIR / "Prithvi_EO_V2_300M.pt"
    if not weights_path.exists():
        raise FileNotFoundError(f"Checkpoint weights not found at {weights_path}")

    model = PrithviViT(num_frames=num_frames, **FROZEN_MODEL_KWARGS)

    full_state_dict = torch.load(weights_path, map_location="cpu", weights_only=True)
    encoder_state_dict = {
        k[len("encoder."):]: v
        for k, v in full_state_dict.items()
        if k.startswith("encoder.") and "pos_embed" not in k
    }

    missing, unexpected = model.load_state_dict(encoder_state_dict, strict=False)
    # pos_embed is the only key we expect to be reported "missing" here (by design, see docstring).
    unexpected_non_trivial = [k for k in unexpected]
    missing_non_trivial = [k for k in missing if "pos_embed" not in k]
    if unexpected_non_trivial:
        raise RuntimeError(f"Unexpected keys when loading encoder weights: {unexpected_non_trivial}")
    if missing_non_trivial:
        raise RuntimeError(f"Missing (non-pos_embed) keys when loading encoder weights: {missing_non_trivial}")

    model.eval()
    for p in model.parameters():
        p.requires_grad_(False)
    model.to(device)
    return model


def extract_layer_representations(model: PrithviViT, x: torch.Tensor) -> list[torch.Tensor]:
    """
    x: (B, 6, T, H, W) already-preprocessed tensor (T=1 per the frozen temporal contract).
    Returns a list of length `depth` (24 for this checkpoint), each element
    (B, num_tokens_incl_cls, embed_dim) - the output of each transformer block,
    with the final block's output additionally passed through the model's
    closing LayerNorm (matching PrithviViT.forward_features's own behavior).
    No masking is applied (forward_features, not forward - masking is an MAE
    pretraining-only mechanism and must not be used for DSS extraction).
    """
    with torch.no_grad():
        return model.forward_features(x, temporal_coords=None, location_coords=None)
