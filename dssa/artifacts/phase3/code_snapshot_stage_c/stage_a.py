"""Phase 3 Stage A (approved 2026-11-06, D3 and D4). Order is enforced:
  1. Freeze the Potsdam split by the positional rule (38 sorted names; train = first 20,
     probe = first 5 of train, validation = next 8, test = last 10) from the directory
     listing alone, write the manifest and its SHA-256. No label archive is opened before
     this point (the audit hook refuses it).
  2. Label archive: SHA-256 of 5_Labels_all.zip and the member list (metadata only).
  3. Training-label integrity: decode the 20 training labels only (colour table, shape,
     class counts). Validation labels are not decoded here; test labels never.
  4. Refit Strategy C on the 20 Vaihingen training images only (D4) and freeze it.
  5. Re-derive the Gate 0 crop positions and check them against the frozen Gate 0 file.
Writes only under dssa/artifacts/phase3/. Never overwrites."""
from __future__ import annotations

import hashlib
import json
import random
import sys
import time
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import p3common as C  # noqa: E402

C.install_guards()
C.setup_paths()
import numpy as np  # noqa: E402
import tifffile  # noqa: E402
import preprocessing as pp  # noqa: E402

OUT = C.ART / "stage_a"


def crops_for(name: str, h: int, w: int) -> list[tuple[int, int]]:
    """Identical to phase2d/gate0_dss.crops_for (that module installs Phase 2D guards on import)."""
    seed = int(hashlib.sha256(f"phase2d-crops-v1:{name}".encode()).hexdigest()[:16], 16)
    r = random.Random(seed)
    return [(0, 0)] + [(r.randrange(h - 223), r.randrange(w - 223)) for _ in range(8)]


def main():
    t0 = time.time()
    log = {"started": t0}
    for p in (C.TRANSFORM_FILE, OUT / "stage_a_record.json"):
        if p.exists():
            raise FileExistsError(f"{p} exists; Stage A never overwrites")
    OUT.mkdir(parents=True, exist_ok=True)
    names = C.potsdam_image_names()
    parts = C._split_rule(names)

    # 1. split, from the listing only. A frozen split is verified, never rewritten.
    if C.SPLIT_FILE.exists():
        assert C.split() == parts
        split_sha = C.sha256_file(C.SPLIT_FILE)
        log["split"] = {"sha256": split_sha, "frozen_at": json.load(open(C.SPLIT_FILE))["created"], "counts": {k: len(v) for k, v in parts.items()},
                        "note": "frozen by the first Stage A attempt, which then stopped at the 4_12 colour check; verified here, not rewritten"}
        print("[split verified]", split_sha, flush=True)
    else:
        C.SPLIT_FILE.parent.mkdir(parents=True, exist_ok=True)
        assert set(parts["probe"]) <= set(parts["train"])
        assert not (set(parts["train"]) & set(parts["validation"])) and not ((set(parts["train"]) | set(parts["validation"])) & set(parts["test"]))
        sizes = {n: (C.POTSDAM_IMG_DIR / n).stat().st_size for n in names}  # stat only, no open
        manifest = {
            "status": "FROZEN before any Potsdam label is read",
            "rule": "38 Potsdam IRRG names sorted lexicographically; positional: train = [0:20], probe = train[0:5], validation = [20:28], test = [28:38]. No shuffle.",
            "approval": "Phase 3 Stage C approval 2026-11-06 (D3)",
            "partitions": parts,
            "tile_ids": {k: [C.potsdam_tile_id(n) for n in v] for k, v in parts.items()},
            "image_file_sizes": sizes,
            "label_archive": str(C.POTSDAM_LABEL_ZIP.relative_to(C.PROJECT)),
            "label_member_pattern": "top_potsdam_{row}_{col}_label.tif (5_Labels_all, with boundaries)",
            "created": time.time(),
        }
        C.write_json_atomic(C.SPLIT_FILE, manifest)
        split_sha = C.sha256_file(C.SPLIT_FILE)
        C.SPLIT_HASH_FILE.write_text(f"{split_sha}  {C.SPLIT_FILE.name}\n")
        log["split"] = {"sha256": split_sha, "frozen_at": time.time(), "counts": {k: len(v) for k, v in parts.items()}}
        print("[split frozen]", split_sha, {k: len(v) for k, v in parts.items()}, flush=True)
        assert C.split() == parts

    # 2. label archive checksum and member list (metadata only)
    zsha = C.sha256_file(C.POTSDAM_LABEL_ZIP)
    with zipfile.ZipFile(C.POTSDAM_LABEL_ZIP) as z:
        info = {i.filename: {"size": i.file_size, "crc": f"{i.CRC:08x}"} for i in z.infolist()}
    need = {C.label_member(C.potsdam_tile_id(n)) for n in names}
    missing = sorted(need - set(info))
    if missing:
        raise RuntimeError(f"label members missing: {missing}")
    log["label_archive"] = {"sha256": zsha, "n_members": len(info), "all_38_members_present": True,
                            "train_val_member_crc": {C.label_member(C.potsdam_tile_id(n)): info[C.label_member(C.potsdam_tile_id(n))] for n in parts["train"] + parts["validation"]}}
    print("[label archive]", zsha, len(info), "members", flush=True)

    # 3. training labels only
    C.LABEL_ALLOW.update(C.potsdam_tile_id(n) for n in parts["train"])
    tl = {}
    for n in parts["train"]:
        img = C.potsdam_image(n)
        lab = C.potsdam_label(n)
        if img.dtype != np.uint8 or img.ndim != 3 or img.shape[2] != 3 or img.shape[:2] != lab.shape:
            raise RuntimeError(f"{n}: image {img.shape} {img.dtype} vs label {lab.shape}")
        cnt = np.bincount(lab.ravel(), minlength=6)
        tl[n] = {"shape": list(img.shape), "image_sha256": C.sha256_file(C.POTSDAM_IMG_DIR / n), "class_counts": cnt.tolist()}
        print("  label ok", n, img.shape, cnt.tolist(), flush=True)
        del img, lab
    tot = np.sum([v["class_counts"] for v in tl.values()], axis=0)
    log["training_labels"] = {"tiles": tl, "class_counts_total": tot.tolist(), "class_fraction": (tot / tot.sum()).round(5).tolist(),
                              "colour_table": "frozen ISPRS table; exact match, except tiles listed in snapped_tiles",
                              "snapped_tiles": dict(C.SNAPPED),
                              "snap_rule": "label-decoding amendment approved by the user 2026-11-06 after the first Stage A attempt found 4_12 to be a lossy copy: per-channel threshold at 128, only if every pixel's nearest ISPRS colour is <= 100 away and the second nearest >= 100 further and the threshold equals the nearest colour; otherwise hard stop. Applies to every Potsdam label tile; fixed before any validation label is decoded."}
    vshapes = {}
    for n in parts["validation"]:  # header only, for the evaluation cost model; no pixels decoded
        with tifffile.TiffFile(str(C.POTSDAM_IMG_DIR / n)) as t:
            vshapes[n] = list(t.pages[0].shape)
    log["validation_image_shapes"] = vshapes

    # 4. Strategy C refit on Vaihingen training images only
    def stream():
        for n in C.V_TRAIN:
            a = tifffile.imread(str(C.VAIHINGEN_IMG_DIR / n))
            assert a.dtype == np.uint8 and a.shape[-1] == 3
            yield a
    co = pp.fit_source_affine(stream())
    old = json.load(open(C.ROOT / "artifacts" / "radiometric_transform.json"))
    tr = {"strategy": "Strategy C - source-fit-only affine; Phase 3 refit (D4)", "fit_on": "vaihingen_target_train_only (Phase 3 source)",
          "files": C.V_TRAIN, "n_vaihingen_files_used": len(C.V_TRAIN), "n_potsdam_files_used": 0,
          "offset_IR_R_G": list(co.offset), "scale_IR_R_G": list(co.scale), "frozen": True, "applied_to": ["vaihingen (source)", "potsdam (target)"],
          "phase2d_transform_for_reference": {"offset_IR_R_G": old["offset_IR_R_G"], "scale_IR_R_G": old["scale_IR_R_G"]}}
    C.write_json_atomic(C.TRANSFORM_FILE, tr)
    log["radiometric_transform"] = {"sha256": C.sha256_file(C.TRANSFORM_FILE), "offset": tr["offset_IR_R_G"], "scale": tr["scale_IR_R_G"]}
    print("[transform]", tr["offset_IR_R_G"], tr["scale_IR_R_G"], flush=True)

    # 5. Gate 0 crop positions
    g0 = json.load(open(C.ROOT / "artifacts" / "phase2d" / "gate0" / "frozen_rankings.json"))["crops"]
    ok = {}
    for n in C.V_TRAIN + parts["train"][:5]:
        d = C.VAIHINGEN_IMG_DIR / n if n in C.V_TRAIN else C.POTSDAM_IMG_DIR / n
        with tifffile.TiffFile(str(d)) as t:
            h, w = t.pages[0].shape[:2]
        ok[n] = [list(c) for c in crops_for(n, h, w)] == [list(c) for c in g0[n]]
    if not all(ok.values()):
        raise RuntimeError(f"Gate 0 crops not reproduced: {[k for k, v in ok.items() if not v]}")
    log["gate0_crops_reproduced"] = {"tiles": len(ok), "all_match": True}

    log["finished"] = time.time()
    log["opened"] = {"potsdam_images": sorted(C.OPENED["images"]), "potsdam_labels": sorted(C.OPENED["labels"])}
    log["code_hash"] = C.code_hash()
    C.write_json_atomic(OUT / "stage_a_record.json", log)
    print("[stage A done]", round(time.time() - t0), "s", flush=True)


if __name__ == "__main__":
    main()
