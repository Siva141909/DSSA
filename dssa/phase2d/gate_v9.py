"""Writes recovery manifest v9 after verifying the recovery inventory: manifests
v1 to v8 unchanged, the 24 completed Gate 2 runs and the pilot passing their
integrity checks, the five interrupted folders in their preserved state, INCIDENT_003
to 007 recorded, the real v8 interruption evidence consistent, no locked test tile
opened by any run, and the frozen artifacts unchanged. Runs and every training field
are copied from v8 in v8 order; completed runs are removed and only the Layer 4 seed
2000 run ID changes, to p2d_oracle_L04_s2000_a2. Also writes gate2/recovery_v9_audit.json."""
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

V8 = C.ART / "manifest_gate2_recovery_v8.json"
V8_SHA = "fbb9dc0f97b3035fea2dd089c3bbad310c6e47189273c5882d72d00986f08427"
DONE = G8.DONE + ["p2d_oracle_L02_s2000_a2", "p2d_oracle_L03_s2000"]
FAILED, RERUN = "p2d_oracle_L04_s2000", "p2d_oracle_L04_s2000_a2"
L04B_FILES = {"IN_PROGRESS": "476afbe99ee85bbb440bb32f916a864d42459ec76d1b8410109b21c02033f178",
              "incident.json": "21b063fd75624a462fffd5d8dba4681d3e80bb5ab085e3680e05a940acce4af3",
              f"{FAILED}_best.pt": "dec5eba0c41d7d256e14759bbcc4d529dd9765357ec00fbffa498808e5bc9135",
              "telemetry.jsonl": "a3ed282aa6feca1cd84f1e1e859903363cbbf9de6fa279dc6bc69ad929bbc35e"}


def v8_interruption_evidence():
    """The real-training stop under v8 (INCIDENT_007): incident.json, child exit code,
    stop latency and sequence termination, all from the preserved logs."""
    g = [json.loads(l) for l in open(C.ART / "logs" / "gate2_guard_v8.jsonl")]
    seq = next(e for e in g if e.get("stage") == "sequence start")
    hz = next(e for e in g if e.get("run") == FAILED and e.get("hazard"))
    ex = next(e for e in g if e.get("run") == FAILED and e.get("action") == "child exited after interrupt")
    inc = json.load(open(C.RUNS / FAILED / "incident.json"))
    st = json.load(open(C.ART / "gate2_status_v8.json"))
    inter = [json.loads(l) for l in open(C.ART / "logs" / "gate2_interruptions_v8.jsonl")]
    log = (C.ART / "logs" / f"{FAILED}.log").read_text()
    sig = json.loads(log.split("[signals] ", 1)[1].split("\n", 1)[0])
    v8runs = [e["run_id"] for e in json.load(open(V8))["runs"]]
    later = [r for r in v8runs[v8runs.index(FAILED) + 1:] if (C.RUNS / r).exists()]
    ev = {"sequence_signals": {k: seq["signals"][k]["os"] for k in ("SIGINT", "SIGTERM")},
          "run_pid": sig["pid"], "run_signals": {k: sig[k]["os"] for k in ("SIGINT", "SIGTERM")}, "guard_child_pid": hz["child_pid"],
          "hazard": hz["hazard"], "action": hz["action"], "child_returncode": ex["returncode"], "stop_latency_s": round(ex["t"] - hz["t"], 3),
          "sigkill_used": any("SIGKILL" in str(e.get("action")) for e in g if e.get("run") == FAILED),
          "incident": {k: inc[k] for k in ("error", "stage", "optimizer_steps_completed", "batches_drawn", "evals_completed", "elapsed_s")},
          "incident_fields_complete": all(k in inc for k in ("error", "traceback", "time", "elapsed_s", "optimizer_steps_completed", "batches_drawn", "stage", "evals_completed",
                                                             "memory_final", "swap_used_mb", "swap_at_start_mb", "pressure", "sampled_max", "telemetry_tail", "tiles_opened")),
          "sequence_state": st["state"], "completed_in_v8": st["completed"], "interruption_logged": inter[-1]["run"] == FAILED and inter[-1]["incident_written"],
          "later_v8_runs_started": later}
    ok = (ev["sequence_signals"] == ev["run_signals"] == {"SIGINT": "caught", "SIGTERM": "caught"} and ev["run_pid"] == ev["guard_child_pid"]
          and ev["child_returncode"] == -2 and not ev["sigkill_used"] and ev["incident"]["error"] == "KeyboardInterrupt()" and ev["incident_fields_complete"]
          and ev["sequence_state"] == "stopped" and ev["interruption_logged"] and not later)
    if not ok:
        raise SystemExit(f"v8 interruption evidence inconsistent: {ev}")
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
    for p, h in ((V8, V8_SHA), (G8.V7, G8.V7_SHA), (G7.V6, G7.V6_SHA), (G5.V4, G5.V4_SHA), (C.ART / "manifest_gate2_recovery_v5.json", G6.V5_SHA)):
        if C.sha256_file(p) != h:
            raise SystemExit(f"{p.name} changed")
    v8 = json.load(open(V8))
    C.assert_frozen_unchanged()
    base = json.load(open(C.BASELINE))
    if not all(C.simulate_data_stream(s) == base["expected"][str(s)]["data_stream_final"] for s in C.PILOT_SEEDS):
        raise SystemExit("data stream replay differs")
    pilot = {k: G5.verified(r) for k, r in v8["completed_pilot_runs"].items()}
    done = {r: G5.verified(r) for r in DONE}
    for e in v8["preserved_interrupted_runs"]:
        if G5.folder_hashes(e["run_id"]) != e["file_sha256"]:
            raise SystemExit(f"{e['run_id']} partial folder changed")
        if C.sha256_file(C.ART / "logs" / e["incident_report"]) != e["incident_report_sha256"]:
            raise SystemExit(f"{e['incident_report']} changed")
    if G5.folder_hashes(FAILED) != L04B_FILES or (C.RUNS / RERUN).exists():
        raise SystemExit("Layer 4 seed 2000 evidence is not in its preserved state, or the rerun folder exists")
    inc7 = C.ART / "logs" / "INCIDENT_007_gate2_v8_lid_closed.md"
    evidence = v8_interruption_evidence()
    runs = []
    for e in v8["runs"]:
        if e["run_id"] in DONE:
            continue
        n = dict(e)
        n.pop("rerun_of", None)
        if n["run_id"] == FAILED:
            n["run_id"] = RERUN
            n["rerun_of"] = FAILED
        n["phase"] = "2D-gate2-recovery-v9"
        n["config_hash"] = C.config_hash(n)
        runs.append(n)
    ids = [r["run_id"] for r in runs]
    assert len(DONE) == 24 and len(set(DONE)) == 24
    assert len(runs) == 39 and ids[0] == RERUN and len(set(ids)) == 39
    assert not any(i in DONE or (C.RUNS / i).exists() for i in ids)
    if [r.get("rerun_of", r["run_id"]) for r in runs] != [e["run_id"] for e in v8["runs"] if e["run_id"] not in DONE]:
        raise SystemExit("order differs from v8")
    v8map = {e["run_id"]: e for e in v8["runs"]}
    same = ["K", "layer_indices", "training_seed", "lora_init_seed", "condition_labels", "protocol_file_hash", "addendum_sha256", "frozen_rankings_sha256", "equivalence_sha256", "cache", "est_seconds"]
    for r in runs:
        if any(r[k] != v8map[r.get("rerun_of", r["run_id"])][k] for k in same):
            raise SystemExit(f"{r['run_id']}: training field differs from v8")
    keep = ("manifest_v1_sha256", "manifest_v2_sha256", "manifest_v3_sha256", "manifest_v4_sha256", "manifest_v5_sha256", "manifest_v6_sha256", "manifest_v7_sha256", "completed_pilot_runs", "train_and_sanity_code_hash",
            "fingerprints", "backbone_fp", "probe_hash", "per_seed_expected", "limits")
    sa = dict(v8["safety_additions"])
    sa["interruption_log"] = "logs/gate2_interruptions_v9.jsonl (every stop with its exact cause and stage)"
    m = {"authorization": "PENDING research-lead approval. Gate 2 recovery: exactly these 39 runs (Layer 4 seed 2000 rerun + the 38 pending v8 runs), in v8 order. No other training.",
         "version": 9, "supersedes_for_remaining_runs": "manifest_gate2_recovery_v8.json (preserved unchanged)", "manifest_v8_sha256": V8_SHA,
         **{k: v8[k] for k in keep}, "pilot_hashes": pilot,
         "completed_gate2_runs_kept": done,
         "preserved_interrupted_runs": v8["preserved_interrupted_runs"] + [{"run_id": FAILED, "file_sha256": L04B_FILES, "replaced_by": RERUN,
                                                                            "incident_report": inc7.name, "incident_report_sha256": C.sha256_file(inc7)}],
         "analysis": "gate2_analysis_v9.py: the frozen gate2_analysis.py with Layers 2, 6, 7 at seed 1000 and Layers 2, 4 at seed 2000 mapped to their _a2 reruns",
         "code_hash": C.code_hash(), "safety_additions": sa,
         "failure_policy": v8["failure_policy"],
         "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=C.PROJECT, capture_output=True, text=True).stdout.strip(),
         "est_hours": sum(r["est_seconds"] for r in runs) / 3600, "runs": runs}
    out = C.ART / "manifest_gate2_recovery_v9.json"
    if out.exists():
        raise SystemExit("manifest v9 already exists; not overwritten")
    C.write_json_atomic(out, m)
    sha = C.sha256_file(out)
    C.write_json_atomic(C.ART / "gate2" / "recovery_v9_audit.json", {"manifest_v9_sha256": sha, "v8_real_interruption_evidence": evidence, "locked_test_set": locked_test_untouched(ids), "environment_at_manifest_time": environment(),
                                                                     "completed_runs": DONE, "failed_partial_runs": [e["run_id"] for e in m["preserved_interrupted_runs"]],
                                                                     "pending_runs": len(runs), "frozen_artifacts_unchanged": True, "data_stream_replay_ok": True})
    print("manifest v9:", len(runs), "runs, est h", round(m["est_hours"], 2), "sha256", sha)


if __name__ == "__main__":
    main()
