"""
DSSA Phase 2C - LoRA on the fused qkv projection.

Implements exactly the resolution frozen in
DSSA_PHASE2B_B_TRAINING_PROTOCOL_FREEZE.md Step 3: timm's Attention module
uses a single fused `qkv: Linear(1024, 3072, bias=qkv_bias)`, not separate
W_q/W_k/W_v matrices (verified by direct source inspection, Phase 2B-B).
LoRA (rank 8) is applied to the Q-slice (output rows 0:1024) and V-slice
(output rows 2048:3072) of this fused layer's output space; the K-slice
(rows 1024:2048) receives zero LoRA contribution. The original qkv weight
and bias are frozen and never modified in place - LoRA adds a parallel,
additive low-rank delta only, computed and concatenated with an exact-zero
delta on the K-slice.

Trainable parameters per wrapped block = 4 * rank * embed_dim = 32,768 for
rank=8, embed_dim=1024 - matches the frozen parameter_accounting exactly
(verified by test, not just by construction).
"""
from __future__ import annotations

import math

import torch
import torch.nn as nn

RANK = 8
ALPHA = 16
DROPOUT = 0.0
EXPECTED_LORA_PARAMS_PER_BLOCK = 32_768


class LoRAQKV(nn.Module):
    """Wraps an existing frozen `qkv` nn.Linear(dim, 3*dim). Q/V-slice LoRA only."""

    def __init__(self, orig_qkv: nn.Linear, rank: int = RANK, alpha: int = ALPHA, dropout: float = DROPOUT):
        super().__init__()
        assert orig_qkv.out_features == 3 * orig_qkv.in_features
        self.orig_qkv = orig_qkv
        for p in self.orig_qkv.parameters():
            p.requires_grad_(False)
        self.dim = orig_qkv.in_features
        self.rank = rank
        self.scaling = alpha / rank
        self.dropout = nn.Dropout(dropout) if dropout > 0 else nn.Identity()

        self.lora_A_q = nn.Parameter(torch.empty(rank, self.dim))
        self.lora_B_q = nn.Parameter(torch.zeros(self.dim, rank))
        self.lora_A_v = nn.Parameter(torch.empty(rank, self.dim))
        self.lora_B_v = nn.Parameter(torch.zeros(self.dim, rank))
        nn.init.kaiming_uniform_(self.lora_A_q, a=math.sqrt(5))
        nn.init.kaiming_uniform_(self.lora_A_v, a=math.sqrt(5))
        # B matrices start at zero -> the adapted model is initially identical
        # to the frozen backbone before any training step (standard LoRA convention).

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        base = self.orig_qkv(x)  # (..., 3*dim)
        xd = self.dropout(x)
        delta_q = (xd @ self.lora_A_q.t()) @ self.lora_B_q.t() * self.scaling  # (..., dim)
        delta_v = (xd @ self.lora_A_v.t()) @ self.lora_B_v.t() * self.scaling  # (..., dim)
        zero_k = torch.zeros_like(delta_q)
        delta = torch.cat([delta_q, zero_k, delta_v], dim=-1)  # (..., 3*dim)
        return base + delta

    def lora_param_count(self) -> int:
        return sum(p.numel() for p in (self.lora_A_q, self.lora_B_q, self.lora_A_v, self.lora_B_v))


def apply_lora_to_encoder(encoder, layer_indices: list[int], rank: int = RANK, alpha: int = ALPHA,
                           dropout: float = DROPOUT) -> list[LoRAQKV]:
    """
    Wraps encoder.blocks[i].attn.qkv with LoRAQKV for every i in layer_indices.
    All other encoder parameters remain frozen (requires_grad=False, set by
    load_frozen_encoder already). Returns the list of created LoRAQKV modules
    (for parameter counting / manifest logging).
    """
    wrapped = []
    for i in layer_indices:
        block = encoder.blocks[i]
        orig_qkv = block.attn.qkv
        if isinstance(orig_qkv, LoRAQKV):
            raise RuntimeError(f"block {i} qkv is already LoRA-wrapped")
        lora_qkv = LoRAQKV(orig_qkv, rank=rank, alpha=alpha, dropout=dropout)
        block.attn.qkv = lora_qkv
        wrapped.append(lora_qkv)
    return wrapped


def trainable_encoder_params(encoder) -> int:
    return sum(p.numel() for p in encoder.parameters() if p.requires_grad)


def assert_only_intended_trainable(encoder, expected_layer_indices: set[int]) -> None:
    """Pre-flight check: verifies LoRA parameters exist only on the intended
    blocks' qkv modules, and every other encoder parameter is frozen."""
    for i, block in enumerate(encoder.blocks):
        qkv = block.attn.qkv
        is_lora = isinstance(qkv, LoRAQKV)
        should_be_lora = i in expected_layer_indices
        if is_lora != should_be_lora:
            raise AssertionError(f"block {i}: LoRA-wrapped={is_lora}, expected={should_be_lora}")
        if is_lora:
            trainable = {n for n, p in qkv.named_parameters() if p.requires_grad}
            expected = {"lora_A_q", "lora_B_q", "lora_A_v", "lora_B_v"}
            if trainable != expected:
                raise AssertionError(f"block {i}: unexpected trainable LoRA params {trainable}")
            for n, p in qkv.orig_qkv.named_parameters():
                if p.requires_grad:
                    raise AssertionError(f"block {i}: original qkv.{n} is unexpectedly trainable")
    for name, p in encoder.named_parameters():
        if "lora_" in name:
            continue
        if p.requires_grad:
            raise AssertionError(f"unexpected trainable non-LoRA encoder parameter: {name}")
