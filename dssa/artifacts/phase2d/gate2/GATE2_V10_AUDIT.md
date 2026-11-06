# Gate 2 recovery v10: manifest and audit (awaiting research-lead approval)

Date: 2026-11-04. Prepared and audited only. **No training has started.**

## Manifest
- `manifest_gate2_recovery_v10.json`, SHA-256
  **`006394f7b27b57089cc42e29c8aa91d91650c3147a5551f74712a28f6401da96`**
- 29 runs, estimated **14.8 h**. Code hash: 51 files, matching the current code.
- An earlier v10 draft that still stopped on a closed lid (`e954ce72…`) was never approved or
  launched. It is kept as `manifest_gate2_recovery_v10__superseded_lid_stop.json`, with its audit
  and tests under `__superseded_lid_stop` names.

| # | Seed | Layers | Run IDs |
|---|---|---|---|
| 1 | 2000 | 15 | `p2d_oracle_L15_s2000_a2` (rerun_of `p2d_oracle_L15_s2000`) |
| 2–8 | 2000 | 16–22 | `p2d_oracle_L16_s2000` … `p2d_oracle_L22_s2000` |
| 9–29 | 3000 | 1–11, 13–22 | `p2d_oracle_L01_s3000` … `p2d_oracle_L22_s3000` |

| Status | Count |
|---|---|
| Completed, kept, not rerun | 34 (s1000: 21; s2000: Layers 1–11, 13, 14) |
| Failed, partial folders preserved | 6 (L02/L06/L07 s1000; L02/L04/L15 s2000) |
| In v10 (pending) | 29 (1 rerun + 28 never started) |

34 + 29 = 63, and together they cover the Gate 2 grid exactly once. The order equals v9's with
completed runs removed. No training field differs from v9. All 29 config hashes are valid.

## Lid behaviour (research lead's instruction of 2026-11-04)
Evidence from the macOS power log and preserved telemetry:
- **On AC with the sequence's caffeinate**, a lid close puts the Mac into *DarkWake*, not sleep:
  - 12:47:01 "Entering DarkWake state due to 'Clamshell Sleep' … Using AC"
  - 19:20:15 the same, followed at 19:20:45 by "DarkWake to FullWake"
  - In the 2 s between the 19:20:15 lid close and the guard's stop, training continued at its
    normal rate: steps 1,285 → 1,289, one step per 0.5 s, with telemetry every 0.25 s.
- **On battery**, a lid close is real sleep: 2026-11-03 12:18, 19:41, 21:31; 2026-11-04 10:22; and
  2026-11-04 12:47:06, when the charger was also disconnected.
- The power settings show no "sleep disabled" option and no keep-awake app. Staying awake with
  the lid closed depends on AC power plus the sequence's `caffeinate -dims`.
- **Not yet verified:** sustained training (minutes to hours) with the lid closed. The longest
  observed span is 2 s. The new health checks below are what protect a long lid-closed period.

## Code changes since v9
Only `run_gate2_v10.py` differs in behaviour. `run_one_v10.py` (manifest path) and
`gate2_analysis_v10.py` (adds mapping (15, 2000) → `_a2`) are name-only. `gate_v10.py` is the
manifest writer. `sigsafe.py`, `run_one_v2.py`, `verify_reload.py` and `verify_reload_v8.py` are
unchanged from the audited v8 hashes.

`run_gate2_v10.py` versus `run_gate2_v9.py`:
1. **Preflight:** `lid_open` removed from the pass/fail checks; recorded as `lid_open_advisory`.
2. **Guard:** `lid closed` is no longer a hazard. Lid transitions are logged as events
   ("lid closed (logged only, not a stop condition)").
3. **New run-health stops** (training stage only; read from the run's own `telemetry.jsonl`):
   - **training process unresponsive:** telemetry not updated for **60 s**. Healthy maximum
     across 42 completed runs is 0.49 s, excluding the run that contained the INCIDENT_003 sleep.
   - **training stalled:** no optimizer step for **300 s**. Healthy maximum is 77 s, during validation.
4. **Unchanged:**
   - system sleep (30 s wall-clock gap)
   - charger disconnected (2 polls)
   - thermal or performance warning
   - critical memory pressure
   - the runner's own limits (footprint 11,776 MB, **swap growth 512 MB**, runtime 1.5×)
   - signal handling, manual stop, interruption log, no retry or skip

The manifest's `safety_additions` record these: no "lid open" preflight, guard `lid_closed: false`,
`training_telemetry_stale_s: 60`, `training_no_optimizer_step_s: 300`.

## Dummy tests of the v10 files (production `nohup caffeinate … &` path)
Evidence is in `gate2/v10_signal_and_health_tests/`. The run executes the real `run_one_v10.py`
and `run_one_v2.main`, with a model-free training loop.

| Test | Expected | Result |
|---|---|---|
| lid_advisory: lid reported closed for 45 s | no stop | Lid event logged; the run kept training (766 steps). It ended only by the manual stop afterwards: KeyboardInterrupt, incident written |
| guard_charger | stop | SIGINT, exit −2 after 0.18 s, incident (step 20), sequence stopped |
| manual_child_sigint (documented command) | stop | exit −2, incident (step 18), sequence stopped |
| guard_sleep (100 s gap) | stop | exit −2, incident (step 3), sequence stopped |
| guard_thermal | stop | exit −2, incident (step 3), sequence stopped |
| step_stall (process alive, no optimizer step) | stop at 300 s | "training stalled (no optimizer step for 300 s at step 5)"; exit −2, incident written |
| telemetry_stale (training process frozen with SIGSTOP) | stop at 60 s | "training process unresponsive (61 s)"; a frozen process cannot handle SIGINT, so SIGKILL after 180 s (exit −9); no incident; cause logged |

- In every stop case the next run did not start.
- No test process remained, and no project file changed.

## Real-training interruption evidence (both checked from preserved logs)
| Run | PID (run = guard) | Signals | Hazard | Exit | SIGINT→exit | incident.json |
|---|---|---|---|---|---|---|
| L04 s2000 (v8) | 13214 = 13214 | caught/caught | lid closed | −2 | 0.429 s, no SIGKILL | KeyboardInterrupt, train, step 850, all 15 fields |
| L15 s2000 (v9) | 32541 = 32541 | caught/caught | lid closed | −2 | 0.441 s, no SIGKILL | KeyboardInterrupt, train, step 1,289, all 15 fields |

Both sequences stopped, both logged `incident_written: true`, and neither started another run.

## Integrity
- Manifests v1–v9 unchanged.
- The 34 completed runs and the 12 pilot runs pass the result-hash, checkpoint-hash and reload checks.
- All six partial folders match their recorded hashes. INCIDENT_003 to 008 are recorded.
- Frozen artifacts unchanged; data-stream replay matches for all seeds.
- **Locked test set:** 51 result and incident records list only approved tiles; 0 of 8 locked
  test tiles opened.
- Preflight PASS (after the tests ended). No training process. No system settings changed.
  Nothing committed or pushed.

## Remaining operational risks
1. **Long lid-closed periods are not yet observed on real training.**
   - If the Mac does sleep, the 30 s sleep check stops the run on the next wake.
   - If GPU work stops or freezes in DarkWake, the 60 s and 300 s health checks stop it.
   - A frozen process cannot write `incident.json`; it is killed after 180 s and the cause is logged.
2. **Heat:** lid-closed operation may run warmer. The thermal guard is unchanged.
3. **Charger:** a closed lid on battery is real sleep. Unplugging still stops the run.
4. **Docker or other memory use** can still trip the 512 MB swap limit.
5. **No `incident.json` in two edge cases:** a stop in the first second of a run, or during
   reload verification. The logs record the cause.

## Launch command (only after approval)
```
cd "/Users/siva/Documents/Major project/dssa/phase2d"
nohup caffeinate -dims ../venv/bin/python -B run_gate2_v10.py > ../artifacts/phase2d/logs/gate2_v10.log 2>&1 &
```
Manual stop: `kill -INT <sequence pid>` (send once).
