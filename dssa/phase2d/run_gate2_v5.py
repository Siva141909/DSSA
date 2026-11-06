"""Gate 2 recovery runner for manifest v5. The training runner is unchanged
(run_one_v2 via run_one_v5). Added around it, in this parent process only:
  preflight  before every run: AC power, lid open, no thermal warning, normal
             memory pressure, free disk, no cloud-only files. A failure stops
             the sequence before the run folder is created.
  guard      during every run and reload: system sleep (wall clock against
             CLOCK_UPTIME_RAW), charger disconnected, lid closed, thermal
             warning, critical memory pressure. A hazard sends SIGINT to the
             child, which writes incident.json, and the sequence stops.
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

C.install_guards()
MANIFEST = C.ART / "manifest_gate2_recovery_v5.json"
STATUS = C.ART / "gate2_status_v5.json"
GUARD_LOG = C.ART / "logs" / "gate2_guard_v5.jsonl"
SLEEP_GAP_S, POLL_S, SLOW_POLL_S, AC_GRACE_POLLS, KILL_WAIT_S = 30, 5, 15, 2, 180
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
    checks = {"charger_connected": s["ac"] is True, "lid_open": s["lid_open"] is True, "no_thermal_warning": s["thermal_ok"] is True,
              "memory_pressure_normal": s["pressure"] == 1, "free_disk_ge_10gb": free_gb >= 10, "required_files_local": not dataless,
              "no_other_phase2d_run": not _cmd(["pgrep", "-f", "run_one_v"]).strip()}
    return checks, {"state": s, "free_gb": round(free_gb, 1), "missing_or_cloud_only": dataless[:10]}


def log_guard(rec):
    with open(GUARD_LOG, "a") as f:
        f.write(json.dumps({"t": round(time.time(), 3), **rec}) + "\n")


def run_guarded(args, logf, rid, stage):
    """Runs one child. Returns (returncode, hazard or None)."""
    p = subprocess.Popen(args, stdout=logf, stderr=subprocess.STDOUT)
    hazard, ac_bad = None, 0
    w0, u0, last_slow = time.time(), time.clock_gettime(time.CLOCK_UPTIME_RAW), 0.0
    while p.poll() is None:
        time.sleep(POLL_S)
        w1, u1 = time.time(), time.clock_gettime(time.CLOCK_UPTIME_RAW)
        slept = (w1 - w0) - (u1 - u0)
        w0, u0 = w1, u1
        full = w1 - last_slow >= SLOW_POLL_S
        s = env_state(full=full)
        if full:
            last_slow = w1
        ac_bad = ac_bad + 1 if s["ac"] is False else 0
        if slept > SLEEP_GAP_S:
            hazard = f"system sleep detected ({slept:.0f} s suspended)"
        elif ac_bad >= AC_GRACE_POLLS:
            hazard = "charger disconnected"
        elif full and s.get("lid_open") is False:
            hazard = "lid closed"
        elif full and s.get("thermal_ok") is False:
            hazard = "thermal or performance warning recorded"
        elif s["pressure"] >= 4:
            hazard = "memory pressure critical"
        if hazard:
            log_guard({"run": rid, "stage": stage, "hazard": hazard, "state": s, "action": "SIGINT"})
            p.send_signal(signal.SIGINT)
            try:
                p.wait(KILL_WAIT_S)
            except subprocess.TimeoutExpired:
                p.kill()
                p.wait()
                log_guard({"run": rid, "stage": stage, "action": "SIGKILL after no exit in 180 s"})
            break
    return p.returncode, hazard


def stop(msg, done):
    print(f"[GATE 2 RECOVERY STOPPED] {msg}", flush=True)
    C.write_json_atomic(STATUS, {"state": "stopped", "reason": msg, "completed": done, "time": time.time()})
    sys.exit(1)


def main():
    if sys.argv[1:] == ["--check"]:
        checks, info = preflight()
        print(json.dumps({"checks": checks, **info}, indent=1))
        print("PREFLIGHT", "PASS" if all(checks.values()) else "FAIL")
        return
    m = json.load(open(MANIFEST))
    n = len(m["runs"])
    assert n == 62
    done = []
    for i, e in enumerate(m["runs"], 1):
        rid = e["run_id"]
        if (C.RUNS / rid).exists():
            stop(f"{rid}: destination already exists; never overwritten", done)
        checks, info = preflight()
        log_guard({"run": rid, "stage": "preflight", "checks": checks, **info})
        if not all(checks.values()):
            stop(f"preflight failed before {rid}: {[k for k, v in checks.items() if not v]} {info}", done)
        C.write_json_atomic(STATUS, {"state": "running", "current": rid, "index": i, "completed": done, "time": time.time()})
        print(f"[gate2-v5] {i}/{n} {rid} est {e['est_seconds']/60:.1f} min", flush=True)
        with open(C.ART / "logs" / f"{rid}.log", "w") as lf:
            rc, hz = run_guarded([sys.executable, "-B", str(C.CODE / "run_one_v5.py"), rid], lf, rid, "train")
            if hz:
                stop(f"{rid}: safety guard stopped the run ({hz}); see runs/{rid}/incident.json and logs/gate2_guard_v5.jsonl", done)
            if rc:
                stop(f"{rid}: run failed; see runs/{rid}/incident.json", done)
            rc, hz = run_guarded([sys.executable, "-B", str(C.CODE / "verify_reload.py"), rid], lf, rid, "reload")
            if hz or rc:
                stop(f"{rid}: reload verification {'interrupted by guard: ' + hz if hz else 'failed'}", done)
        try:
            C.assert_frozen_unchanged()
        except RuntimeError as ex:
            stop(str(ex), done)
        done.append(rid)
        print(open(C.ART / "logs" / f"{rid}.log").read().split("[done]")[-1].split("\n")[0], flush=True)
    C.write_json_atomic(STATUS, {"state": f"complete_{n}_of_{n}", "completed": done, "time": time.time()})
    print(f"[GATE 2 RECOVERY COMPLETE] {n} of {n}. Authorization ends here.", flush=True)


if __name__ == "__main__":
    main()
