"""Writes recovery manifest v7 after verifying the recovery inventory: manifests
v1 to v6 unchanged, the six completed Gate 2 runs (Layers 1-6 seed 1000) and the
pilot passing their integrity checks, the interrupted Layer 2, 6 and 7 folders in
their preserved state, INCIDENT_003/004/005 and the partial reports unchanged or
present, and the frozen artifacts unchanged. Runs and every training field are
copied from v6 in v6 order; completed runs are removed and only the Layer 7 seed
1000 run ID changes, to p2d_oracle_L07_s1000_a2. Also writes the recovery audit
(environment state at manifest time) to gate2/recovery_v7_audit.json."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
import gate_v5 as G5  # noqa: E402
import gate_v6 as G6  # noqa: E402

V6 = C.ART / "manifest_gate2_recovery_v6.json"
V6_SHA = "b4e852aaf9409b8e0bc9541b82a18f66e40bb5ab7f1113835cdefe3a572b428c"
DONE = G6.DONE + ["p2d_oracle_L06_s1000_a2"]
FAILED, RERUN = "p2d_oracle_L07_s1000", "p2d_oracle_L07_s1000_a2"
L07_FILES = {"IN_PROGRESS": "83c34d97354f4427550d41567109a5a64c21e41887cec622057f121c401942e6",
             "incident.json": "b686d7056bf97199e059e5c2af0683afd2a25512611a13b7e3b355729e28e840",
             f"{FAILED}_best.pt": "c0872e01b8e5f4d2e75d9ad746ed00e3a1edc3b0b375498dc5a4804572c996af",
             "telemetry.jsonl": "0b5193ecd47fd7a123216a9380a0f93edd9273bdb12533c9ab1d4114c7303ab1"}


def _out(args):
    return subprocess.run(args, capture_output=True, text=True).stdout


def environment():
    swap = _out(["sysctl", "-n", "vm.swapusage"]).strip()
    procs = [l for l in _out(["pgrep", "-fl", "-i", "docker|Virtualization.VirtualMachine"]).splitlines() if l.strip()]
    return {"time": time.strftime("%Y-%m-%d %H:%M:%S %Z"), "swapusage": swap, "memory_pressure_level": C.pressure_level(),
            "docker_or_vm_processes": [p[:120] for p in procs],
            "virtual_machine_running": any("Virtualization.VirtualMachine" in p or "com.docker.virtualization" in p for p in procs)}


def main():
    for p, h in ((V6, V6_SHA), (G5.V4, G5.V4_SHA), (C.ART / "manifest_gate2_recovery_v5.json", G6.V5_SHA)):
        if C.sha256_file(p) != h:
            raise SystemExit(f"{p.name} changed")
    v6 = json.load(open(V6))
    C.assert_frozen_unchanged()
    base = json.load(open(C.BASELINE))
    if not all(C.simulate_data_stream(s) == base["expected"][str(s)]["data_stream_final"] for s in C.PILOT_SEEDS):
        raise SystemExit("data stream replay differs")
    pilot = {k: G5.verified(r) for k, r in v6["completed_pilot_runs"].items()}
    done = {r: G5.verified(r) for r in DONE}
    for e in v6["preserved_interrupted_runs"]:
        if G5.folder_hashes(e["run_id"]) != e["file_sha256"]:
            raise SystemExit(f"{e['run_id']} partial folder changed")
        if C.sha256_file(C.ART / "logs" / e["incident_report"]) != e["incident_report_sha256"]:
            raise SystemExit(f"{e['incident_report']} changed")
    if G5.folder_hashes(FAILED) != L07_FILES or (C.RUNS / RERUN).exists():
        raise SystemExit("Layer 7 evidence is not in its preserved state, or the rerun folder exists")
    inc5 = C.ART / "logs" / "INCIDENT_005_gate2_v6_swap_growth_stop.md"
    runs = []
    for e in v6["runs"]:
        if e["run_id"] in DONE:
            continue
        n = dict(e)
        n.pop("rerun_of", None)
        if n["run_id"] == FAILED:
            n["run_id"] = RERUN
            n["rerun_of"] = FAILED
        n["phase"] = "2D-gate2-recovery-v7"
        n["config_hash"] = C.config_hash(n)
        runs.append(n)
    ids = [r["run_id"] for r in runs]
    assert len(runs) == 57 and ids[0] == RERUN and len(set(ids)) == 57
    assert not any(i in DONE or (C.RUNS / i).exists() for i in ids)
    if [r.get("rerun_of", r["run_id"]) for r in runs] != [e["run_id"] for e in v6["runs"] if e["run_id"] not in DONE]:
        raise SystemExit("order differs from v6")
    v6map = {e["run_id"]: e for e in v6["runs"]}
    same = ["K", "layer_indices", "training_seed", "lora_init_seed", "condition_labels", "protocol_file_hash", "addendum_sha256", "frozen_rankings_sha256", "equivalence_sha256", "cache", "est_seconds"]
    for r in runs:
        if any(r[k] != v6map[r.get("rerun_of", r["run_id"])][k] for k in same):
            raise SystemExit(f"{r['run_id']}: training field differs from v6")
    keep = ("manifest_v1_sha256", "manifest_v2_sha256", "manifest_v3_sha256", "manifest_v4_sha256", "manifest_v5_sha256", "completed_pilot_runs", "train_and_sanity_code_hash",
            "fingerprints", "backbone_fp", "probe_hash", "per_seed_expected", "limits")
    sa = dict(v6["safety_additions"])
    sa["preflight_before_each_run"] = [c for c in sa["preflight_before_each_run"] if "virtual machine" not in c]
    sa["virtual_machine"] = "Advisory only: logged before each run, not a stop condition (research lead, 2026-11-03). Resource limits stay authoritative."
    sa["interruption_log"] = "logs/gate2_interruptions_v7.jsonl (every stop with its exact cause and stage)"
    m = {"authorization": "PENDING research-lead approval. Gate 2 recovery: exactly these 57 runs (Layer 7 seed 1000 rerun + the 56 pending v6 runs), in v6 order. No other training.",
         "version": 7, "supersedes_for_remaining_runs": "manifest_gate2_recovery_v6.json (preserved unchanged)", "manifest_v6_sha256": V6_SHA,
         **{k: v6[k] for k in keep}, "pilot_hashes": pilot,
         "completed_gate2_runs_kept": done,
         "preserved_interrupted_runs": v6["preserved_interrupted_runs"] + [{"run_id": FAILED, "file_sha256": L07_FILES, "replaced_by": RERUN,
                                                                            "incident_report": inc5.name, "incident_report_sha256": C.sha256_file(inc5)}],
         "analysis": "gate2_analysis_v7.py: the frozen gate2_analysis.py with Layers 2, 6 and 7 at seed 1000 mapped to their _a2 reruns",
         "code_hash": C.code_hash(), "safety_additions": sa,
         "failure_policy": v6["failure_policy"],
         "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=C.PROJECT, capture_output=True, text=True).stdout.strip(),
         "est_hours": sum(r["est_seconds"] for r in runs) / 3600, "runs": runs}
    out = C.ART / "manifest_gate2_recovery_v7.json"
    if out.exists():
        raise SystemExit("manifest v7 already exists; not overwritten")
    C.write_json_atomic(out, m)
    sha = C.sha256_file(out)
    C.write_json_atomic(C.ART / "gate2" / "recovery_v7_audit.json", {"manifest_v7_sha256": sha, "environment_at_manifest_time": environment(),
                                                                     "completed_runs": DONE, "failed_partial_runs": [e["run_id"] for e in m["preserved_interrupted_runs"]],
                                                                     "pending_runs": len(runs), "frozen_artifacts_unchanged": True, "data_stream_replay_ok": True})
    print("manifest v7:", len(runs), "runs, est h", round(m["est_hours"], 2), "sha256", sha)


if __name__ == "__main__":
    main()
