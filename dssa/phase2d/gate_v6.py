"""Writes recovery manifest v6 after verifying the recovery inventory: manifests
v1 to v5 unchanged, every completed Gate 2 run (Layer 1 from v4; Layers 2-5 seed
1000 from v5) and the pilot passing their integrity checks, the interrupted
Layer 2 and Layer 6 folders in their preserved state, INCIDENT_003/004 and the
partial reports present, and the frozen artifacts unchanged. Runs and every
training field are copied from v5 in v5 order; completed runs are removed and
only the Layer 6 seed 1000 run ID changes, to p2d_oracle_L06_s1000_a2."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
import gate_v5 as G5  # noqa: E402

V5 = C.ART / "manifest_gate2_recovery_v5.json"
V5_SHA = "d4cfcb74fd298aa468dc4d3949a739255d32db3b1917a5860b175ddd332341d4"
DONE = ["p2d_oracle_L01_s1000", "p2d_oracle_L02_s1000_a2", "p2d_oracle_L03_s1000", "p2d_oracle_L04_s1000", "p2d_oracle_L05_s1000"]
FAILED, RERUN = "p2d_oracle_L06_s1000", "p2d_oracle_L06_s1000_a2"
L06_FILES = {"IN_PROGRESS": "5deab8babbfbb89759b92ae12a44195f1d9ca9212e754f94fa33243c02338ae4",
             "incident.json": "73cec8dea26b1124a1a299f08d8aab1865573c7f77967e8bfc2a37819e9a9646",
             f"{FAILED}_best.pt": "b417d855c83436b605e824b21eab79be0e2165687cc4e2de6b701c004bebb98e",
             "telemetry.jsonl": "e5ebaf661e76caac4331b42510c4c4fe56f16d2388a336cc901d2d0d5ec5d2cd"}


def main():
    if C.sha256_file(V5) != V5_SHA or C.sha256_file(G5.V4) != G5.V4_SHA:
        raise SystemExit("manifest v4 or v5 changed")
    v5 = json.load(open(V5))
    C.assert_frozen_unchanged()
    base = json.load(open(C.BASELINE))
    if not all(C.simulate_data_stream(s) == base["expected"][str(s)]["data_stream_final"] for s in C.PILOT_SEEDS):
        raise SystemExit("data stream replay differs")
    pilot = {k: G5.verified(r) for k, r in v5["completed_pilot_runs"].items()}
    done = {r: G5.verified(r) for r in DONE}
    l02 = v5["preserved_interrupted_run"]
    if G5.folder_hashes(l02["run_id"]) != l02["file_sha256"]:
        raise SystemExit("Layer 2 partial folder changed")
    if G5.folder_hashes(FAILED) != L06_FILES or (C.RUNS / RERUN).exists():
        raise SystemExit("Layer 6 evidence is not in its preserved state, or the rerun folder exists")
    inc3 = C.ART / "logs" / l02["incident_report"]
    inc4 = C.ART / "logs" / "INCIDENT_004_gate2_v5_swap_growth_stop.md"
    rep5 = C.ART / "gate2" / "GATE2_V5_PARTIAL_RESULTS.md"
    if C.sha256_file(inc3) != l02["incident_report_sha256"] or C.sha256_file(C.ART / "gate2" / "GATE2_PARTIAL_RESULTS.md") != l02["partial_results_sha256"]:
        raise SystemExit("INCIDENT_003 or the v4 partial report changed")
    runs = []
    for e in v5["runs"]:
        if e["run_id"] in DONE:
            continue
        n = dict(e)
        if n["run_id"] == FAILED:
            n["run_id"] = RERUN
            n["rerun_of"] = FAILED
        n["phase"] = "2D-gate2-recovery-v6"
        n["config_hash"] = C.config_hash(n)
        runs.append(n)
    assert len(runs) == 58 and runs[0]["run_id"] == RERUN and len({r["run_id"] for r in runs}) == 58
    assert not any(r["run_id"] in DONE or (C.RUNS / r["run_id"]).exists() for r in runs)
    v5map = {e["run_id"]: e for e in v5["runs"]}
    same = ["K", "layer_indices", "training_seed", "lora_init_seed", "condition_labels", "protocol_file_hash", "addendum_sha256", "frozen_rankings_sha256", "equivalence_sha256", "cache", "est_seconds"]
    for r in runs:
        o = v5map[r.get("rerun_of") if r["run_id"] == RERUN else r["run_id"]]
        if any(r[k] != o[k] for k in same):
            raise SystemExit(f"{r['run_id']}: training field differs from v5")
    if [r.get("rerun_of", r["run_id"]) for r in runs] != [e["run_id"] for e in v5["runs"] if e["run_id"] not in DONE]:
        raise SystemExit("order differs from v5")
    keep = ("manifest_v1_sha256", "manifest_v2_sha256", "manifest_v3_sha256", "manifest_v4_sha256", "completed_pilot_runs", "train_and_sanity_code_hash",
            "fingerprints", "backbone_fp", "probe_hash", "per_seed_expected", "limits")
    m = {"authorization": "PENDING research-lead approval. Gate 2 recovery: exactly these 58 runs (Layer 6 seed 1000 rerun + the 57 pending v5 runs), in v5 order. No other training.",
         "version": 6, "supersedes_for_remaining_runs": "manifest_gate2_recovery_v5.json (preserved unchanged)", "manifest_v5_sha256": V5_SHA,
         **{k: v5[k] for k in keep}, "pilot_hashes": pilot,
         "completed_gate2_runs_kept": done,
         "preserved_interrupted_runs": [l02, {"run_id": FAILED, "file_sha256": L06_FILES, "replaced_by": RERUN, "incident_report": inc4.name,
                                              "incident_report_sha256": C.sha256_file(inc4), "partial_results_sha256": C.sha256_file(rep5)}],
         "analysis": "gate2_analysis_v6.py: the frozen gate2_analysis.py with Layer 2 and Layer 6 seed 1000 mapped to their _a2 reruns",
         "code_hash": C.code_hash(),
         "safety_additions": {**v5["safety_additions"], "preflight_before_each_run": v5["safety_additions"]["preflight_before_each_run"] + ["no virtual machine (Docker) running"],
                              "interruption_log": "logs/gate2_interruptions_v6.jsonl (every stop with its exact cause and stage)",
                              "after_any_stop": "No automatic retry or resume. Resuming requires a new manifest version giving the interrupted run a new ID, and explicit approval."},
         "failure_policy": "Stop the whole sequence at the first failure, stop condition, guard stop or failed integrity check. No retry, no skip.",
         "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=C.PROJECT, capture_output=True, text=True).stdout.strip(),
         "est_hours": sum(r["est_seconds"] for r in runs) / 3600, "runs": runs}
    out = C.ART / "manifest_gate2_recovery_v6.json"
    if out.exists():
        raise SystemExit("manifest v6 already exists; not overwritten")
    C.write_json_atomic(out, m)
    print("manifest v6:", len(runs), "runs, est h", round(m["est_hours"], 2), "sha256", C.sha256_file(out))


if __name__ == "__main__":
    main()
