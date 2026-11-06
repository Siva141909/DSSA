"""Writes recovery manifest v11 after verifying the recovery inventory: manifests
v1 to v10 unchanged, the 39 completed Gate 2 runs and the pilot passing their
integrity checks, the seven interrupted folders in their preserved state, INCIDENT_003
to 009 recorded, the three real-training interruptions (v8 L04 s2000, v9 L15 s2000,
v10 L20 s2000) consistent, no locked test tile opened, and the frozen artifacts
unchanged. Runs and every training field are copied from v10 in v10 order; completed
runs are removed and only the Layer 20 seed 2000 run ID changes, to
p2d_oracle_L20_s2000_a2. Also writes gate2/recovery_v11_audit.json."""
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

V10 = C.ART / "manifest_gate2_recovery_v10.json"
V10_SHA = "006394f7b27b57089cc42e29c8aa91d91650c3147a5551f74712a28f6401da96"
V10_DONE = [G10.RERUN] + [f"p2d_oracle_L{l:02d}_s2000" for l in (16, 17, 18, 19)]
DONE = G10.DONE + V10_DONE
FAILED, RERUN = "p2d_oracle_L20_s2000", "p2d_oracle_L20_s2000_a2"
L20B_FILES = {"IN_PROGRESS": "87e3ecd2fedf9fe85654fe6f23a082d6342b2b243700180fd5afbc2fb7a11f01",
              "incident.json": "a9e06a48a7d6d179b08ee378651ce08d156b902a8ee305eaaa215cf5c5680c15",
              f"{FAILED}_best.pt": "6a374c618fc4088bf3b8f425489727a320b6909cd710b3abd2ef044e56c804b7",
              "telemetry.jsonl": "1f9a8fc8a9b94688bddead0d9c9aeab1239827c5aabee007c894749fb4ded7b7"}


def main():
    for p, h in ((V10, V10_SHA), (G10.V9, G10.V9_SHA), (G9.V8, G9.V8_SHA), (G8.V7, G8.V7_SHA), (G7.V6, G7.V6_SHA), (G5.V4, G5.V4_SHA),
                 (C.ART / "manifest_gate2_recovery_v5.json", G6.V5_SHA)):
        if C.sha256_file(p) != h:
            raise SystemExit(f"{p.name} changed")
    v10 = json.load(open(V10))
    C.assert_frozen_unchanged()
    base = json.load(open(C.BASELINE))
    if not all(C.simulate_data_stream(s) == base["expected"][str(s)]["data_stream_final"] for s in C.PILOT_SEEDS):
        raise SystemExit("data stream replay differs")
    pilot = {k: G5.verified(r) for k, r in v10["completed_pilot_runs"].items()}
    done = {r: G5.verified(r) for r in DONE}
    for e in v10["preserved_interrupted_runs"]:
        if G5.folder_hashes(e["run_id"]) != e["file_sha256"]:
            raise SystemExit(f"{e['run_id']} partial folder changed")
        if C.sha256_file(C.ART / "logs" / e["incident_report"]) != e["incident_report_sha256"]:
            raise SystemExit(f"{e['incident_report']} changed")
    if G5.folder_hashes(FAILED) != L20B_FILES or (C.RUNS / RERUN).exists():
        raise SystemExit("Layer 20 seed 2000 evidence is not in its preserved state, or the rerun folder exists")
    inc9 = C.ART / "logs" / "INCIDENT_009_gate2_v10_charger_sleep.md"
    evidence = [G10.interruption_evidence("v8", G9.FAILED, G9.V8), G10.interruption_evidence("v9", G10.FAILED, G10.V9),
                G10.interruption_evidence("v10", FAILED, V10)]
    runs = []
    for e in v10["runs"]:
        if e["run_id"] in DONE:
            continue
        n = dict(e)
        n.pop("rerun_of", None)
        if n["run_id"] == FAILED:
            n["run_id"] = RERUN
            n["rerun_of"] = FAILED
        n["phase"] = "2D-gate2-recovery-v11"
        n["config_hash"] = C.config_hash(n)
        runs.append(n)
    ids = [r["run_id"] for r in runs]
    assert len(DONE) == 39 and len(set(DONE)) == 39
    assert len(runs) == 24 and ids[0] == RERUN and len(set(ids)) == 24
    assert not any(i in DONE or (C.RUNS / i).exists() for i in ids)
    if [r.get("rerun_of", r["run_id"]) for r in runs] != [e["run_id"] for e in v10["runs"] if e["run_id"] not in DONE]:
        raise SystemExit("order differs from v10")
    v10map = {e["run_id"]: e for e in v10["runs"]}
    same = ["K", "layer_indices", "training_seed", "lora_init_seed", "condition_labels", "protocol_file_hash", "addendum_sha256", "frozen_rankings_sha256", "equivalence_sha256", "cache", "est_seconds"]
    for r in runs:
        if any(r[k] != v10map[r.get("rerun_of", r["run_id"])][k] for k in same):
            raise SystemExit(f"{r['run_id']}: training field differs from v10")
    keep = ("manifest_v1_sha256", "manifest_v2_sha256", "manifest_v3_sha256", "manifest_v4_sha256", "manifest_v5_sha256", "manifest_v6_sha256", "manifest_v7_sha256", "manifest_v8_sha256",
            "manifest_v9_sha256", "completed_pilot_runs", "train_and_sanity_code_hash", "fingerprints", "backbone_fp", "probe_hash", "per_seed_expected", "limits", "failure_policy")
    sa = dict(v10["safety_additions"])
    sa["interruption_log"] = "logs/gate2_interruptions_v11.jsonl (every stop with its exact cause and stage)"
    m = {"authorization": "PENDING research-lead approval. Gate 2 recovery: exactly these 24 runs (Layer 20 seed 2000 rerun + the 23 pending v10 runs), in v10 order. No other training.",
         "version": 11, "supersedes_for_remaining_runs": "manifest_gate2_recovery_v10.json (preserved unchanged)", "manifest_v10_sha256": V10_SHA,
         **{k: v10[k] for k in keep}, "safety_additions": sa, "pilot_hashes": pilot,
         "completed_gate2_runs_kept": done,
         "preserved_interrupted_runs": v10["preserved_interrupted_runs"] + [{"run_id": FAILED, "file_sha256": L20B_FILES, "replaced_by": RERUN,
                                                                             "incident_report": inc9.name, "incident_report_sha256": C.sha256_file(inc9)}],
         "analysis": "gate2_analysis_v11.py: the frozen gate2_analysis.py with Layers 2, 6, 7 at seed 1000 and Layers 2, 4, 15, 20 at seed 2000 mapped to their _a2 reruns",
         "code_hash": C.code_hash(),
         "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=C.PROJECT, capture_output=True, text=True).stdout.strip(),
         "est_hours": sum(r["est_seconds"] for r in runs) / 3600, "runs": runs}
    out = C.ART / "manifest_gate2_recovery_v11.json"
    if out.exists():
        raise SystemExit("manifest v11 already exists; not overwritten")
    C.write_json_atomic(out, m)
    sha = C.sha256_file(out)
    C.write_json_atomic(C.ART / "gate2" / "recovery_v11_audit.json", {"manifest_v11_sha256": sha, "real_interruption_evidence": evidence,
                                                                     "locked_test_set": G10.locked_test_untouched(ids), "environment_at_manifest_time": G10.environment(),
                                                                     "completed_runs": DONE, "failed_partial_runs": [e["run_id"] for e in m["preserved_interrupted_runs"]],
                                                                     "pending_runs": len(runs), "frozen_artifacts_unchanged": True, "data_stream_replay_ok": True})
    print("manifest v11:", len(runs), "runs, est h", round(m["est_hours"], 2), "sha256", sha)


if __name__ == "__main__":
    main()
