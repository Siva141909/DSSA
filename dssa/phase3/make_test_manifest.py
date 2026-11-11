"""Freezes the Potsdam test opening before any test tile is read (protocol v2 section 9, v3
section 9; approved by the user 2026-11-11 after Stage D). Lists the 70 models of scenario S2
(the 67 Stage D models of manifest v4 and the 3 reused Stage C K0 models), each with its
step-2000 checkpoint SHA-256, the 10 test tiles from the frozen split, the Phase 3 code hash
(which covers test_tile.py, run_test.py and test_analysis.py), and the validation mIoU already
on record. Refuses unless every model is complete and integrity-checked. Never overwrites."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import p3common as C  # noqa: E402

C.install_guards()

TDIR = C.ART / "test_potsdam"
REUSED_K0 = ["p3_K0_s1000", "p3_K0_s2000", "p3_K0_s3000"]


def main():
    out = TDIR / "test_manifest.json"
    if out.exists():
        raise FileExistsError(out)
    if TDIR.exists() and any(TDIR.iterdir()):
        raise RuntimeError("test_potsdam folder is not empty")
    md = json.load(open(C.MANIFEST_D))
    entries = [(e, "stage_d") for e in md["runs"]] + [(e, "stage_c") for e in json.load(open(C.MANIFEST))["runs"] if e["run_id"] in REUSED_K0]
    models = []
    for e, src in entries:
        rid = e["run_id"]
        d = C.RUNS / rid
        summ = json.load(open(d / "summary.json"))
        res = json.load(open(d / "result.json"))
        if not (json.load(open(d / "reload_check.json"))["pass"] and summ["all_tiles_same_checkpoint"]):
            raise RuntimeError(f"{rid}: integrity check failed")
        sha = C.sha256_file(d / res["checkpoint"]["path"])
        if sha != res["checkpoint"]["sha256"] or sha != summ["checkpoint_sha256"]:
            raise RuntimeError(f"{rid}: checkpoint hash changed")
        models.append({"run_id": rid, "arm": e["condition_labels"][0], "seed": e["training_seed"], "blocks": e["layer_indices"],
                       "rank": e.get("rank", 8), "source": src, "checkpoint_sha256": sha, "val_miou": summ["pooled"]["mean_iou"]})
    counts = {}
    for m in models:
        counts[m["arm"]] = counts.get(m["arm"], 0) + 1
    assert len(models) == 70 and counts == {"UNIF8": 5, "K0": 10, "PRIOR3": 10, "UNIF1": 10, "MID3": 5, "LATE3": 5, "DSS3": 5,
                                            "FISH3": 5, "LOGME3": 5, "RAND3": 10}, counts
    tiles = C.split()["test"]
    assert len(tiles) == 10
    m = {"opening": "Potsdam test, scenario S2, single opening", "created": time.time(),
         "authorization": "Approved by the user 2026-11-11 after Stage D completed (67/67): 'yeah go ahead'.",
         "protocol": "v2 section 9 (amended by v3 section 9, v4 section 11): all S2 models, final step-2000 checkpoints, 10 test tiles, one process per tile",
         "primary_analysis": "C3: Prior-3 non-inferior to Uniform-r1, margin 0.010, paired by seed, n = 10 (test_analysis.py, hashed here)",
         "forbidden_uses": "choosing K, arms, candidates or thresholds; rerunning with changes",
         "tiles": tiles, "models": models, "arm_counts": counts,
         "code_hash": C.code_hash(), "test_analysis_sha256": C.sha256_file(C.CODE / "test_analysis.py"),
         "split_sha256": C.sha256_file(C.SPLIT_FILE), "transform_sha256": C.sha256_file(C.TRANSFORM_FILE),
         "stage_d_manifest_sha256": C.sha256_file(C.MANIFEST_D), "stage_c_manifest_sha256": C.sha256_file(C.MANIFEST),
         "stage_d_code_snapshot_sha256sums": C.sha256_file(C.ART / "code_snapshot_stage_d" / "SHA256SUMS"),
         "limits": {"stop_rule_mb": C.STOP_RULE_MB, "early_abort_mb": C.ABORT_MB, "hard_guard_mb": C.MEM_LIMIT_MB, "eval_watchdog_s": 400}}
    TDIR.mkdir(parents=True, exist_ok=True)
    C.write_json_atomic(out, m)
    (TDIR / "test_manifest.sha256").write_text(C.sha256_file(out) + "  test_manifest.json\n")
    print("test manifest", C.sha256_file(out), len(models), "models", len(tiles), "tiles")


if __name__ == "__main__":
    main()
