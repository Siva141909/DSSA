"""Phase 2D model builder: LoRA initialization isolated from the global RNG."""
from __future__ import annotations

import hashlib
import math
import sys
from pathlib import Path

import torch
import torch.nn as nn

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "train"))
import lora as lora_mod  # noqa: E402
import model_wrapper as mw  # noqa: E402
from decoder import SegDecoder  # noqa: E402
import common as C  # noqa: E402

dm = mw.dssa_model


def tensor_hash(tensors) -> str:
    h = hashlib.sha256()
    for t in tensors:
        h.update(t.detach().cpu().numpy().tobytes())
    return h.hexdigest()


def decoder_hash(decoder) -> str:
    sd = decoder.state_dict()
    return tensor_hash([sd[k] for k in sorted(sd)])


def backbone_fingerprint(model) -> str:
    """Same tensors, same order as run_matrix.backbone_fingerprint."""
    e = model.encoder
    return tensor_hash([e.patch_embed.proj.weight, e.blocks[0].mlp.fc1.weight, e.blocks[12].norm1.weight, e.blocks[23].mlp.fc2.bias])


def probe_output_hash(model, device) -> str:
    x = torch.randn(1, 6, 1, 224, 224, generator=torch.Generator().manual_seed(1)).to(device)
    was = model.training
    model.eval()
    with torch.no_grad():
        out = model.encoder.forward_features(x, temporal_coords=None, location_coords=None)[-1]
    model.train(was)
    return tensor_hash([out])


def isolated_lora(encoder, layers: list[int], lora_seed: int) -> list:
    """Wraps the blocks without consuming the global stream. A is drawn from a
    dedicated generator, re-seeded per block so A is the same at every layer."""
    wrapped = []
    for i in layers:
        block = encoder.blocks[i]
        with torch.random.fork_rng(devices=[]):
            q = lora_mod.LoRAQKV(block.attn.qkv, rank=lora_mod.RANK, alpha=lora_mod.ALPHA, dropout=lora_mod.DROPOUT)
        g = torch.Generator().manual_seed(lora_seed)
        nn.init.kaiming_uniform_(q.lora_A_q, a=math.sqrt(5), generator=g)
        nn.init.kaiming_uniform_(q.lora_A_v, a=math.sqrt(5), generator=g)
        block.attn.qkv = q
        wrapped.append(q)
    return wrapped


def build(layers: list[int], device: str, lora_seed: int):
    """K=0 is the unmodified Phase 2C build_model path."""
    if not layers:
        return mw.build_model([], device=device)
    encoder = dm.load_frozen_encoder(num_frames=1, device=device)
    mods = isolated_lora(encoder, layers, lora_seed)
    model = mw.DSSASegModel(encoder, SegDecoder(embed_dim=1024, num_classes=6)).to(device)
    return model, mods
