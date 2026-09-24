"""
DSSA Phase 2C - checkpoint save/load.

Only trainable parameters (decoder + LoRA adapters) are persisted - the
frozen backbone (303,886,336 params, identical and unchanged across every
run) is reloaded fresh from the checkpoint each time via build_model(),
not duplicated per run on disk.
"""
from __future__ import annotations

from pathlib import Path

import torch


LORA_PARAM_NAMES = ("lora_A_q", "lora_B_q", "lora_A_v", "lora_B_v")


def _lora_only_state(lm) -> dict:
    # Deliberately does NOT use lm.state_dict(): LoRAQKV holds the frozen
    # original qkv Linear as a child module, so a naive state_dict() also
    # serializes ~3.15M frozen weights per wrapped block (found and fixed
    # during Phase 2C preflight - see DSSA_PHASE2C_PREFLIGHT_REPORT.md). Those
    # weights are identical across every run and reloaded fresh from the
    # checkpoint by build_model() regardless, so saving them per-run is pure
    # waste, not a correctness issue.
    return {name: getattr(lm, name).detach().cpu().clone() for name in LORA_PARAM_NAMES}


def save_checkpoint(path: Path, model, lora_modules: list, layer_indices: list[int], step: int, extra: dict | None = None):
    payload = {
        "decoder_state_dict": model.decoder.state_dict(),
        "lora_state_dicts": [_lora_only_state(lm) for lm in lora_modules],
        "layer_indices": list(layer_indices),
        "step": step,
    }
    if extra:
        payload["extra"] = extra
    torch.save(payload, path)


def load_checkpoint(path: Path, model, lora_modules: list, layer_indices: list[int]) -> dict:
    payload = torch.load(path, map_location="cpu", weights_only=False)
    if payload["layer_indices"] != list(layer_indices):
        raise ValueError(f"checkpoint layer_indices {payload['layer_indices']} != expected {layer_indices}")
    model.decoder.load_state_dict(payload["decoder_state_dict"])
    for lm, sd in zip(lora_modules, payload["lora_state_dicts"]):
        for name in LORA_PARAM_NAMES:
            getattr(lm, name).data.copy_(sd[name])
    return payload
