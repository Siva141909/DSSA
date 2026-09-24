"""
DSSA Phase 2C - efficiency measurement.

Per DSSA_PHASE2B_B_TRAINING_PROTOCOL_FREEZE.md Step 11: measures parameters,
peak memory, and wall-clock time only. Never presents a trainable-parameter
reduction as implying a FLOPs or wall-clock reduction unless both are
actually measured here.
"""
from __future__ import annotations

import platform
import time

import torch


class WallClockTimer:
    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *exc):
        self.elapsed_seconds = time.time() - self.start


def reset_peak_memory(device: str) -> None:
    if device == "mps" and torch.backends.mps.is_available():
        try:
            torch.mps.empty_cache()
        except Exception:
            pass
    elif device == "cuda":
        torch.cuda.reset_peak_memory_stats()


def peak_memory_mb(device: str) -> float | None:
    if device == "mps" and torch.backends.mps.is_available():
        try:
            return torch.mps.current_allocated_memory() / (1024 ** 2)
        except Exception:
            return None
    if device == "cuda":
        return torch.cuda.max_memory_allocated() / (1024 ** 2)
    return None


def hardware_info() -> dict:
    return {
        "platform": platform.platform(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "torch_version": torch.__version__,
        "mps_available": torch.backends.mps.is_available(),
        "cuda_available": torch.cuda.is_available(),
    }
