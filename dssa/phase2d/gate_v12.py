"""Writes recovery manifest v12 after verifying the recovery inventory: manifests
v4 to v11 unchanged, the 46 completed Gate 2 runs and the pilot passing their
integrity checks, the eight interrupted folders in their preserved state, INCIDENT_003
to 010 recorded, the four real-training interruptions (v8 L04 s2000, v9 L15 s2000,
v10 L20 s2000, v11 L05 s3000) consistent, no locked test tile opened, and the frozen
artifacts unchanged. Runs and every training field are copied from v11 in v11 order;
completed runs are removed and only the Layer 5 seed 3000 run ID changes, to
p2d_oracle_L05_s3000_a2. Also writes gate2/recovery_v12_audit.json."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
import gate_v5 as G5  # noqa: E402
import gate_v6 as G6  # noqa: E402
import gate_v7 as G7  # noqa: E402
import gate_v8 as G8  # noqa: E402
import gate_v9 as G9  # noqa: E402
import gate_v10 as G10  # noqa: E402
import gate_v11 as G11  # noqa: E402

V11 = C.ART / "manifest_gate2_recovery_v11.json"
V11_SHA = "7c60dee4490ef828a33b0fe54df500375b513a063b0df211ce6e7e765ae77538"
V11_DONE = [G11.RERUN] + [f"p2d_oracle_L{l:02d}_s2000" for l in (21, 22)] + [f"p2d_oracle_L{l:02d}_s3000" for l in (1, 2, 3, 4)]
DONE = G11.DONE + V11_DONE
FAILED, RERUN = "p2d_oracle_L05_s3000", "p2d_oracle_L05_s3000_a2"
L05C_FILES = {"IN_PROGRESS": "04dcd68083e88131b5037b3990d6566c24fe603cc8969680add7c145d3d9024f",
              "incident.json": "826d780fb9c5d3f9293a1a940a1dc096edd985b31e9f0d83a19a68b5a53c08b0",
              "telemetry.jsonl": "abe6082f48fb5f46c2d8bf90f34df6ef24c3f453b81d21ff7873d6f6f88e67bc"}  # stopped at step 152, before the first checkpoint


def main():
    for p, h in ((V11, V11_SHA), (G11.V10, G11.V10_SHA), (G10.V9, G10.V9_SHA), (G9.V8, G9.V8_SHA), (G8.V7, G8.V7_SHA), (G7.V6, G7.V6_SHA),
                 (G5.V4, G5.V4_SHA), (C.ART / "manifest_gate2_recovery_v5.json", G6.V5_SHA)):
        if C.sha256_file(p) != h:
            raise SystemExit(f"{p.name} changed")
    v11 = json.load(open(V11))
    C.assert_frozen_unchanged()
    base = json.load(open(C.BASELINE))
    if not all(C.simulate_data_stream(s) == base["expected"][str(s)]["data_stream_final"] for s in C.PILOT_SEEDS):
        raise SystemExit("data stream replay differs")
    pilot = {k: G5.verified(r) for k, r in v11["completed_pilot_runs"].items()}
    done = {r: G5.verified(r) for r in DONE}
    for e in v11["preserved_interrupted_runs"]:
        if G5.folder_hashes(e["run_id"]) != e["file_sha256"]:
            raise SystemExit(f"{e['run_id']} partial folder changed")
        if C.sha256_file(C.ART / "logs" / e["incident_report"]) != e["incident_report_sha256"]:
            raise SystemExit(f"{e['incident_report']} changed")
    if G5.folder_hashes(FAILED) != L05C_FILES or (C.RUNS / RERUN).exists():
        raise SystemExit("Layer 5 seed 3000 evidence is not in its preserved state, or the rerun folder exists")
    inc10 = C.ART / "logs" / "INCIDENT_010_gate2_v11_lid_close_power_loss_sleep.md"
    evidence = [G10.interruption_evidence("v8", G9.FAILED, G9.V8), G10.interruption_evidence("v9", G10.FAILED, G10.V9),
                G10.interruption_evidence("v10", G11.FAILED, G11.V10), G10.interruption_evidence("v11", FAILED, V11)]
    runs = []
    for e in v11["runs"]:
        if e["run_id"] in DONE:
            continue
        n = dict(e)
        n.pop("rerun_of", None)
        if n["run_id"] == FAILED:
            n["run_id"] = RERUN
            n["rerun_of"] = FAILED
        n["phase"] = "2D-gate2-recovery-v12"
        n["config_hash"] = C.config_hash(n)
        runs.append(n)
    ids = [r["run_id"] for r in runs]
    assert len(DONE) == 46 and len(set(DONE)) == 46
    assert len(runs) == 17 and ids[0] == RERUN and len(set(ids)) == 17
    assert not any(i in DONE or (C.RUNS / i).exists() for i in ids)
    if [r.get("rerun_of", r["run_id"]) for r in runs] != [e["run_id"] for e in v11["runs"] if e["run_id"] not in DONE]:
        raise SystemExit("order differs from v11")
    v11map = {e["run_id"]: e for e in v11["runs"]}
    same = ["K", "layer_indices", "training_seed", "lora_init_seed", "condition_labels", "protocol_file_hash", "addendum_sha256", "frozen_rankings_sha256", "equivalence_sha256", "cache", "est_seconds"]
    for r in runs:
        if any(r[k] != v11map[r.get("rerun_of", r["run_id"])][k] for k in same):
            raise SystemExit(f"{r['run_id']}: training field differs from v11")
    keep = ("manifest_v1_sha256", "manifest_v2_sha256", "manifest_v3_sha256", "manifest_v4_sha256", "manifest_v5_sha256", "manifest_v6_sha256", "manifest_v7_sha256", "manifest_v8_sha256",
            "manifest_v9_sha256", "manifest_v10_sha256", "completed_pilot_runs", "train_and_sanity_code_hash", "fingerprints", "backbone_fp", "probe_hash", "per_seed_expected", "limits", "failure_policy")
    sa = dict(v11["safety_additions"])
    sa["interruption_log"] = "logs/gate2_interruptions_v12.jsonl (every stop with its exact cause and stage)"
    m = {"authorization": "PENDING research-lead approval. Gate 2 recovery: exactly these 17 runs (Layer 5 seed 3000 rerun + the 16 pending v11 runs), in v11 order. No other training.",
         "version": 12, "supersedes_for_remaining_runs": "manifest_gate2_recovery_v11.json (preserved unchanged)", "manifest_v11_sha256": V11_SHA,
         **{k: v11[k] for k in keep}, "safety_additions": sa, "pilot_hashes": pilot,
         "completed_gate2_runs_kept": done,
         "preserved_interrupted_runs": v11["preserved_interrupted_runs"] + [{"run_id": FAILED, "file_sha256": L05C_FILES, "replaced_by": RERUN,
                                                                             "incident_report": inc10.name, "incident_report_sha256": C.sha256_file(inc10)}],
         "analysis": "gate2_analysis_v12.py: the frozen gate2_analysis.py with Layers 2, 6, 7 at seed 1000, Layers 2, 4, 15, 20 at seed 2000 and Layer 5 at seed 3000 mapped to their _a2 reruns",
         "code_hash": C.code_hash(),
         "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=C.PROJECT, capture_output=True, text=True).stdout.strip(),
         "est_hours": sum(r["est_seconds"] for r in runs) / 3600, "runs": runs}
    out = C.ART / "manifest_gate2_recovery_v12.json"
    if out.exists():
        raise SystemExit("manifest v12 already exists; not overwritten")
    C.write_json_atomic(out, m)
    sha = C.sha256_file(out)
    C.write_json_atomic(C.ART / "gate2" / "recovery_v12_audit.json", {"manifest_v12_sha256": sha, "real_interruption_evidence": evidence,
                                                                     "locked_test_set": G10.locked_test_untouched(ids), "environment_at_manifest_time": G10.environment(),
                                                                     "completed_runs": DONE, "failed_partial_runs": [e["run_id"] for e in m["preserved_interrupted_runs"]],
                                                                     "pending_runs": len(runs), "frozen_artifacts_unchanged": True, "data_stream_replay_ok": True})
    print("manifest v12:", len(runs), "runs, est h", round(m["est_hours"], 2), "sha256", sha)


if __name__ == "__main__":
    main()
