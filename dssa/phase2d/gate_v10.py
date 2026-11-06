"""Writes recovery manifest v10 after verifying the recovery inventory: manifests
v1 to v9 unchanged, the 34 completed Gate 2 runs and the pilot passing their
integrity checks, the six interrupted folders in their preserved state, INCIDENT_003
to 008 recorded, both real-training interruptions (v8 L04 s2000, v9 L15 s2000)
consistent, no locked test tile opened, and the frozen artifacts unchanged. Runs and
every training field are copied from v9 in v9 order; completed runs are removed and
only the Layer 15 seed 2000 run ID changes, to p2d_oracle_L15_s2000_a2. Also writes
gate2/recovery_v10_audit.json."""
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
import gate_v8 as G8  # noqa: E402
import gate_v9 as G9  # noqa: E402

V9 = C.ART / "manifest_gate2_recovery_v9.json"
V9_SHA = "7e77b72c5b8b91847e948eb171dfed05f16a8e83e43e2095d590ed42751533db"
V9_DONE = ["p2d_oracle_L04_s2000_a2"] + [f"p2d_oracle_L{l:02d}_s2000" for l in (5, 6, 7, 8, 9, 10, 11, 13, 14)]
DONE = G9.DONE + V9_DONE
FAILED, RERUN = "p2d_oracle_L15_s2000", "p2d_oracle_L15_s2000_a2"
L15B_FILES = {"IN_PROGRESS": "c9948e58126fa7c6704d3d1afe318dc81f81a2b286e60a48a82cf87fd6e0909f",
              "incident.json": "d2ce925fdb432749cacaaf7249b789c2cc6f44397b391a338fd9b7e76fcde8db",
              f"{FAILED}_best.pt": "2b9f267bb82b8205fa685c93c4cceb7b60dafc0b00c89e0fd8655c2951986ec1",
              "telemetry.jsonl": "932dfd11b7aa1578d988e5ae7738c0c80f183a64e4fe326a92236954367bf7eb"}


def interruption_evidence(ver, rid, manifest):
    """A real-training stop under the repaired runner: incident.json, child exit code,
    stop latency and sequence termination, all from the preserved logs."""
    g = [json.loads(l) for l in open(C.ART / "logs" / f"gate2_guard_{ver}.jsonl")]
    seq = next(e for e in g if e.get("stage") == "sequence start")
    hz = next(e for e in g if e.get("run") == rid and e.get("hazard"))
    ex = next(e for e in g if e.get("run") == rid and e.get("action") == "child exited after interrupt")
    inc = json.load(open(C.RUNS / rid / "incident.json"))
    st = json.load(open(C.ART / f"gate2_status_{ver}.json"))
    inter = [json.loads(l) for l in open(C.ART / "logs" / f"gate2_interruptions_{ver}.jsonl")]
    log = (C.ART / "logs" / f"{rid}.log").read_text()
    sig = json.loads(log.split("[signals] ", 1)[1].split("\n", 1)[0])
    later = [e["run"] for e in g if e.get("action") == "child started" and e["t"] > hz["t"]]  # in this sequence's own log
    ev = {"manifest": manifest.name, "run": rid, "sequence_signals": {k: seq["signals"][k]["os"] for k in ("SIGINT", "SIGTERM")},
          "run_pid": sig["pid"], "run_signals": {k: sig[k]["os"] for k in ("SIGINT", "SIGTERM")}, "guard_child_pid": hz["child_pid"],
          "hazard": hz["hazard"], "action": hz["action"], "child_returncode": ex["returncode"], "stop_latency_s": round(ex["t"] - hz["t"], 3),
          "sigkill_used": any("SIGKILL" in str(e.get("action")) for e in g if e.get("run") == rid),
          "incident": {k: inc[k] for k in ("error", "stage", "optimizer_steps_completed", "batches_drawn", "evals_completed", "elapsed_s")},
          "incident_fields_complete": all(k in inc for k in ("error", "traceback", "time", "elapsed_s", "optimizer_steps_completed", "batches_drawn", "stage", "evals_completed",
                                                             "memory_final", "swap_used_mb", "swap_at_start_mb", "pressure", "sampled_max", "telemetry_tail", "tiles_opened")),
          "sequence_state": st["state"], "completed_in_sequence": len(st["completed"]), "interruption_logged": inter[-1]["run"] == rid and inter[-1]["incident_written"],
          "later_runs_started": later}
    ok = (ev["sequence_signals"] == ev["run_signals"] == {"SIGINT": "caught", "SIGTERM": "caught"} and ev["run_pid"] == ev["guard_child_pid"]
          and ev["child_returncode"] == -2 and not ev["sigkill_used"] and ev["incident"]["error"] == "KeyboardInterrupt()" and ev["incident_fields_complete"]
          and ev["sequence_state"] == "stopped" and ev["interruption_logged"] and not later)
    if not ok:
        raise SystemExit(f"interruption evidence inconsistent: {ev}")
    return ev


def locked_test_untouched(ids):
    """Every completed result and every incident lists only allowed (train/validation) tiles."""
    seen, bad = 0, []
    for d in sorted(C.RUNS.iterdir()):
        for f in ("result.json", "incident.json"):
            p = d / f
            if p.exists():
                r = json.load(open(p))
                t = set(r["post_run_checks"]["tiles_opened"] if f == "result.json" else r.get("tiles_opened", []))
                seen += 1
                if (t & C.FORBIDDEN) or (t - C.ALLOWED_TILES):
                    bad.append(str(p))
    if bad:
        raise SystemExit(f"tile check failed: {bad}")
    return {"records_checked": seen, "forbidden_tiles_opened": 0, "locked_test_tiles": len(C.FORBIDDEN)}


def _out(args):
    return subprocess.run(args, capture_output=True, text=True).stdout


def environment():
    swap = _out(["sysctl", "-n", "vm.swapusage"]).strip()
    procs = [l for l in _out(["pgrep", "-fl", "-i", "docker|Virtualization.VirtualMachine"]).splitlines() if l.strip()]
    return {"time": time.strftime("%Y-%m-%d %H:%M:%S %Z"), "swapusage": swap, "memory_pressure_level": C.pressure_level(),
            "docker_or_vm_processes": [p[:120] for p in procs],
            "virtual_machine_running": any("Virtualization.VirtualMachine" in p or "com.docker.virtualization" in p for p in procs)}


def main():
    for p, h in ((V9, V9_SHA), (G9.V8, G9.V8_SHA), (G8.V7, G8.V7_SHA), (G7.V6, G7.V6_SHA), (G5.V4, G5.V4_SHA), (C.ART / "manifest_gate2_recovery_v5.json", G6.V5_SHA)):
        if C.sha256_file(p) != h:
            raise SystemExit(f"{p.name} changed")
    v9 = json.load(open(V9))
    C.assert_frozen_unchanged()
    base = json.load(open(C.BASELINE))
    if not all(C.simulate_data_stream(s) == base["expected"][str(s)]["data_stream_final"] for s in C.PILOT_SEEDS):
        raise SystemExit("data stream replay differs")
    pilot = {k: G5.verified(r) for k, r in v9["completed_pilot_runs"].items()}
    done = {r: G5.verified(r) for r in DONE}
    for e in v9["preserved_interrupted_runs"]:
        if G5.folder_hashes(e["run_id"]) != e["file_sha256"]:
            raise SystemExit(f"{e['run_id']} partial folder changed")
        if C.sha256_file(C.ART / "logs" / e["incident_report"]) != e["incident_report_sha256"]:
            raise SystemExit(f"{e['incident_report']} changed")
    if G5.folder_hashes(FAILED) != L15B_FILES or (C.RUNS / RERUN).exists():
        raise SystemExit("Layer 15 seed 2000 evidence is not in its preserved state, or the rerun folder exists")
    inc8 = C.ART / "logs" / "INCIDENT_008_gate2_v9_lid_closed.md"
    evidence = [interruption_evidence("v8", G9.FAILED, G9.V8), interruption_evidence("v9", FAILED, V9)]
    runs = []
    for e in v9["runs"]:
        if e["run_id"] in DONE:
            continue
        n = dict(e)
        n.pop("rerun_of", None)
        if n["run_id"] == FAILED:
            n["run_id"] = RERUN
            n["rerun_of"] = FAILED
        n["phase"] = "2D-gate2-recovery-v10"
        n["config_hash"] = C.config_hash(n)
        runs.append(n)
    ids = [r["run_id"] for r in runs]
    assert len(DONE) == 34 and len(set(DONE)) == 34
    assert len(runs) == 29 and ids[0] == RERUN and len(set(ids)) == 29
    assert not any(i in DONE or (C.RUNS / i).exists() for i in ids)
    if [r.get("rerun_of", r["run_id"]) for r in runs] != [e["run_id"] for e in v9["runs"] if e["run_id"] not in DONE]:
        raise SystemExit("order differs from v9")
    v9map = {e["run_id"]: e for e in v9["runs"]}
    same = ["K", "layer_indices", "training_seed", "lora_init_seed", "condition_labels", "protocol_file_hash", "addendum_sha256", "frozen_rankings_sha256", "equivalence_sha256", "cache", "est_seconds"]
    for r in runs:
        if any(r[k] != v9map[r.get("rerun_of", r["run_id"])][k] for k in same):
            raise SystemExit(f"{r['run_id']}: training field differs from v9")
    keep = ("manifest_v1_sha256", "manifest_v2_sha256", "manifest_v3_sha256", "manifest_v4_sha256", "manifest_v5_sha256", "manifest_v6_sha256", "manifest_v7_sha256", "manifest_v8_sha256", "completed_pilot_runs", "train_and_sanity_code_hash",
            "fingerprints", "backbone_fp", "probe_hash", "per_seed_expected", "limits")
    sa = dict(v9["safety_additions"])
    sa["interruption_log"] = "logs/gate2_interruptions_v10.jsonl (every stop with its exact cause and stage)"
    sa["preflight_before_each_run"] = [c for c in sa["preflight_before_each_run"] if c != "lid open"]
    sa["guard_during_each_run"] = {**sa["guard_during_each_run"], "lid_closed": False,
                                   "training_telemetry_stale_s": 60, "training_no_optimizer_step_s": 300}
    sa["lid"] = ("Advisory only: a closed lid is logged in preflight and by the guard, not a stop condition (research lead, 2026-11-04). "
                 "On AC with caffeinate the Mac stays in DarkWake; real sleep is still stopped by the wall-clock sleep check, and an "
                 "unresponsive or stalled training process by the telemetry and optimizer-step checks.")
    m = {"authorization": "PENDING research-lead approval. Gate 2 recovery: exactly these 29 runs (Layer 15 seed 2000 rerun + the 28 pending v9 runs), in v9 order. No other training.",
         "version": 10, "supersedes_for_remaining_runs": "manifest_gate2_recovery_v9.json (preserved unchanged)", "manifest_v9_sha256": V9_SHA,
         **{k: v9[k] for k in keep}, "pilot_hashes": pilot,
         "completed_gate2_runs_kept": done,
         "preserved_interrupted_runs": v9["preserved_interrupted_runs"] + [{"run_id": FAILED, "file_sha256": L15B_FILES, "replaced_by": RERUN,
                                                                            "incident_report": inc8.name, "incident_report_sha256": C.sha256_file(inc8)}],
         "analysis": "gate2_analysis_v10.py: the frozen gate2_analysis.py with Layers 2, 6, 7 at seed 1000 and Layers 2, 4, 15 at seed 2000 mapped to their _a2 reruns",
         "code_hash": C.code_hash(), "safety_additions": sa,
         "failure_policy": v9["failure_policy"],
         "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=C.PROJECT, capture_output=True, text=True).stdout.strip(),
         "est_hours": sum(r["est_seconds"] for r in runs) / 3600, "runs": runs}
    out = C.ART / "manifest_gate2_recovery_v10.json"
    if out.exists():
        raise SystemExit("manifest v10 already exists; not overwritten")
    C.write_json_atomic(out, m)
    sha = C.sha256_file(out)
    C.write_json_atomic(C.ART / "gate2" / "recovery_v10_audit.json", {"manifest_v10_sha256": sha, "real_interruption_evidence": evidence, "locked_test_set": locked_test_untouched(ids), "environment_at_manifest_time": environment(),
                                                                     "completed_runs": DONE, "failed_partial_runs": [e["run_id"] for e in m["preserved_interrupted_runs"]],
                                                                     "pending_runs": len(runs), "frozen_artifacts_unchanged": True, "data_stream_replay_ok": True})
    print("manifest v10:", len(runs), "runs, est h", round(m["est_hours"], 2), "sha256", sha)


if __name__ == "__main__":
    main()
