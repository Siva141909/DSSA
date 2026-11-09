"""Phase 3 Stage B/C sequence runner. The audited run_gate2_v12 guard logic, unchanged in
substance (preflight before every run; during every child: system sleep, charger, thermal,
critical pressure, and for training telemetry staleness and optimizer-step stall; SIGINT to
the child on a hazard; sigsafe; no retry; any failure stops the sequence), plus the
approved Phase 3 limits:
  - each run = training process (no evaluation) -> reload verification process ->
    8 evaluation processes, one per Potsdam validation tile (D22, D25);
  - the sequence stops if ANY process's kernel lifetime peak footprint exceeds 10.5 GB,
    or any process wrote abort.json (11.0 GB early abort);
  - single-block runs start only if the Stage B scores are frozen and their SHA-256
    verifies, and were frozen before any single-block run folder existed;
  - the first single-block run is the early-block canary (L00, seed 1000);
  - stop and review if the first K0 run's mIoU is below 0.30 (protocol v2 section 8).
Modes: k0 | scores | canary | single | --check. Never overwrites a run folder.
canary (manifest v3): runs only p3_L00_s1000_r1, launched only if memory pressure is normal
and swap is not increasing over a 60 s observation (baseline recorded); then stops."""
from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import p3common as C  # noqa: E402

C.install_guards()
C.setup_paths()
import sigsafe  # noqa: E402
import numpy as np  # noqa: E402
from metrics import ConfusionMatrixAccumulator  # noqa: E402

PY = sys.executable
STATUS = C.ART / "sequence_status.json"
GUARD_LOG = C.LOGS / "guard.jsonl"
INTERRUPTIONS = C.LOGS / "interruptions.jsonl"
SLEEP_GAP_S, POLL_S, SLOW_POLL_S, AC_GRACE_POLLS, KILL_WAIT_S = 30, 5, 15, 2, 180
TELEMETRY_STALE_S, STEP_STALL_S = 60, 300
EVAL_HANG_S, RELOAD_HANG_S, SCORE_HANG_S = 400, 300, 3600   # watchdogs for non-training children (3x estimate)
K0_FLOOR = 0.30
SF_DATALESS = 0x40000000


def _cmd(args):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=30).stdout
    except Exception:
        return ""


def env_state(full=True):
    s = {"pressure": C.pressure_level()}
    b = _cmd(["pmset", "-g", "batt"]).splitlines()
    s["ac"] = ("AC Power" in b[0]) if b else None
    if full:
        lid = _cmd(["ioreg", "-r", "-k", "AppleClamshellState", "-d", "4"])
        s["lid_open"] = None if "AppleClamshellState" not in lid else ('"AppleClamshellState" = No' in lid)
        th = _cmd(["pmset", "-g", "therm"])
        s["thermal_ok"] = None if not th else ("No thermal warning level has been recorded" in th and "No performance warning level has been recorded" in th)
    return s


def required_files():
    s = C.split()
    fs = [C.POTSDAM_IMG_DIR / n for n in s["train"] + s["validation"]] + [C.VAIHINGEN_IMG_DIR / n for n in C.V_TRAIN]
    fs += [C.POTSDAM_LABEL_ZIP, C.ROOT / "checkpoint" / "Prithvi_EO_V2_300M.pt", C.ROOT / "checkpoint" / "prithvi_mae.py"]
    for d in (C.CODE, C.ROOT / "phase2d", C.ROOT / "train", C.ROOT / "sanity"):
        fs += [p for p in d.iterdir() if p.is_file() and p.suffix == ".py"]
    return fs


def preflight():
    s = env_state()
    free_gb = shutil.disk_usage(C.ROOT).free / 1e9
    dataless = [str(p) for p in required_files() if not p.exists() or os.lstat(p).st_flags & SF_DATALESS]
    others = [l for l in _cmd(["pgrep", "-fl", "run_one_v|run_train.py|eval_tile.py|reload_check.py|stage_b_"]).splitlines() if l.strip()]
    checks = {"charger_connected": s["ac"] is True, "no_thermal_warning": s["thermal_ok"] is True,
              "memory_pressure_normal": s["pressure"] == 1, "free_disk_ge_10gb": free_gb >= 10, "required_files_local": not dataless,
              "no_other_training_or_eval_process": not others}
    vm = bool(_cmd(["pgrep", "-f", "Virtualization.VirtualMachine|com.docker.virtualization"]).strip())
    return checks, {"state": s, "free_gb": round(free_gb, 1), "missing_or_cloud_only": dataless[:10], "other_processes": others[:5],
                    "virtual_machine_running_advisory": vm, "lid_open_advisory": s["lid_open"]}


def run_health(rid, now, prog):
    p = C.RUNS / rid / "telemetry.jsonl"
    if not p.exists():
        return None
    age = now - p.stat().st_mtime
    if age > TELEMETRY_STALE_S:
        return f"training process unresponsive (telemetry not updated for {age:.0f} s)"
    with open(p, "rb") as f:
        f.seek(max(0, p.stat().st_size - 4096))
        tail = f.read().decode(errors="ignore").strip().splitlines()
    try:
        step = json.loads(tail[-1])["opt_step"]
    except (IndexError, ValueError, KeyError):
        return None
    if step != prog.get("step"):
        prog.update(step=step, since=now)
    elif now - prog["since"] > STEP_STALL_S:
        return f"training stalled (no optimizer step for {now - prog['since']:.0f} s at step {step})"
    return None


def log_guard(rec):
    with open(GUARD_LOG, "a") as f:
        f.write(json.dumps({"t": round(time.time(), 3), **rec}) + "\n")


def run_guarded(args, logf, rid, stage, hang_s=None):
    p = subprocess.Popen(args, stdout=logf, stderr=subprocess.STDOUT)
    log_guard({"run": rid, "stage": stage, "action": "child started", "child_pid": p.pid})
    hazard, ac_bad, s, lid, prog = None, 0, {}, None, {}
    t_start = time.time()
    w0, u0, last_slow = time.time(), time.clock_gettime(time.CLOCK_UPTIME_RAW), 0.0
    try:
        while p.poll() is None:
            time.sleep(POLL_S)
            w1, u1 = time.time(), time.clock_gettime(time.CLOCK_UPTIME_RAW)
            slept = (w1 - w0) - (u1 - u0)
            w0, u0 = w1, u1
            full = w1 - last_slow >= SLOW_POLL_S
            s = env_state(full=full)
            if full:
                last_slow = w1
                if s.get("lid_open") is not None and s["lid_open"] != lid:
                    if lid is not None or s["lid_open"] is False:
                        log_guard({"run": rid, "stage": stage, "event": f"lid {'opened' if s['lid_open'] else 'closed'} (logged only, not a stop condition)", "state": s})
                    lid = s["lid_open"]
            ac_bad = ac_bad + 1 if s["ac"] is False else 0
            health = run_health(rid, w1, prog) if stage == "train" else None
            if slept > SLEEP_GAP_S:
                hazard = f"system sleep detected ({slept:.0f} s suspended)"
            elif ac_bad >= AC_GRACE_POLLS:
                hazard = "charger disconnected"
            elif health:
                hazard = health
            elif full and s.get("thermal_ok") is False:
                hazard = "thermal or performance warning recorded"
            elif s["pressure"] >= 4:
                hazard = "memory pressure critical"
            elif hang_s and w1 - t_start > hang_s:
                hazard = f"{stage} process above its {hang_s} s watchdog"
            if hazard:
                interrupt(p, rid, stage, hazard, s)
                break
    except (KeyboardInterrupt, sigsafe.Terminated) as ex:
        hazard = f"sequence process received {'SIGINT' if isinstance(ex, KeyboardInterrupt) else 'SIGTERM'} (manual stop)"
        interrupt(p, rid, stage, hazard, s)
    if not hazard:
        log_guard({"run": rid, "stage": stage, "action": "child exited", "child_pid": p.pid, "returncode": p.returncode, "seconds": round(time.time() - t_start, 1)})
    return p.returncode, hazard, time.time() - t_start


def interrupt(p, rid, stage, hazard, s):
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    log_guard({"run": rid, "stage": stage, "hazard": hazard, "state": s, "action": "SIGINT", "child_pid": p.pid})
    p.send_signal(signal.SIGINT)
    try:
        p.wait(KILL_WAIT_S)
    except subprocess.TimeoutExpired:
        p.kill()
        p.wait()
        log_guard({"run": rid, "stage": stage, "action": "SIGKILL after no exit in 180 s", "child_pid": p.pid})
    log_guard({"run": rid, "stage": stage, "action": "child exited after interrupt", "child_pid": p.pid, "returncode": p.returncode})


def stop(msg, done, rid=None):
    with open(INTERRUPTIONS, "a") as f:
        f.write(json.dumps({"t": round(time.time(), 3), "run": rid, "cause": msg, "completed_before": len(done)}) + "\n")
    print(f"[PHASE 3 SEQUENCE STOPPED] {msg}", flush=True)
    C.write_json_atomic(STATUS, {"state": "stopped", "reason": msg, "run": rid, "completed": done, "time": time.time()})
    sys.exit(1)


def peak_of(path: Path, key=("memory", "kernel_lifetime_max_footprint_mb")):
    j = json.load(open(path))
    for k in key:
        j = j[k]
    return float(j)


def check_memory(rid, label, mb, done):
    if mb > C.STOP_RULE_MB:
        stop(f"{rid}: {label} peak footprint {mb:.0f} MB exceeds the 10.5 GB stop rule ({C.STOP_RULE_MB:.0f} MB); evidence in runs/{rid}", done, rid)


def scores_frozen_ok():
    if not (C.SCORES_FILE.exists() and C.SCORES_HASH_FILE.exists()):
        return False, "Stage B scores are not frozen"
    if C.sha256_file(C.SCORES_FILE) != C.SCORES_HASH_FILE.read_text().split()[0]:
        return False, "Stage B score file hash mismatch"
    t_frozen = json.load(open(C.SCORES_FILE))["frozen_at"]
    singles = [p for p in C.RUNS.glob("p3_L*")] if C.RUNS.exists() else []
    early = [p.name for p in singles if p.stat().st_birthtime < t_frozen]
    if early:
        return False, f"single-block runs exist from before the score freeze: {early}"
    return True, "ok"


def run_one(e, i, n, done, timing):
    rid = e["run_id"]
    if (C.RUNS / rid).exists():
        stop(f"{rid}: destination already exists; never overwritten", done)
    checks, info = preflight()
    log_guard({"run": rid, "stage": "preflight", "checks": checks, **info})
    if not all(checks.values()):
        stop(f"preflight failed before {rid}: {[k for k, v in checks.items() if not v]} {info}", done, rid)
    C.write_json_atomic(STATUS, {"state": "running", "current": rid, "index": i, "of": n, "completed": done, "time": time.time()})
    print(f"[phase3] {i}/{n} {rid} est train {e['est_seconds'] / 60:.1f} min", flush=True)
    d = C.RUNS / rid
    s = C.split()
    t_run = time.time()
    with open(C.LOGS / f"{rid}.log", "w") as lf:
        rc, hz, t_tr = run_guarded([PY, "-B", str(C.CODE / "run_train.py"), rid], lf, rid, "train")
        if (d / "abort.json").exists():
            stop(f"{rid}: training process hit the 11.0 GB early abort; see runs/{rid}/abort.json", done, rid)
        if hz:
            stop(f"{rid}: safety guard stopped the run ({hz}); see runs/{rid}/incident.json", done, rid)
        if rc:
            stop(f"{rid}: training failed (rc {rc}); see runs/{rid}/incident.json", done, rid)
        check_memory(rid, "training process", peak_of(d / "result.json"), done)
        rc, hz, t_rl = run_guarded([PY, "-B", str(C.CODE / "reload_check.py"), rid], lf, rid, "reload", RELOAD_HANG_S)
        if hz or rc:
            stop(f"{rid}: reload verification {'interrupted: ' + hz if hz else 'failed'}", done, rid)
        check_memory(rid, "reload process", float(json.load(open(d / "reload_check.json"))["peak_mb"]), done)
        tiles, t_ev = {}, []
        for tile in s["validation"]:
            tid = tile.split("_")[2] + "_" + tile.split("_")[3]
            rc, hz, te = run_guarded([PY, "-B", str(C.CODE / "eval_tile.py"), rid, tile], lf, rid, f"eval {tid}", EVAL_HANG_S)
            if (d / "eval" / "abort.json").exists():
                stop(f"{rid}: evaluation of {tile} hit the 11.0 GB early abort", done, rid)
            if hz or rc:
                stop(f"{rid}: evaluation of {tile} {'interrupted: ' + hz if hz else 'failed'}", done, rid)
            tj = d / "eval" / f"{tid}.json"
            check_memory(rid, f"evaluation process {tid}", peak_of(tj), done)
            tiles[tile] = json.load(open(tj))
            t_ev.append(te)
    acc = ConfusionMatrixAccumulator()
    for t in tiles.values():
        acc.matrix += np.array(t["confusion_matrix"], dtype=np.int64)
    m = acc.compute()
    res = json.load(open(d / "result.json"))
    summ = {"run_id": rid, "entry": e, "step": 2000, "pooled": m, "val_ce": sum(t["ce_sum"] for t in tiles.values()) / sum(t["pixels"] for t in tiles.values()),
            "tiles": {k: {"confusion_matrix": v["confusion_matrix"], "ce_sum": v["ce_sum"], "pixels": v["pixels"], "checkpoint_sha256": v["checkpoint_sha256"]} for k, v in tiles.items()},
            "checkpoint_sha256": res["checkpoint"]["sha256"], "all_tiles_same_checkpoint": all(v["checkpoint_sha256"] == res["checkpoint"]["sha256"] for v in tiles.values()),
            "reload": json.load(open(d / "reload_check.json")),
            "timing": {"training_seconds": res["timing"]["training_seconds"], "train_process_wall": t_tr, "reload_wall": t_rl, "eval_walls": t_ev,
                       "eval_seconds_inner": [v["timing"]["eval_s"] for v in tiles.values()], "run_wall": time.time() - t_run},
            "memory_peaks_mb": {"train": peak_of(d / "result.json"), "reload": float(json.load(open(d / "reload_check.json"))["peak_mb"]),
                                **{k: peak_of(d / "eval" / f"{k.split('_')[2]}_{k.split('_')[3]}.json") for k in tiles}}}
    if not summ["all_tiles_same_checkpoint"]:
        stop(f"{rid}: tiles evaluated different checkpoints", done, rid)
    C.write_json_atomic(d / "summary.json", summ)
    done.append(rid)
    print(f"[done] {rid} mIoU={m['mean_iou']:.4f} train={res['timing']['training_seconds']:.0f}s run_wall={summ['timing']['run_wall']:.0f}s "
          f"peaks train={summ['memory_peaks_mb']['train']:.0f} max_eval={max(list(summ['memory_peaks_mb'].values())[2:]):.0f} MB", flush=True)
    return summ


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    C.LOGS.mkdir(parents=True, exist_ok=True)
    C.RUNS.mkdir(parents=True, exist_ok=True)
    if mode == "--check":
        checks, info = preflight()
        print(json.dumps({"checks": checks, **info}, indent=1))
        print("PREFLIGHT", "PASS" if all(checks.values()) else "FAIL")
        return
    if mode not in ("k0", "single", "scores", "canary"):
        raise SystemExit("usage: run_sequence.py k0|scores|canary|single|--check")
    sigsafe.restore()
    m = json.load(open(C.MANIFEST))
    if C.code_hash() != m["code_hash"]:
        raise SystemExit("Phase 3 code differs from the manifest")
    log_guard({"stage": f"sequence start ({mode})", "signals": sigsafe.report()})
    done = []
    try:
        if mode == "scores":
            run_scores(done)
            return
        runs = [e for e in m["runs"] if (e["K"] == 0) == (mode == "k0")]
        if mode in ("single", "canary"):
            ok, why = scores_frozen_ok()
            if not ok:
                stop(f"single-block runs refused: {why}", done)
            if runs[0]["run_id"] != C.CANARY:
                stop(f"the first single-block run must be the early-block canary {C.CANARY}", done)
        if mode == "canary":
            runs = runs[:1]
            base = swap_stability()
            if not base["launch_ok"]:
                stop(f"canary not launched: system not ready ({base['reason']})", done)
        if mode == "single":
            rep = C.ART / "canary_report.json"
            if not (rep.exists() and json.load(open(rep)).get("run") == C.CANARY and json.load(open(rep)).get("passed")):
                stop("single-block sequence refused: no passed canary report for the restarted canary", done)
            runs = runs[1:]
            # resume (manifest v4): completed runs are skipped and never touched; a partial
            # folder that is not a recorded interrupted run stops the sequence
            interrupted = set(m.get("interrupted_runs", {}))
            completed = [e["run_id"] for e in runs if (C.RUNS / e["run_id"] / "summary.json").exists()]
            partial = [e["run_id"] for e in runs if (C.RUNS / e["run_id"]).exists() and e["run_id"] not in completed and e["run_id"] not in interrupted]
            if partial:
                stop(f"partial run folders exist; refusing to resume: {partial}", done)
            log_guard({"stage": "resume", "skipping_completed": completed})
            print(f"[resume] skipping {len(completed)} completed runs", flush=True)
            runs = [e for e in runs if e["run_id"] not in completed]
        for i, e in enumerate(runs, 1):
            summ = run_one(e, i, len(runs), done, None)
            if e["run_id"] == "p3_K0_s1000" and summ["pooled"]["mean_iou"] < K0_FLOOR:
                stop(f"K0 seed 1000 mIoU {summ['pooled']['mean_iou']:.4f} below the {K0_FLOOR} pipeline floor (protocol v2 section 8): stop and review", done, e["run_id"])
            if e["run_id"] == C.CANARY:
                C.write_json_atomic(C.ART / "canary_report.json", {"run": e["run_id"], "memory_peaks_mb": summ["memory_peaks_mb"], "stop_rule_mb": C.STOP_RULE_MB,
                                                                   "passed": True, "timing": summ["timing"], "time": time.time()})
                print("[canary] passed: all process peaks below 10.5 GB", flush=True)
    except (KeyboardInterrupt, sigsafe.Terminated) as ex:
        stop(f"sequence process received {'SIGINT' if isinstance(ex, KeyboardInterrupt) else 'SIGTERM'} between runs (manual stop)", done)
    C.write_json_atomic(STATUS, {"state": f"complete_{mode}", "completed": done, "time": time.time()})
    print(f"[PHASE 3 {mode.upper()} COMPLETE] {len(done)} runs.", flush=True)


def swap_stability(seconds=60, dt=5):
    """Baseline for the canary restart: memory pressure normal at every sample and swap not
    increasing (last sample <= first + 8 MB, maximum rise <= 32 MB)."""
    samples = []
    for _ in range(seconds // dt + 1):
        samples.append({"t": round(time.time(), 1), "swap_used_mb": round(C.swap_used_mb(), 1), "pressure": C.pressure_level()})
        time.sleep(dt)
    sw = [x["swap_used_mb"] for x in samples]
    reasons = []
    if any(x["pressure"] != 1 for x in samples):
        reasons.append("memory pressure not normal")
    if sw[-1] > sw[0] + 8 or max(sw) > sw[0] + 32:
        reasons.append(f"swap increasing ({sw[0]:.0f} -> {sw[-1]:.0f} MB, max {max(sw):.0f})")
    rec = {"samples": samples, "baseline_swap_used_mb": sw[0], "launch_ok": not reasons, "reason": "; ".join(reasons) or "ok"}
    C.write_json_atomic(C.ART / "canary_r1_launch_baseline.json", rec)
    log_guard({"stage": "canary launch check", **{k: v for k, v in rec.items() if k != "samples"}})
    return rec


def run_scores(done):
    """Stage B scoring children, under the same guard. Each writes one JSON; then freeze."""
    for name, args in (("labelfree", []), ("logme", []), ("fisher", []), ("freeze", [])):
        checks, info = preflight()
        log_guard({"run": f"stage_b_{name}", "stage": "preflight", "checks": checks, **info})
        if not all(checks.values()):
            stop(f"preflight failed before Stage B {name}: {[k for k, v in checks.items() if not v]}", done)
        with open(C.LOGS / f"stage_b_{name}.log", "w") as lf:
            rc, hz, t = run_guarded([PY, "-B", str(C.CODE / "stage_b_scores.py"), name] + args, lf, f"stage_b_{name}", "score", SCORE_HANG_S)
        ab = C.ART / "stage_b" / "abort.json"
        if ab.exists():
            stop(f"Stage B {name} hit the 11.0 GB early abort", done)
        if hz or rc:
            stop(f"Stage B {name} {'interrupted: ' + hz if hz else 'failed'}; see logs/stage_b_{name}.log", done)
        pk = C.ART / "stage_b" / f"{name}.json"
        if pk.exists():
            mb = float(json.load(open(pk))["peak_mb"])
            if mb > C.STOP_RULE_MB:
                stop(f"Stage B {name} peak footprint {mb:.0f} MB exceeds the 10.5 GB stop rule", done)
        done.append(name)
        print(f"[stage B] {name} done in {t:.0f}s", flush=True)
    C.write_json_atomic(STATUS, {"state": "complete_scores", "completed": done, "time": time.time()})


if __name__ == "__main__":
    main()
