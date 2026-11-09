"""Stage D model builder with a LoRA rank parameter.

Rank 8 (and K0) delegate to the Phase 2D builder (phase2d/models.build) unchanged, so every
Stage C and rank-8 Stage D model is built by exactly the Stage C code path. Other ranks
(uniform rank 1) repeat phase2d/models.isolated_lora with only the rank changed and
alpha = 2 x rank, the frozen project convention (Phase 2B-B: alpha 16 = 2 x rank 8, so the
scale alpha/r stays 2.0). LoRA A is drawn from the same dedicated generator, re-seeded per
block; the global RNG stream is not consumed, so the decoder initialisation is the same as
in every other arm with the same training seed."""
from __future__ import annotations

import math

import torch
import torch.nn as nn

import p3common as C

C.setup_paths()
import lora as lora_mod  # noqa: E402
import model_wrapper as mw  # noqa: E402
import models as M  # noqa: E402
from decoder import SegDecoder  # noqa: E402


def alpha_for(rank: int) -> int:
    return 2 * rank


def build(layers: list[int], device: str, lora_seed: int, rank: int = lora_mod.RANK):
    if not layers or rank == lora_mod.RANK:
        return M.build(list(layers), device, lora_seed)
    encoder = M.dm.load_frozen_encoder(num_frames=1, device=device)
    mods = []
    for i in layers:
        block = encoder.blocks[i]
        with torch.random.fork_rng(devices=[]):
            q = lora_mod.LoRAQKV(block.attn.qkv, rank=rank, alpha=alpha_for(rank), dropout=lora_mod.DROPOUT)
        g = torch.Generator().manual_seed(lora_seed)
        nn.init.kaiming_uniform_(q.lora_A_q, a=math.sqrt(5), generator=g)
        nn.init.kaiming_uniform_(q.lora_A_v, a=math.sqrt(5), generator=g)
        block.attn.qkv = q
        mods.append(q)
    model = mw.DSSASegModel(encoder, SegDecoder(embed_dim=1024, num_classes=6)).to(device)
    return model, mods


def lora_params(rank: int, n_blocks: int) -> int:
    """Q and V each get A (r x 1024) and B (1024 x r)."""
    return 2 * rank * (1024 + 1024) * n_blocks
