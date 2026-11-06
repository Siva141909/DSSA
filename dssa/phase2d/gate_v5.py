"""Writes recovery manifest v5 after verifying that manifest v4, the completed
Layer 1 run, the interrupted Layer 2 folder, INCIDENT_003, the pilot evidence and
the frozen artifacts are intact. v1 to v4 are preserved unchanged. Order, seeds
and every training field are copied from v4; only the Layer 2 seed 1000 run ID
changes, to p2d_oracle_L02_s1000_a2."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

C.install_guards()
V4 = C.ART / "manifest_gate2_v4.json"
V4_SHA = "b855b97241b72517b0ac4605e19d6bd76601406bbc64986d1e88c19f2a5d7639"
DONE, FAILED, RERUN = "p2d_oracle_L01_s1000", "p2d_oracle_L02_s1000", "p2d_oracle_L02_s1000_a2"


def folder_hashes(rid):
    d = C.RUNS / rid
    return {p.name: C.sha256_file(p) for p in sorted(d.iterdir()) if p.is_file()}


def verified(rid):
    d = C.RUNS / rid
    r, h = json.load(open(d / "result.json")), json.load(open(d / "hashes.json"))
    ok = (r["status"] == "completed" and r["post_run_checks"]["steps"] == 2000 and C.sha256_file(d / "result.json") == h["result_sha256"]
          and all(C.sha256_file(d / f"{rid}_{t}.pt") == h["checkpoints"][t]["sha256"] and h["checkpoints"][t]["cm_diff"] == 0 for t in ("best", "final")))
    if not ok:
        raise SystemExit(f"{rid}: evidence check failed")
    return h


def main():
    if C.sha256_file(V4) != V4_SHA:
        raise SystemExit("manifest v4 changed")
    v4 = json.load(open(V4))
    C.assert_frozen_unchanged()
    base = json.load(open(C.BASELINE))
    if not all(C.simulate_data_stream(s) == base["expected"][str(s)]["data_stream_final"] for s in C.PILOT_SEEDS):
        raise SystemExit("data stream replay differs")
    pilot = {k: verified(r) for k, r in v4["completed_pilot_runs"].items()}
    l01 = verified(DONE)
    l02 = folder_hashes(FAILED)
    if set(l02) != {"IN_PROGRESS", "incident.json", f"{FAILED}_best.pt", "telemetry.jsonl"} or (C.RUNS / RERUN).exists():
        raise SystemExit("Layer 2 evidence is not in its preserved state, or the rerun folder exists")
    inc = C.ART / "logs" / "INCIDENT_003_gate2_runtime_stop_system_sleep.md"
    runs = []
    for e in v4["runs"]:
        if e["run_id"] == DONE:
            continue
        n = dict(e)
        if n["run_id"] == FAILED:
            n["run_id"] = RERUN
            n["rerun_of"] = FAILED
        n["phase"] = "2D-gate2-recovery-v5"
        n["config_hash"] = C.config_hash(n)
        runs.append(n)
    assert len(runs) == 62 and runs[0]["run_id"] == RERUN and len({r["run_id"] for r in runs}) == 62
    same = [k for k in ("K", "layer_indices", "training_seed", "lora_init_seed", "condition_labels", "protocol_file_hash", "addendum_sha256", "frozen_rankings_sha256", "equivalence_sha256", "cache", "est_seconds")]
    v4map = {e["run_id"]: e for e in v4["runs"]}
    for r in runs:
        o = v4map[r.get("rerun_of", r["run_id"])]
        if any(r[k] != o[k] for k in same):
            raise SystemExit(f"{r['run_id']}: training field differs from v4")
    m = {"authorization": "PENDING research-lead approval. Gate 2 recovery: exactly these 62 runs (Layer 2 seed 1000 rerun + the 61 pending v4 runs), in v4 order. No other training.",
         "version": 5, "supersedes_for_remaining_runs": "manifest_gate2_v4.json (preserved unchanged)", "manifest_v4_sha256": V4_SHA,
         "manifest_v1_sha256": v4["manifest_v1_sha256"], "manifest_v2_sha256": v4["manifest_v2_sha256"], "manifest_v3_sha256": v4["manifest_v3_sha256"],
         "completed_pilot_runs": v4["completed_pilot_runs"], "pilot_hashes": pilot,
         "completed_gate2_runs_kept": {DONE: l01},
         "preserved_interrupted_run": {"run_id": FAILED, "file_sha256": l02, "replaced_by": RERUN, "incident_report": inc.name, "incident_report_sha256": C.sha256_file(inc),
                                       "partial_results_sha256": C.sha256_file(C.ART / "gate2" / "GATE2_PARTIAL_RESULTS.md")},
         "analysis": "gate2_analysis_v5.py: the frozen gate2_analysis.py with Layer 2 seed 1000 mapped to " + RERUN,
         "code_hash": C.code_hash(), "train_and_sanity_code_hash": v4["train_and_sanity_code_hash"], "fingerprints": v4["fingerprints"],
         "backbone_fp": v4["backbone_fp"], "probe_hash": v4["probe_hash"], "per_seed_expected": v4["per_seed_expected"], "limits": v4["limits"],
         "safety_additions": {"preflight_before_each_run": ["charger connected", "lid open", "no thermal or performance warning", "memory pressure normal", "free disk >= 10 GB", "required files local, not cloud-only", "no other Phase 2D run"],
                              "guard_during_each_run": {"system_sleep_gap_s": 30, "charger_disconnected_polls": 2, "lid_closed": True, "thermal_warning": True, "pressure_critical": True, "action": "SIGINT to the run (incident.json written), sequence stops, no retry"}},
         "failure_policy": "Stop the whole sequence at the first failure, stop condition, guard stop or failed integrity check. No retry, no skip.",
         "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=C.PROJECT, capture_output=True, text=True).stdout.strip(),
         "est_hours": sum(r["est_seconds"] for r in runs) / 3600, "runs": runs}
    out = C.ART / "manifest_gate2_recovery_v5.json"
    if out.exists():
        raise SystemExit("manifest v5 already exists; not overwritten")
    C.write_json_atomic(out, m)
    print("manifest v5:", len(runs), "runs, est h", round(m["est_hours"], 2), "sha256", C.sha256_file(out))


if __name__ == "__main__":
    main()
