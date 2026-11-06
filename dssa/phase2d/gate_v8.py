"""Writes recovery manifest v8 after verifying the recovery inventory: manifests
v1 to v7 unchanged, the 22 completed Gate 2 runs and the pilot passing their
integrity checks, the interrupted Layer 2 s1000, Layer 6 s1000, Layer 7 s1000 and
Layer 2 s2000 folders in their preserved state, INCIDENT_003 to 006 recorded, and
the frozen artifacts unchanged. Runs and every training field are copied from v7
in v7 order; completed runs are removed and only the Layer 2 seed 2000 run ID
changes, to p2d_oracle_L02_s2000_a2. Also writes gate2/recovery_v8_audit.json."""
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
import gate_v7 as G7  # noqa: E402

V7 = C.ART / "manifest_gate2_recovery_v7.json"
V7_SHA = "a4a19944816713cd938fefb475894f1980af44f89df7552bce2f90579f8b3e56"
V7_DONE = ["p2d_oracle_L07_s1000_a2"] + [f"p2d_oracle_L{l:02d}_s1000" for l in (8, 9, 10, 11, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22)] + ["p2d_oracle_L01_s2000"]
DONE = G7.DONE + V7_DONE
FAILED, RERUN = "p2d_oracle_L02_s2000", "p2d_oracle_L02_s2000_a2"
L02B_FILES = {"IN_PROGRESS": "e32b59c352f1eabd358476de257cd0df6481c06c684dab119040c8bb31b8cb95",
              f"{FAILED}_best.pt": "c5eed1466da22452c20424143a69c2e773091433107510151cd5f9aba884414c",
              "telemetry.jsonl": "5557da8a0059e96539719fd8d21cb184bdde65802447d169e878da4361bad80e"}


def _out(args):
    return subprocess.run(args, capture_output=True, text=True).stdout


def environment():
    swap = _out(["sysctl", "-n", "vm.swapusage"]).strip()
    procs = [l for l in _out(["pgrep", "-fl", "-i", "docker|Virtualization.VirtualMachine"]).splitlines() if l.strip()]
    return {"time": time.strftime("%Y-%m-%d %H:%M:%S %Z"), "swapusage": swap, "memory_pressure_level": C.pressure_level(),
            "docker_or_vm_processes": [p[:120] for p in procs],
            "virtual_machine_running": any("Virtualization.VirtualMachine" in p or "com.docker.virtualization" in p for p in procs)}


def main():
    for p, h in ((V7, V7_SHA), (G7.V6, G7.V6_SHA), (G5.V4, G5.V4_SHA), (C.ART / "manifest_gate2_recovery_v5.json", G6.V5_SHA)):
        if C.sha256_file(p) != h:
            raise SystemExit(f"{p.name} changed")
    v7 = json.load(open(V7))
    C.assert_frozen_unchanged()
    base = json.load(open(C.BASELINE))
    if not all(C.simulate_data_stream(s) == base["expected"][str(s)]["data_stream_final"] for s in C.PILOT_SEEDS):
        raise SystemExit("data stream replay differs")
    pilot = {k: G5.verified(r) for k, r in v7["completed_pilot_runs"].items()}
    done = {r: G5.verified(r) for r in DONE}
    for e in v7["preserved_interrupted_runs"]:
        if G5.folder_hashes(e["run_id"]) != e["file_sha256"]:
            raise SystemExit(f"{e['run_id']} partial folder changed")
        if C.sha256_file(C.ART / "logs" / e["incident_report"]) != e["incident_report_sha256"]:
            raise SystemExit(f"{e['incident_report']} changed")
    if G5.folder_hashes(FAILED) != L02B_FILES or (C.RUNS / RERUN).exists():
        raise SystemExit("Layer 2 seed 2000 evidence is not in its preserved state, or the rerun folder exists")
    inc6 = C.ART / "logs" / "INCIDENT_006_gate2_v7_charger_disconnected.md"
    rep7 = C.ART / "gate2" / "GATE2_V7_PARTIAL_RESULTS.md"
    runs = []
    for e in v7["runs"]:
        if e["run_id"] in DONE:
            continue
        n = dict(e)
        n.pop("rerun_of", None)
        if n["run_id"] == FAILED:
            n["run_id"] = RERUN
            n["rerun_of"] = FAILED
        n["phase"] = "2D-gate2-recovery-v8"
        n["config_hash"] = C.config_hash(n)
        runs.append(n)
    ids = [r["run_id"] for r in runs]
    assert len(DONE) == 22 and len(set(DONE)) == 22
    assert len(runs) == 41 and ids[0] == RERUN and len(set(ids)) == 41
    assert not any(i in DONE or (C.RUNS / i).exists() for i in ids)
    if [r.get("rerun_of", r["run_id"]) for r in runs] != [e["run_id"] for e in v7["runs"] if e["run_id"] not in DONE]:
        raise SystemExit("order differs from v7")
    v7map = {e["run_id"]: e for e in v7["runs"]}
    same = ["K", "layer_indices", "training_seed", "lora_init_seed", "condition_labels", "protocol_file_hash", "addendum_sha256", "frozen_rankings_sha256", "equivalence_sha256", "cache", "est_seconds"]
    for r in runs:
        if any(r[k] != v7map[r.get("rerun_of", r["run_id"])][k] for k in same):
            raise SystemExit(f"{r['run_id']}: training field differs from v7")
    keep = ("manifest_v1_sha256", "manifest_v2_sha256", "manifest_v3_sha256", "manifest_v4_sha256", "manifest_v5_sha256", "manifest_v6_sha256", "completed_pilot_runs", "train_and_sanity_code_hash",
            "fingerprints", "backbone_fp", "probe_hash", "per_seed_expected", "limits")
    sa = dict(v7["safety_additions"])
    sa["interruption_log"] = "logs/gate2_interruptions_v8.jsonl (every stop with its exact cause and stage)"
    sa["signal_handling"] = ("sigsafe.restore() in the sequence process and in every run and reload process: SIGINT raises KeyboardInterrupt, "
                             "SIGTERM raises Terminated; run_one_v2 writes incident.json. SIGINT/SIGTERM to the sequence process is forwarded to the "
                             "active run as SIGINT and the sequence stops (INCIDENT_006). SIGKILL after 180 s remains only as a fallback.")
    m = {"authorization": "PENDING research-lead approval. Gate 2 recovery: exactly these 41 runs (Layer 2 seed 2000 rerun + the 40 pending v7 runs), in v7 order. No other training.",
         "version": 8, "supersedes_for_remaining_runs": "manifest_gate2_recovery_v7.json (preserved unchanged)", "manifest_v7_sha256": V7_SHA,
         **{k: v7[k] for k in keep}, "pilot_hashes": pilot,
         "completed_gate2_runs_kept": done,
         "preserved_interrupted_runs": v7["preserved_interrupted_runs"] + [{"run_id": FAILED, "file_sha256": L02B_FILES, "replaced_by": RERUN,
                                                                            "incident_report": inc6.name, "incident_report_sha256": C.sha256_file(inc6),
                                                                            "partial_results_sha256": C.sha256_file(rep7)}],
         "analysis": "gate2_analysis_v8.py: the frozen gate2_analysis.py with Layers 2, 6, 7 at seed 1000 and Layer 2 at seed 2000 mapped to their _a2 reruns",
         "code_hash": C.code_hash(), "safety_additions": sa,
         "failure_policy": v7["failure_policy"],
         "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=C.PROJECT, capture_output=True, text=True).stdout.strip(),
         "est_hours": sum(r["est_seconds"] for r in runs) / 3600, "runs": runs}
    out = C.ART / "manifest_gate2_recovery_v8.json"
    if out.exists():
        raise SystemExit("manifest v8 already exists; not overwritten")
    C.write_json_atomic(out, m)
    sha = C.sha256_file(out)
    C.write_json_atomic(C.ART / "gate2" / "recovery_v8_audit.json", {"manifest_v8_sha256": sha, "environment_at_manifest_time": environment(),
                                                                     "completed_runs": DONE, "failed_partial_runs": [e["run_id"] for e in m["preserved_interrupted_runs"]],
                                                                     "pending_runs": len(runs), "frozen_artifacts_unchanged": True, "data_stream_replay_ok": True})
    print("manifest v8:", len(runs), "runs, est h", round(m["est_hours"], 2), "sha256", sha)


if __name__ == "__main__":
    main()
