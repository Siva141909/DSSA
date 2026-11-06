"""8-bit training-tile cache. Same outputs as dataset.TargetSegDataset in train
mode, verified bit-for-bit by gate_v2.py. Tiles stay uint8 in memory; the frozen
Strategy C calibration runs on each crop instead of each whole tile. It is the same
per-pixel expression, so values do not change. dataset.py is not modified."""
from __future__ import annotations

import numpy as np

import dataset as ds


class TargetSegDatasetU8(ds.TargetSegDataset):
    def __init__(self, filenames, mode, seed=1000, steps_per_epoch=None, eval_max_size=None):
        if mode != "train" or eval_max_size is not None:
            raise ValueError("TargetSegDatasetU8 is the train-mode cache only")
        super().__init__(filenames, mode, seed=seed, steps_per_epoch=steps_per_epoch)

    def _raw(self, filename):
        if filename not in self._cache:
            img = ds.load_irrg_image(filename)
            if img.dtype != np.uint8:
                raise ValueError(f"{filename}: expected uint8 imagery, got {img.dtype}")
            lbl = ds.rgb_to_class_index(ds.load_label_array(filename))
            if img.shape[:2] != lbl.shape:
                raise ValueError(f"{filename}: image/label shape mismatch")
            if lbl.min() < 0 or lbl.max() >= ds.NUM_CLASSES:
                raise ValueError(f"{filename}: label index out of range")
            self._cache[filename] = (img, lbl.astype(np.uint8))
        return self._cache[filename]

    def __getitem__(self, i):
        filename = self._rng.choice(self.filenames)
        img, lbl = self._raw(filename)
        h, w = lbl.shape
        y0 = self._rng.randrange(0, h - ds.CROP + 1)
        x0 = self._rng.randrange(0, w - ds.CROP + 1)
        img_crop = self.coeffs.apply(img[y0:y0 + ds.CROP, x0:x0 + ds.CROP, :].astype(np.float64))
        lbl_crop = lbl[y0:y0 + ds.CROP, x0:x0 + ds.CROP].astype(np.int64)
        img_crop, lbl_crop = self._augment(img_crop, lbl_crop)
        x = ds.dssa_prep.build_prithvi_input(img_crop).squeeze(0)
        y = ds.torch.from_numpy(lbl_crop.copy()).long()
        return x, y, filename
