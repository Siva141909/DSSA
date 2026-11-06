"""Gate 2 recovery runner for manifest v11: the audited v10 runner, unchanged except for
manifest, file names and run count (INCIDENT_009). v10 description follows: the audited v8 runner with one change, per the
research lead (2026-11-04): a closed lid is no longer a stop condition, because with
AC power and caffeinate the Mac stays in DarkWake rather than sleeping. A closed lid
is logged (preflight and guard). Real sleep is still caught by the wall-clock check,
and two run-health stops are added for the training process: telemetry not updated
for TELEMETRY_STALE_S, or no optimizer step for STEP_STALL_S (healthy runs: at most
0.49 s and 77 s). Signal handling repaired in v8 (INCIDENT_006). SIGINT/SIGTERM handlers are restored in this process and in every
child (sigsafe), so the guard's SIGINT and the manual stop reach the run, which
writes incident.json. A SIGINT/SIGTERM to this process is forwarded to the active
run, and the sequence stops. The virtual-machine check stays advisory. The training runner is unchanged
(run_one_v2 via run_one_v5). Added around it, in this parent process only:
  preflight  before every run: AC power, no thermal warning, normal memory
             pressure, free disk, no cloud-only files. Lid state and whether a
             virtual machine (Docker) is running are logged, not checked. A
             failure stops the sequence before the run folder is created.
  guard      during every run and reload: system sleep (wall clock against
             CLOCK_UPTIME_RAW), charger disconnected, thermal warning, critical
             memory pressure; during training also run health (telemetry and
             optimizer-step progress). Lid changes are logged only. A hazard
             sends SIGINT to the child, which writes incident.json, and the
             sequence stops.
No retry. Any failure stops the whole sequence. `--check` prints the preflight
and exits without training."""
from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
import sigsafe  # noqa: E402

C.install_guards()
MANIFEST = C.ART / "manifest_gate2_recovery_v11.json"
STATUS = C.ART / "gate2_status_v11.json"
GUARD_LOG = C.ART / "logs" / "gate2_guard_v11.jsonl"
INTERRUPTIONS = C.ART / "logs" / "gate2_interruptions_v11.jsonl"
SLEEP_GAP_S, POLL_S, SLOW_POLL_S, AC_GRACE_POLLS, KILL_WAIT_S = 30, 5, 15, 2, 180
TELEMETRY_STALE_S, STEP_STALL_S = 60, 300
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
    sp = json.load(open(C.ROOT / "artifacts" / "splits" / "vaihingen_target_split_manifest.json"))["partitions"]
    fs = [C.ROOT / "data" / "vaihingen_irrg" / n for n in sp["target_train"] + sp["target_validation"]]
    fs += [C.ROOT / "data" / "Vaihingen" / "ISPRS_semantic_labeling_Vaihingen_ground_truth_COMPLETE.zip", C.ROOT / "checkpoint" / "Prithvi_EO_V2_300M.pt", C.ROOT / "checkpoint" / "prithvi_mae.py"]
    for d in (C.CODE, C.ROOT / "train", C.ROOT / "sanity", C.ROOT / "config"):
        fs += [p for p in d.iterdir() if p.is_file()]
    return fs


def preflight():
    s = env_state()
    free_gb = shutil.disk_usage(C.ROOT).free / 1e9
    dataless = [str(p) for p in required_files() if not p.exists() or os.lstat(p).st_flags & SF_DATALESS]
    checks = {"charger_connected": s["ac"] is True, "no_thermal_warning": s["thermal_ok"] is True,
              "memory_pressure_normal": s["pressure"] == 1, "free_disk_ge_10gb": free_gb >= 10, "required_files_local": not dataless,
              "no_other_phase2d_run": not _cmd(["pgrep", "-f", "run_one_v"]).strip()}
    vm = bool(_cmd(["pgrep", "-f", "Virtualization.VirtualMachine|com.docker.virtualization"]).strip())
    return checks, {"state": s, "free_gb": round(free_gb, 1), "missing_or_cloud_only": dataless[:10], "virtual_machine_running_advisory": vm,
                    "lid_open_advisory": s["lid_open"]}


def run_health(rid, now, prog):
    """Training-process health from its own telemetry (written every 0.25 s by
    run_one_v2). Returns a hazard string or None. `prog` tracks step progress."""
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


def run_guarded(args, logf, rid, stage):
    """Runs one child. Returns (returncode, hazard or None)."""
    p = subprocess.Popen(args, stdout=logf, stderr=subprocess.STDOUT)
    log_guard({"run": rid, "stage": stage, "action": "child started", "child_pid": p.pid})
    hazard, ac_bad, s, lid, prog = None, 0, {}, None, {}
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
            if hazard:
                interrupt(p, rid, stage, hazard, s)
                break
    except (KeyboardInterrupt, sigsafe.Terminated) as ex:
        hazard = f"sequence process received {'SIGINT' if isinstance(ex, KeyboardInterrupt) else 'SIGTERM'} (manual stop)"
        interrupt(p, rid, stage, hazard, s)
    if not hazard:
        log_guard({"run": rid, "stage": stage, "action": "child exited", "child_pid": p.pid, "returncode": p.returncode})
    return p.returncode, hazard


def interrupt(p, rid, stage, hazard, s):
    """SIGINT to the run, then wait for it to write incident.json and exit. Further
    SIGINT/SIGTERM to this process are ignored meanwhile; no child starts after this."""
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
    log_guard({"run": rid, "stage": stage, "action": "child exited after interrupt", "child_pid": p.pid, "returncode": p.returncode,
               "incident_written": (C.RUNS / rid / "incident.json").exists()})


def stop(msg, done, rid=None):
    inc = C.RUNS / rid / "incident.json" if rid else None
    i = json.load(open(inc)) if inc and inc.exists() else {}
    with open(INTERRUPTIONS, "a") as f:
        f.write(json.dumps({"t": round(time.time(), 3), "run": rid, "cause": msg, "error": i.get("error"), "stage": i.get("stage"),
                            "optimizer_steps_completed": i.get("optimizer_steps_completed"), "incident_written": bool(i), "completed_before": len(done)}) + "\n")
    print(f"[GATE 2 RECOVERY STOPPED] {msg}", flush=True)
    C.write_json_atomic(STATUS, {"state": "stopped", "reason": msg, "completed": done, "time": time.time()})
    sys.exit(1)


def main():
    if sys.argv[1:] == ["--check"]:
        checks, info = preflight()
        print(json.dumps({"checks": checks, **info}, indent=1))
        print("PREFLIGHT", "PASS" if all(checks.values()) else "FAIL")
        return
    sigsafe.restore()
    log_guard({"stage": "sequence start", "signals": sigsafe.report()})
    m = json.load(open(MANIFEST))
    n = len(m["runs"])
    assert n == 24
    done = []
    try:
        run_all(m, n, done)
    except (KeyboardInterrupt, sigsafe.Terminated) as ex:
        stop(f"sequence process received {'SIGINT' if isinstance(ex, KeyboardInterrupt) else 'SIGTERM'} between runs (manual stop)", done)
    C.write_json_atomic(STATUS, {"state": f"complete_{n}_of_{n}", "completed": done, "time": time.time()})
    print(f"[GATE 2 RECOVERY COMPLETE] {n} of {n}. Authorization ends here.", flush=True)


def run_all(m, n, done):
    for i, e in enumerate(m["runs"], 1):
        rid = e["run_id"]
        if (C.RUNS / rid).exists():
            stop(f"{rid}: destination already exists; never overwritten", done)
        checks, info = preflight()
        log_guard({"run": rid, "stage": "preflight", "checks": checks, **info})
        if not all(checks.values()):
            stop(f"preflight failed before {rid}: {[k for k, v in checks.items() if not v]} {info}", done, rid)
        C.write_json_atomic(STATUS, {"state": "running", "current": rid, "index": i, "completed": done, "time": time.time()})
        print(f"[gate2-v11] {i}/{n} {rid} est {e['est_seconds']/60:.1f} min", flush=True)
        with open(C.ART / "logs" / f"{rid}.log", "w") as lf:
            rc, hz = run_guarded([sys.executable, "-B", str(C.CODE / "run_one_v11.py"), rid], lf, rid, "train")
            if hz:
                stop(f"{rid}: safety guard stopped the run ({hz}); see runs/{rid}/incident.json and logs/gate2_guard_v11.jsonl", done, rid)
            if rc:
                stop(f"{rid}: run failed; see runs/{rid}/incident.json", done, rid)
            rc, hz = run_guarded([sys.executable, "-B", str(C.CODE / "verify_reload_v8.py"), rid], lf, rid, "reload")
            if hz or rc:
                stop(f"{rid}: reload verification {'interrupted by guard: ' + hz if hz else 'failed'}", done, rid)
        try:
            C.assert_frozen_unchanged()
        except RuntimeError as ex:
            stop(str(ex), done, rid)
        done.append(rid)
        print(open(C.ART / "logs" / f"{rid}.log").read().split("[done]")[-1].split("\n")[0], flush=True)


if __name__ == "__main__":
    main()
