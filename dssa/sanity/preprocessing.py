"""
DSSA sanity phase - preprocessing.

Implements exactly the FROZEN contracts from DSSA_IMPLEMENTATION_FREEZE.md
Sections 3-5 (input, radiometric, temporal). Nothing here is tunable at
runtime - every threshold/choice below is a frozen decision, not a default.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch

# Band order fixed by the checkpoint's own config.json (verified this session):
#   index 0=Blue 1=Green 2=Red 3=NarrowNIR 4=SWIR1 5=SWIR2
BAND_MEAN = np.array([1087.0, 1342.0, 1433.0, 2734.0, 1958.0, 1363.0], dtype=np.float64)
BAND_STD = np.array([2248.0, 2179.0, 2178.0, 1850.0, 1242.0, 1049.0], dtype=np.float64)

BLUE, GREEN, RED, NARROW_NIR, SWIR1, SWIR2 = range(6)
ZERO_FILL_SLOTS = (BLUE, SWIR1, SWIR2)  # frozen: these three bands are unavailable from IRRG data


@dataclass(frozen=True)
class SourceFitAffine:
    """
    FROZEN Strategy C (DSSA_PREIMPLEMENTATION_CALIBRATION.md Sec 3): one fixed,
    per-channel affine transform, fit ONCE on Potsdam (source) statistics only,
    then applied UNCHANGED to both Potsdam and Vaihingen. Never refit on target.

    Channels here are (IR, R, G) - the three live bands available from IRRG
    imagery, in that order, matching the order returned by load_irrg_tiff().
    """
    offset: tuple[float, float, float]  # per-channel (IR, R, G) 8-bit DN offset
    scale: tuple[float, float, float]   # per-channel (IR, R, G) multiplicative scale

    def apply(self, irrg_8bit: np.ndarray) -> np.ndarray:
        """irrg_8bit: (H, W, 3) uint8/float array, channel order (IR, R, G)."""
        offset = np.asarray(self.offset, dtype=np.float64)
        scale = np.asarray(self.scale, dtype=np.float64)
        return (irrg_8bit.astype(np.float64) - offset) * scale


def fit_source_affine(potsdam_irrg_samples) -> SourceFitAffine:
    """
    Fit the frozen affine transform using ONLY Potsdam (source) pixel statistics.

    Per-channel target: map the source distribution's mean to the pretrained
    model's own per-band mean (for the corresponding slot: IR->NarrowNIR,
    R->Red, G->Green) and its spread to that band's pretrained std - i.e. the
    transform lands the *source* distribution where the model expects a
    *typically-scaled* input to be, without ever looking at Vaihingen.

    potsdam_irrg_samples: an iterable (list or generator) of (H, W, 3) arrays.
    Computed via streaming sum/sum-of-squares accumulation, one array at a
    time - NOT by concatenating every array into one float64 buffer, which
    is memory-unsafe at real ISPRS tile resolution (a naive concatenation of
    38 full 6000x6000 Potsdam tiles as float64 requires ~33 GB and will be
    OOM-killed on typical hardware). This streaming form computes the exact
    same global per-channel mean/std as the naive form - it is a memory-safe
    implementation of the same statistic, not a different statistic, per the
    frozen Strategy C definition and the explicit compute-safety instruction.
    """
    count = 0
    ch_sum = np.zeros(3, dtype=np.float64)
    ch_sumsq = np.zeros(3, dtype=np.float64)
    n_arrays = 0
    for arr in potsdam_irrg_samples:
        if arr.shape[-1] != 3:
            raise ValueError(f"expected 3-channel IRRG array, got shape {arr.shape}")
        flat = arr.reshape(-1, 3).astype(np.float64)  # one array's worth at a time, freed each iteration
        ch_sum += flat.sum(axis=0)
        ch_sumsq += (flat ** 2).sum(axis=0)
        count += flat.shape[0]
        n_arrays += 1
    if n_arrays == 0:
        raise ValueError("fit_source_affine requires at least one Potsdam IRRG sample; none provided.")

    src_mean = ch_sum / count  # (IR, R, G) - identical formula to the naive global mean
    src_var = ch_sumsq / count - src_mean ** 2
    src_std = np.sqrt(np.maximum(src_var, 0.0)) + 1e-8

    target_mean = np.array([BAND_MEAN[NARROW_NIR], BAND_MEAN[RED], BAND_MEAN[GREEN]])
    target_std = np.array([BAND_STD[NARROW_NIR], BAND_STD[RED], BAND_STD[GREEN]])

    scale = target_std / src_std
    offset = src_mean - target_mean / scale

    return SourceFitAffine(offset=tuple(offset.tolist()), scale=tuple(scale.tolist()))


def build_prithvi_input(irrg_calibrated: np.ndarray) -> torch.Tensor:
    """
    irrg_calibrated: (H, W, 3) float array, already through SourceFitAffine.apply(),
    channel order (IR, R, G), in the *pretrained model's own band-mean/std scale*
    (i.e. already calibrated, not yet z-score normalized).

    Returns: (1, 6, 1, H, W) float32 tensor - the exact frozen input contract
    (T=1, zero-fill for Blue/SWIR1/SWIR2 in NORMALIZED space).
    """
    h, w, _ = irrg_calibrated.shape
    six_channel = np.zeros((h, w, 6), dtype=np.float64)
    six_channel[..., NARROW_NIR] = irrg_calibrated[..., 0]  # IR
    six_channel[..., RED] = irrg_calibrated[..., 1]          # R
    six_channel[..., GREEN] = irrg_calibrated[..., 2]        # G
    # Blue / SWIR1 / SWIR2: set to that band's own pretrained mean BEFORE
    # normalization, so that after (x-mean)/std they become exactly zero.
    for idx in ZERO_FILL_SLOTS:
        six_channel[..., idx] = BAND_MEAN[idx]

    normalized = (six_channel - BAND_MEAN) / BAND_STD  # (H, W, 6)
    tensor = torch.from_numpy(normalized.astype(np.float32))
    tensor = tensor.permute(2, 0, 1)          # (6, H, W)
    tensor = tensor.unsqueeze(1)              # (6, T=1, H, W)
    tensor = tensor.unsqueeze(0)              # (1, 6, T=1, H, W)
    return tensor


def load_hls_reference_tiff(path: str) -> np.ndarray:
    """
    Loads the official, natively-scaled HLS reference sample as-is (int16,
    already in the checkpoint's own band order and radiometric scale - NO
    Strategy C transform applied, since this sample is not Potsdam/Vaihingen
    data and needs no radiometric reconciliation).

    Returns (H, W, 6) int16 array, band order [Blue, Green, Red, NarrowNIR, SWIR1, SWIR2].
    """
    import tifffile
    arr = tifffile.imread(path)
    if arr.shape[-1] != 6:
        raise ValueError(f"Expected 6-band HLS reference, got shape {arr.shape}")
    return arr


def build_prithvi_input_from_hls(hls_int16: np.ndarray) -> torch.Tensor:
    """
    Native HLS reference path (Check 3's reference forward pass): direct
    (raw - mean) / std normalization, matching the checkpoint's own official
    inference.py exactly (no rescaling by 10000 - confirmed this session by
    reading inference.py's load_example(): it normalizes raw int16 HLS values
    directly against config.json's mean/std, which are themselves expressed
    in that same raw int16 HLS scale).
    """
    normalized = (hls_int16.astype(np.float64) - BAND_MEAN) / BAND_STD
    tensor = torch.from_numpy(normalized.astype(np.float32))
    tensor = tensor.permute(2, 0, 1).unsqueeze(1).unsqueeze(0)  # (1, 6, 1, H, W)
    return tensor
