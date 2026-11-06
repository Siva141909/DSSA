"""Phase 3 shared run pieces: the Potsdam training-tile cache, the frozen Phase 3 transform,
the checked model build, the data-stream replay and the probe-logit fingerprint."""
from __future__ import annotations

import hashlib
import json
import random

import numpy as np
import torch

import p3common as C

C.setup_paths()
import dataset as ds  # noqa: E402
import preprocessing as pp  # noqa: E402
import lora as lora_mod  # noqa: E402
import models as M  # noqa: E402

TILE = 6000  # every Potsdam tile (checked in Stage A and on load)


def transform() -> pp.SourceFitAffine:
    t = json.load(open(C.TRANSFORM_FILE))
    rec = json.load(open(C.ART / "stage_a" / "stage_a_record.json"))
    if C.sha256_file(C.TRANSFORM_FILE) != rec["radiometric_transform"]["sha256"]:
        raise RuntimeError("Phase 3 radiometric transform changed since Stage A")
    return pp.SourceFitAffine(tuple(t["offset_IR_R_G"]), tuple(t["scale_IR_R_G"]))


class PotsdamSegDatasetU8(ds.TargetSegDataset):
    """Train mode only. Same random-number use, crop, calibration-per-crop and augmentation as
    phase2d/dataset_u8.TargetSegDatasetU8; only the tile source and the transform differ."""

    def __init__(self, filenames, seed):
        super().__init__(filenames, "train", seed=seed)
        self.coeffs = transform()

    def _raw(self, filename):
        if filename not in self._cache:
            img = C.potsdam_image(filename)
            lbl = C.potsdam_label(filename)
            if img.dtype != np.uint8 or img.shape != (TILE, TILE, 3) or lbl.shape != (TILE, TILE):
                raise ValueError(f"{filename}: unexpected shapes {img.shape} {lbl.shape}")
            if lbl.max() >= ds.NUM_CLASSES:
                raise ValueError(f"{filename}: label index out of range")
            self._cache[filename] = (img, lbl)
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
        x = pp.build_prithvi_input(img_crop).squeeze(0)
        y = torch.from_numpy(lbl_crop.copy()).long()
        return x, y, filename


def rng_hash(r: random.Random) -> str:
    return hashlib.sha256(repr(r.getstate()).encode()).hexdigest()


def replay_stream(seed: int, files: list[str], draws: int) -> str:
    """Pure replay of the dataset's random-number use (no pixels read)."""
    r = random.Random(seed)
    for _ in range(draws):
        r.choice(files)
        r.randrange(0, TILE - 223)
        r.randrange(0, TILE - 223)
        r.random()
        r.random()
        r.randrange(4)
    return rng_hash(r)


def baseline() -> dict:
    return json.load(open(C.P2D_BASELINE))


def build_checked(layers: list[int], seed: int, lora_seed: int, device: str = "mps"):
    """Seeds the global RNG exactly as train.run_training does, builds, and asserts the
    initialisation equals the Phase 2D initialisation for the same seed (same decoder, same
    RNG state, same LoRA A, unchanged backbone)."""
    import train as T
    base = baseline()
    exp = base["expected"][str(seed)]
    T.set_all_seeds(seed)
    model, mods = M.build(list(layers), device, lora_seed)
    chk = {"decoder_hash": M.decoder_hash(model.decoder), "torch_rng_hash": M.tensor_hash([torch.get_rng_state()]),
           "backbone_fp": M.backbone_fingerprint(model), "probe_hash": M.probe_output_hash(model, device)}
    for k, want in (("decoder_hash", exp["decoder_hash"]), ("torch_rng_hash", exp["torch_rng_hash"]),
                    ("backbone_fp", base["expected_common"]["backbone_fp"]), ("probe_hash", base["expected_common"]["probe_hash"])):
        if chk[k] != want:
            raise RuntimeError(f"pre-run assertion failed: {k}")
    lora_mod.assert_only_intended_trainable(model.encoder, set(layers))
    if sum(m.lora_param_count() for m in mods) != 32768 * len(layers):
        raise RuntimeError("LoRA parameter count")
    for m in mods:
        if not (torch.count_nonzero(m.lora_B_q) == 0 and torch.count_nonzero(m.lora_B_v) == 0):
            raise RuntimeError("B not zero")
        if M.tensor_hash([m.lora_A_q, m.lora_A_v]) != exp["lora_A_hash"]:
            raise RuntimeError("A init hash mismatch")
    return model, mods, chk


def probe_logits(model, device: str = "mps") -> torch.Tensor:
    """Full-model logits on a fixed random input; fingerprints the trained decoder + LoRA."""
    x = torch.randn(2, 6, 1, 224, 224, generator=torch.Generator().manual_seed(2)).to(device)
    was = model.training
    model.eval()
    with torch.no_grad():
        out = model(x).detach().cpu()
    model.train(was)
    return out


def trainable_hash(model) -> str:
    return M.tensor_hash([p for p in model.parameters() if p.requires_grad])
