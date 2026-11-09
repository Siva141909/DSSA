"""Writes the Stage C manifest (75 runs) and locks the Phase 3 code hash. Never overwrites.
Order: K0 x 3 seeds (Stage B part); then, after the score freeze, the early-block canary
L00 seed 1000, the rest of seed 1000 (L01-L23), then seeds 2000 and 3000 (L00-L23).
est_seconds (training process only) = Phase 2D mean training time of the arm + 150 s for
Potsdam cache load and start-up; the 1.5x runtime guard applies to it."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import p3common as C  # noqa: E402

C.install_guards()

T_ARM = {"K0": 761, 0: 1521, 1: 1483, 2: 1464, 3: 1426, 4: 1401, 5: 1375, 6: 1355, 7: 1292, 8: 1254, 9: 1219, 10: 1184, 11: 1157,
         12: 1118, 13: 1100, 14: 1061, 15: 1035, 16: 996, 17: 963, 18: 935, 19: 900, 20: 862, 21: 829, 22: 797, 23: 759}


def entry(layers, seed):
    rid = f"p3_K0_s{seed}" if not layers else f"p3_L{layers[0]:02d}_s{seed}"
    e = {"run_id": rid, "K": len(layers), "layer_indices": layers, "training_seed": seed, "lora_init_seed": seed + C.LORA_SEED_OFFSET,
         "condition_labels": ["K0"] if not layers else [f"Oracle_L{layers[0]:02d}"], "steps": 2000, "batch": 8, "crop": 224,
         "eval": "step 2000 only, final checkpoint, 8 Potsdam validation tiles, one process per tile",
         "est_seconds": T_ARM["K0" if not layers else layers[0]] + 150}
    e["config_hash"] = C.config_hash(e)
    return e


def make_v3():
    """v3 = v2 with the interrupted canary p3_L00_s1000 given the new ID p3_L00_s1000_r1
    (single controlled restart approved by the user 2026-11-06). Every other entry and every
    limit is unchanged; the interrupted folder is recorded by hash and never reused."""
    v2 = json.load(open(C.MANIFEST_V2))
    old_id = "p3_L00_s1000"
    d = C.RUNS / old_id
    if (d / "result.json").exists() or not (d / "incident.json").exists():
        raise RuntimeError("the v1/v2 canary is not an interrupted run")
    runs = []
    for e in v2["runs"]:
        if e["run_id"] == old_id:
            e = {k: v for k, v in e.items() if k != "config_hash"}
            e["run_id"] = C.CANARY
            e["config_hash"] = C.config_hash(e)
        runs.append(e)
    inc = json.load(open(d / "incident.json"))
    m = dict(v2)
    m.update({"version": 3, "created": time.time(), "runs": runs, "code_hash": C.code_hash(),
              "supersedes": {"manifest_stage_c_v2.json": C.sha256_file(C.MANIFEST_V2), "v2_code_hash": v2["code_hash"],
                             "manifest_stage_c.json": C.sha256_file(C.MANIFEST_V1)},
              "interrupted_runs": {old_id: {"files": {p.name: C.sha256_file(p) for p in sorted(d.iterdir()) if p.is_file()},
                                            "error": inc["error"], "stage": inc["stage"], "optimizer_steps_completed": inc["optimizer_steps_completed"],
                                            "kernel_lifetime_max_mb": inc["memory_final"]["lifetime_max_phys_footprint_mb"],
                                            "preserved": "never overwritten or reused"}},
              "authorization_v3": "Exactly one controlled canary restart (p3_L00_s1000_r1), approved by the user 2026-11-06. "
                                  "Launch only with normal memory pressure and stable swap (baseline recorded). Run only the canary; no automatic "
                                  "continuation; any guard trip stops with evidence and no second retry without explicit approval."})
    m["amendments"] = list(v2["amendments"]) + ["v3: canary p3_L00_s1000 stopped at optimizer step 4 by the swap-growth guard (717 MB > 512 MB; "
                                                "process peak 9,431 MB). Restart under a new run ID with every limit unchanged."]
    C.write_json_atomic(C.MANIFEST, m)
    print("manifest v3", C.sha256_file(C.MANIFEST), len(runs), "runs")


def make_v4(prev_path=None, old_id="p3_L06_s2000", new_id="p3_L06_s2000_r1", version=4, approved="2026-11-08"):
    """Resume manifest: the previous manifest with one interrupted run given a new ID.
    v4 (2026-11-08): p3_L06_s2000 -> p3_L06_s2000_r1; v5 (2026-11-09): p3_L10_s3000 ->
    p3_L10_s3000_r1. Both were stopped by the charger-disconnect guard. Every other entry and
    every limit is unchanged. Completed runs are skipped on resume and never overwritten."""
    prev_path = prev_path or C.MANIFEST_V3
    v3 = json.load(open(prev_path))
    d = C.RUNS / old_id
    if (d / "result.json").exists() or not (d / "incident.json").exists():
        raise RuntimeError(f"{old_id} is not an interrupted run")
    runs = []
    for e in v3["runs"]:
        if e["run_id"] == old_id:
            e = {k: v for k, v in e.items() if k != "config_hash"}
            e["run_id"] = new_id
            e["config_hash"] = C.config_hash(e)
        runs.append(e)
    inc = json.load(open(d / "incident.json"))
    done = sorted(e["run_id"] for e in runs if (C.RUNS / e["run_id"] / "summary.json").exists())
    m = dict(v3)
    m.update({"version": version, "created": time.time(), "runs": runs, "code_hash": C.code_hash(),
              "supersedes": {prev_path.name: C.sha256_file(prev_path), f"v{version - 1}_code_hash": v3["code_hash"],
                             "manifest_stage_c_v2.json": C.sha256_file(C.MANIFEST_V2), "manifest_stage_c.json": C.sha256_file(C.MANIFEST_V1)},
              f"completed_before_v{version}": {r: C.sha256_file(C.RUNS / r / "summary.json") for r in done},
              f"authorization_v{version}": f"Resume the Stage C sequence after the charger-disconnect stop, approved by the user {approved}. "
                                           f"Completed runs are skipped; the interrupted run restarts as {new_id}; all limits unchanged; no retry."})
    m["interrupted_runs"] = dict(v3["interrupted_runs"])
    m["interrupted_runs"][old_id] = {"files": {p.name: C.sha256_file(p) for p in sorted(d.iterdir()) if p.is_file()},
                                     "error": inc["error"], "cause": "charger disconnected (sequence guard SIGINT)", "stage": inc["stage"],
                                     "optimizer_steps_completed": inc["optimizer_steps_completed"], "preserved": "never overwritten or reused"}
    m["amendments"] = list(v3["amendments"]) + [f"v{version}: {old_id} stopped at optimizer step {inc['optimizer_steps_completed']} by the charger-disconnect guard. "
                                                "Restart under a new run ID; resume skips completed runs; limits unchanged."]
    C.write_json_atomic(C.MANIFEST, m)
    print(f"manifest v{version}", C.sha256_file(C.MANIFEST), len(runs), "runs;", len(done), "completed")


def main():
    if C.MANIFEST.exists():
        raise FileExistsError(C.MANIFEST)
    if C.MANIFEST_V4.exists():
        return make_v4(C.MANIFEST_V4, "p3_L10_s3000", "p3_L10_s3000_r1", 5, "2026-11-09")
    if C.MANIFEST_V3.exists():
        return make_v4()
    if C.MANIFEST_V2.exists():
        return make_v3()
    runs = [entry([], s) for s in C.SEEDS] + [entry([l], s) for s in C.SEEDS for l in range(24)]
    assert len(runs) == 75 and runs[3]["run_id"] == "p3_L00_s1000"
    p2d = {p.name: C.sha256_file(p) for p in sorted((C.ROOT / "phase2d").glob("*")) if p.is_file() and p.suffix in (".py", ".md")}
    git = subprocess.run(["git", "-C", str(C.ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(C.ROOT), "status", "--porcelain", "--", "phase2d", "train", "sanity", "artifacts/phase2d", "artifacts/splits", "artifacts/radiometric_transform.json"],
                           capture_output=True, text=True).stdout.strip()
    if dirty:
        raise RuntimeError(f"Phase 2D/2C files are not clean in git: {dirty}")
    m = {"authorization": "Phase 3 Stage C, approved 2026-11-06: 75 runs (K0 + 24 single blocks x 3 seeds), budget 48.8 h +-10%. "
                          "No Stage D, no test openings, no LoveDA, no commit or push.",
         "approved_decisions": ["D3", "D4", "D5", "D6", "D8 (Stage C only)", "D9", "D10", "D11", "D13", "D14", "D15", "D16", "D17", "D20", "D22", "D25", "D27"],
         "amendments": ["Potsdam label decoding: threshold snap for lossy tiles (4_12), approved by the user 2026-11-06 after Stage A found it; see stage_a_record.json"],
         "version": 1, "created": time.time(), "runs": runs,
         "code_hash": C.code_hash(), "phase2d_code_hash": p2d, "git_head": git,
         "split_sha256": C.sha256_file(C.SPLIT_FILE), "transform_sha256": C.sha256_file(C.TRANSFORM_FILE),
         "stage_a_record_sha256": C.sha256_file(C.ART / "stage_a" / "stage_a_record.json"),
         "limits": {"stop_rule_mb": C.STOP_RULE_MB, "early_abort_mb": C.ABORT_MB, "hard_guard_mb": C.MEM_LIMIT_MB, "swap_growth_mb": C.SWAP_GROWTH_LIMIT_MB,
                    "runtime": "1.5 x est_seconds (training)", "eval_watchdog_s": 400, "reload_watchdog_s": 300,
                    "guards": "sleep 30 s, charger 2 polls, thermal, critical pressure, telemetry stale 60 s, no optimizer step 300 s; no retry"},
         "budget_hours": {"stage_c": 48.8, "tolerance": 0.10}}
    if C.MANIFEST_V1.exists():
        v1 = json.load(open(C.MANIFEST_V1))
        if [r["config_hash"] for r in v1["runs"]] != [r["config_hash"] for r in runs]:
            raise RuntimeError("v2 run entries differ from v1")
        ver = sorted((C.ART / "eval_v2_verification").glob("*.json"))
        recs = [json.load(open(f)) for f in ver]
        if len(recs) != 24 or not all(r["pass"] for r in recs):
            raise RuntimeError("evaluator verification incomplete or failed")
        m["version"] = 2
        m["supersedes"] = {"manifest_stage_c.json": C.sha256_file(C.MANIFEST_V1), "v1_code_hash": v1["code_hash"],
                           "runs_completed_under_v1": ["p3_K0_s1000", "p3_K0_s2000", "p3_K0_s3000"]}
        m["amendments"].append("Evaluation memory (approved by the user 2026-11-06): K0 evaluation processes reached 10.14 GB against the 10.5 GB stop rule. "
                               "eval_tile.py now uses p3eval.eval_tile_u8 (uint8 padding, per-window calibration, in-place division, row-chunked CE). "
                               "Verified on all 24 K0 tile evaluations: confusion matrices identical, CE relative difference <= 1.7e-7, "
                               "peak 10,146 -> 6,007 MB. Limits unchanged.")
        m["evaluator_verification"] = {"files": {f.name: C.sha256_file(f) for f in ver}, "all_pass": True,
                                       "max_ce_rel_diff": max(r["ce_rel_diff"] for r in recs), "max_new_peak_mb": max(r["new_peak_mb"] for r in recs),
                                       "max_old_peak_mb": max(r["old_peak_mb"] for r in recs)}
    C.write_json_atomic(C.MANIFEST, m)
    print("manifest", C.sha256_file(C.MANIFEST), len(runs), "runs")


if __name__ == "__main__":
    main()
