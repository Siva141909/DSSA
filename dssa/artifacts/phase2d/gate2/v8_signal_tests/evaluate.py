import json, sys, re
from pathlib import Path
T = Path(sys.argv[1])
MODES = ["guard_charger", "guard_lid", "guard_thermal", "guard_sleep", "manual_child_sigint", "child_sigterm", "seq_sigint", "seq_sigterm", "reload_guard", "early_signal"]
R1, R2, R3 = "p2d_oracle_L02_s2000_a2", "p2d_oracle_L03_s2000", "p2d_oracle_L04_s2000"
REQ = ["error", "traceback", "time", "elapsed_s", "optimizer_steps_completed", "batches_drawn", "stage", "evals_completed", "memory_final", "swap_used_mb", "swap_at_start_mb", "pressure", "sampled_max", "telemetry_tail", "tiles_opened"]
rows = []
for m in MODES:
    a = T / m
    g = [json.loads(l) for l in open(a / "logs" / "guard.jsonl")]
    seqsig = next(e["signals"] for e in g if e.get("stage") == "sequence start")
    starts = [(e["run"], e["stage"], e["child_pid"]) for e in g if e.get("action") == "child started"]
    haz = [e for e in g if e.get("hazard")]
    after = [e for e in g if e.get("action") == "child exited after interrupt"]
    kills = [e for e in g if "SIGKILL" in str(e.get("action"))]
    inter = [json.loads(l) for l in open(a / "logs" / "interruptions.jsonl")]
    st = json.load(open(a / "status.json"))
    stopped_rid = R1 if m == "reload_guard" else R2
    log = (a / "logs" / f"{stopped_rid}.log").read_text()
    child_sig = [json.loads(x) for x in re.findall(r"^\[dummy\] inherited signals (.*)$", log, re.M)]
    entry_sig = [json.loads(x) for x in re.findall(r"^\[signals\] (.*)$", log, re.M)]
    rl = (a / "logs" / f"{R1}.log").read_text()
    reload_sig = [json.loads(x) for x in re.findall(r"^\[dummy reload\] (?:inherited signals|after restore) (.*)$", rl, re.M)]
    inc_p = a / "runs" / stopped_rid / "incident.json"
    inc = json.load(open(inc_p)) if inc_p.exists() else None
    files = sorted(p.name for p in (a / "runs" / stopped_rid).iterdir()) if (a / "runs" / stopped_rid).exists() else []
    rows.append({
        "mode": m,
        "sequence_signals": {k: seqsig[k]["os"] for k in ("SIGINT", "SIGTERM")}, "sequence_pid": seqsig["pid"],
        "children_started": starts,
        "child_inherited_signals_from_sequence": {k: child_sig[0][k]["os"] for k in ("SIGINT", "SIGTERM")} if child_sig else None,
        "run_entry_signals_after_restore": {k: entry_sig[0][k]["os"] for k in ("SIGINT", "SIGTERM")} if entry_sig else None,
        "reload_signals": [{k: r[k]["os"] for k in ("SIGINT", "SIGTERM")} for r in reload_sig],
        "hazard": [h["hazard"] for h in haz],
        "child_exit": [(e["child_pid"], e["returncode"], e["incident_written"]) for e in after],
        "sigkill_used": bool(kills),
        "incident": None if inc is None else {"error": inc["error"], "stage": inc["stage"], "optimizer_steps_completed": inc["optimizer_steps_completed"],
                                             "batches_drawn": inc["batches_drawn"], "telemetry_tail_len": len(inc["telemetry_tail"]), "all_required_keys": all(k in inc for k in REQ)},
        "stopped_run_files": files,
        "status": st["state"], "completed": st["completed"], "interruption_log": [{k: i[k] for k in ("run", "error", "stage", "optimizer_steps_completed", "incident_written", "completed_before")} for i in inter],
        "run1_result": (a / "runs" / R1 / "result.json").exists(), "run2_started": (a / "runs" / R2).exists(), "run3_started": (a / "runs" / R3).exists(),
    })
print(json.dumps(rows, indent=1))
