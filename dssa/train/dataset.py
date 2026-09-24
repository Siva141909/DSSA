"""
DSSA Phase 2C - target-domain supervised dataset for training/validation/test.

Loads Vaihingen IRRG imagery (dssa/data/vaihingen_irrg/) and ISPRS ground-truth
labels (read directly from the official
ISPRS_semantic_labeling_Vaihingen_ground_truth_COMPLETE.zip - not extracted to
disk). Applies the FROZEN Strategy C source-fit-only radiometric transform
(fit in Phase 1B, never refit here) and the frozen 6-band zero-fill contract
via dssa/sanity/preprocessing.py, unchanged - so segmentation training sees
inputs in the same distribution the backbone/DSS mechanism was validated
against.

Class/color mapping matches dssa/config/phase2b_training_protocol.json
architecture.decoder.class_color_palette_rgb exactly.
"""
from __future__ import annotations

import io
import json
import random
import sys
import zipfile
from pathlib import Path

import numpy as np
import tifffile
import torch
from torch.utils.data import Dataset

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sanity"))
import preprocessing as dssa_prep  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
VAIHINGEN_IMG_DIR = ROOT / "data" / "vaihingen_irrg"
LABEL_ZIP = ROOT / "data" / "Vaihingen" / "ISPRS_semantic_labeling_Vaihingen_ground_truth_COMPLETE.zip"

CLASS_NAMES = ["impervious_surfaces", "building", "low_vegetation", "tree", "car", "clutter_background"]
CLASS_COLORS_RGB = {
    "impervious_surfaces": (255, 255, 255),
    "building": (0, 0, 255),
    "low_vegetation": (0, 255, 255),
    "tree": (0, 255, 0),
    "car": (255, 255, 0),
    "clutter_background": (255, 0, 0),
}
NUM_CLASSES = 6
CROP = 224


def load_radiometric_coeffs() -> "dssa_prep.SourceFitAffine":
    with open(ROOT / "artifacts" / "radiometric_transform.json") as f:
        saved = json.load(f)
    return dssa_prep.SourceFitAffine(offset=tuple(saved["offset_IR_R_G"]), scale=tuple(saved["scale_IR_R_G"]))


def load_label_array(filename: str) -> np.ndarray:
    """Reads one Vaihingen ground-truth label TIFF directly from the official
    zip (never extracted to disk). Returns (H, W, 3) uint8 RGB array."""
    with zipfile.ZipFile(LABEL_ZIP) as z:
        with z.open(filename) as f:
            data = f.read()
    arr = tifffile.imread(io.BytesIO(data))
    if arr.ndim != 3 or arr.shape[-1] != 3:
        raise ValueError(f"{filename}: expected (H,W,3) label array, got {arr.shape}")
    return arr


def rgb_to_class_index(label_rgb: np.ndarray) -> np.ndarray:
    """(H,W,3) uint8 -> (H,W) int64 class-index array. Raises if any pixel does
    not match one of the 6 frozen ISPRS colors exactly (no silent fallback)."""
    h, w, _ = label_rgb.shape
    out = np.full((h, w), -1, dtype=np.int64)
    for idx, name in enumerate(CLASS_NAMES):
        color = np.array(CLASS_COLORS_RGB[name], dtype=np.uint8)
        mask = np.all(label_rgb == color, axis=-1)
        out[mask] = idx
    if (out == -1).any():
        n_bad = int((out == -1).sum())
        raise ValueError(f"{n_bad} pixels did not match any of the 6 frozen ISPRS colors")
    return out


def load_irrg_image(filename: str) -> np.ndarray:
    return tifffile.imread(str(VAIHINGEN_IMG_DIR / filename))


class TargetSegDataset(Dataset):
    """
    Supervised target-domain dataset for one named split.

    mode='train': each __getitem__ returns one random CROPxCROP crop with the
      frozen geometric augmentation (h-flip, v-flip, 90-degree rotation),
      sampled uniformly over files then uniformly over crop position -
      matches the frozen 'training_crop_sampling' policy exactly.
    mode='eval': each __getitem__ returns the FULL calibrated image + full
      label array for one file (no cropping, no augmentation) - sliding-
      window tiling/stitching for validation/test happens in tiling.py.
    """

    def __init__(self, filenames: list[str], mode: str, seed: int = 1000, steps_per_epoch: int | None = None,
                 eval_max_size: int | None = None):
        assert mode in ("train", "eval")
        self.filenames = list(filenames)
        self.mode = mode
        self.coeffs = load_radiometric_coeffs()
        self._rng = random.Random(seed)
        self._steps_per_epoch = steps_per_epoch or len(self.filenames)
        self._cache: dict[str, tuple[np.ndarray, np.ndarray]] = {}
        # eval_max_size: PREFLIGHT-ONLY speed accommodation - crops eval images
        # to a bounded top-left region so implementation checks run quickly.
        # Never set by the real Phase 2C training/evaluation code path, which
        # always evaluates the full image per the frozen tiling protocol.
        self.eval_max_size = eval_max_size

    def _get_calibrated_and_label(self, filename: str):
        if filename not in self._cache:
            img = load_irrg_image(filename).astype(np.float64)
            calibrated = self.coeffs.apply(img)  # (H,W,3), channel order (IR,R,G)
            label_rgb = load_label_array(filename)
            label_idx = rgb_to_class_index(label_rgb)
            if calibrated.shape[:2] != label_idx.shape:
                raise ValueError(f"{filename}: image/label shape mismatch {calibrated.shape[:2]} vs {label_idx.shape}")
            self._cache[filename] = (calibrated, label_idx)
        return self._cache[filename]

    def __len__(self):
        return self._steps_per_epoch if self.mode == "train" else len(self.filenames)

    def _augment(self, img_crop: np.ndarray, lbl_crop: np.ndarray):
        if self._rng.random() < 0.5:
            img_crop = np.ascontiguousarray(img_crop[:, ::-1, :])
            lbl_crop = np.ascontiguousarray(lbl_crop[:, ::-1])
        if self._rng.random() < 0.5:
            img_crop = np.ascontiguousarray(img_crop[::-1, :, :])
            lbl_crop = np.ascontiguousarray(lbl_crop[::-1, :])
        k = self._rng.randrange(4)
        if k:
            img_crop = np.ascontiguousarray(np.rot90(img_crop, k, axes=(0, 1)))
            lbl_crop = np.ascontiguousarray(np.rot90(lbl_crop, k, axes=(0, 1)))
        return img_crop, lbl_crop

    def __getitem__(self, i):
        if self.mode == "train":
            filename = self._rng.choice(self.filenames)
            calibrated, label_idx = self._get_calibrated_and_label(filename)
            h, w = label_idx.shape
            y0 = self._rng.randrange(0, h - CROP + 1)
            x0 = self._rng.randrange(0, w - CROP + 1)
            img_crop = calibrated[y0:y0 + CROP, x0:x0 + CROP, :]
            lbl_crop = label_idx[y0:y0 + CROP, x0:x0 + CROP]
            img_crop, lbl_crop = self._augment(img_crop, lbl_crop)
            x = dssa_prep.build_prithvi_input(img_crop).squeeze(0)  # (6,1,224,224)
            y = torch.from_numpy(lbl_crop.copy()).long()
            return x, y, filename
        else:
            filename = self.filenames[i]
            calibrated, label_idx = self._get_calibrated_and_label(filename)
            if self.eval_max_size is not None:
                m = self.eval_max_size
                calibrated = calibrated[:m, :m, :]
                label_idx = label_idx[:m, :m]
            return calibrated, label_idx, filename
