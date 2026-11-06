# Gate 2 recovery v8: signal repair, dummy tests, manifest and audit

Date: 2026-11-04. Prepared and audited only. **No training has started.**

## 1. Root cause (INCIDENT_006)
- The sequence was launched with `nohup … &` from a non-interactive shell. POSIX shells
  start background jobs with SIGINT set to *ignored*; the setting is inherited across fork and exec.
- Python only installs its KeyboardInterrupt handler when SIGINT is not ignored, so every
  run process ignored SIGINT. The guard's SIGINT and the manual stop had no effect; only the
  180 s SIGKILL fallback worked, and it writes no `incident.json`.
- Reproduced with a kernel-level `sigaction` probe (`v8_signal_tests/sigprobe.py`):
  - under `nohup … &`: SIGINT **ignored**, SIGTERM default
  - in a foreground process: SIGINT caught
  - after `sigsafe.restore()`: both caught

## 2. Changed and new files (all new; no existing file modified)
| File | What it does |
|---|---|
| `phase2d/sigsafe.py` (new) | `restore()`: SIGINT raises KeyboardInterrupt; SIGTERM raises `Terminated` (a BaseException). `report()`: kernel and Python dispositions. |
| `phase2d/run_one_v8.py` (new) | Calls `sigsafe.restore()`, logs `[signals]`, then runs the unchanged `run_one_v2.main` against manifest v8. Its `except BaseException` writes `incident.json` and re-raises. |
| `phase2d/verify_reload_v8.py` (new) | Calls `sigsafe.restore()`, then the unchanged `verify_reload.main`. |
| `phase2d/run_gate2_v8.py` (new; v7 runner plus the changes below) | Signal repair in the sequence process. |
| `phase2d/gate_v8.py` (new) | Verifies the inventory and writes manifest v8 and `gate2/recovery_v8_audit.json`. |
| `phase2d/gate2_analysis_v8.py` (new) | Frozen analysis with Layer 2 seed 2000 also mapped to its `_a2` rerun. |

`run_one_v2.py`, `verify_reload.py`, `train/`, `common.py`, the analysis definitions, rankings
and limits are unchanged.

`run_gate2_v8.py` versus `run_gate2_v7.py`:
- `main()` calls `sigsafe.restore()` first and logs the sequence's own dispositions.
- Every run and reload child is logged with its PID at start and at exit (return code).
- The whole guard loop is inside `try … except (KeyboardInterrupt, Terminated)`. A SIGINT or
  SIGTERM to the sequence becomes hazard "sequence process received … (manual stop)", is
  forwarded to the child as SIGINT, and the sequence stops.
- New `interrupt()` (guard hazards and manual stops):
  - ignores further SIGINT/SIGTERM in the sequence
  - sends SIGINT to the child, waits up to 180 s, then SIGKILL as the fallback
  - logs the child's return code and whether `incident.json` exists
- A signal between runs stops the sequence with a recorded cause and starts no new run.
- The interruption log records `incident_written`.
- File names are v8, `run_one_v8.py` and `verify_reload_v8.py` are used, and the runner asserts 41 runs.
- All thresholds are unchanged: sleep 30 s, AC 2 polls, lid, thermal, pressure ≥ 4, 180 s fallback.

## 3. Manifest v8
- `manifest_gate2_recovery_v8.json`, SHA-256
  **`fbb9dc0f97b3035fea2dd089c3bbad310c6e47189273c5882d72d00986f08427`**
- 41 runs, estimated 21.6 h. Code hash: 43 files, matching the current code.

| # | Seed | Layers | Run IDs |
|---|---|---|---|
| 1 | 2000 | 2 | `p2d_oracle_L02_s2000_a2` (rerun_of `p2d_oracle_L02_s2000`) |
| 2–20 | 2000 | 3–11, 13–22 | `p2d_oracle_L03_s2000` … `p2d_oracle_L22_s2000` |
| 21–41 | 3000 | 1–11, 13–22 | `p2d_oracle_L01_s3000` … `p2d_oracle_L22_s3000` |

| Status | Count |
|---|---|
| Completed, kept, not rerun | 22 (seed 1000: 21 layers; seed 2000: Layer 1) |
| Failed, partial folders preserved | 4 (L02 s1000, L06 s1000, L07 s1000, L02 s2000) |
| In v8 | 41 (1 rerun + 40 never started) |

22 + 41 = 63, and they cover the full Gate 2 grid (21 layers × 3 seeds) exactly once.

Manifest audit:
- 41 unique IDs; no run folder exists for any of them; no completed run is included.
- The order equals v7's with completed runs removed.
- No training field differs from v7.
- All 41 config hashes are valid.
- Fingerprints, probe, per-seed expectations and pilot records are identical to v7.
- Limits are identical: footprint 11,776 MB, swap growth 512 MB, runtime 1.5×, critical pressure.

## 4. Dummy tests through the production launch path
Each test ran as `nohup caffeinate -dims ../venv/bin/python -B harness.py … &` from a
non-interactive shell in `dssa/phase2d`, the same as the production launch.
- **The harness** is the real `run_gate2_v8.main()`, with only artifact, run and code paths
  redirected to the scratchpad, and hazards injected into `env_state`.
- **Run 1** is a dummy that completes.
- **Run 2 executes the real `run_one_v8.py`**: real `sigsafe.restore()` and real `run_one_v2.main`,
  including the manifest, config and code-hash checks, data-stream replay, telemetry thread,
  `p_batch`/`tick()` and optimizer step hook, and the incident handler.
  `train.run_training` is replaced by a model-free loop with native matrix multiplies:
  no model, no data, no training.
- **Run 3** must never start.

Evidence is in `gate2/v8_signal_tests/`: `results.json` (SHA-256 `6e92279f…`), plus per-test logs,
guard logs, status and `incident.json`.

**Signal dispositions (kernel `sigaction`), identical in all 10 tests:**
| Process | SIGINT | SIGTERM |
|---|---|---|
| Sequence (after `restore()`) | caught | caught |
| Run process as inherited from the sequence (before its own restore) | caught | default |
| Run process after `run_one_v8` restore | caught | caught |
| Reload process (inherited / after restore) | caught / caught | default / caught |
| caffeinate (PID recorded; not in the signal path; macOS `ps` cannot show dispositions) | not inspectable | not inspectable |

**Results:**
| Test | Trigger | Run exit | incident.json (error, stage, step) | Sequence | Run 3 |
|---|---|---|---|---|---|
| guard_charger | AC false × 2 polls | −2 (SIGINT), 2.1 s | KeyboardInterrupt, train, 30 | stopped | not started |
| guard_lid | lid closed | −2 | KeyboardInterrupt, train, 15 | stopped | not started |
| guard_thermal | thermal warning | −2 | KeyboardInterrupt, train, 3 | stopped | not started |
| guard_sleep | 100 s sleep gap | −2 | KeyboardInterrupt, train, 3 | stopped | not started |
| manual_child_sigint | documented `kill -INT $(pgrep -P <seq> -f 'run_one_v8.py\|verify_reload_v8.py')` | −2, 1.1 s | KeyboardInterrupt, train, 17 | stopped | not started |
| child_sigterm | `kill -TERM <run pid>` | 1 | Terminated('received SIGTERM'), train, 17 | stopped | not started |
| seq_sigint | `kill -INT <sequence pid>` | −2 (forwarded) | KeyboardInterrupt, train, 17 | stopped | not started |
| seq_sigterm | `kill -TERM <sequence pid>` | −2 (forwarded) | KeyboardInterrupt, train, 18 | stopped | not started |
| reload_guard | AC false during run 1's reload | −2 | none (the reload step has no incident writer, by design) | stopped; run 1 not marked complete | run 2 not started |
| early_signal | SIGINT 1 s after the run process starts, before its entry point | −2 | none (no run folder yet) | stopped | not started |

- In all 10 tests: SIGKILL was never needed, the sequence exited 0–2 s after the action,
  and no test process remained.
- Every `incident.json` has all 15 fields: error, traceback, time, elapsed_s, steps, batches,
  stage, evals, memory, swap, swap at start, pressure, sampled max, telemetry tail, tiles opened.
- The partial folders kept `IN_PROGRESS`, `incident.json`, `telemetry.jsonl` and, where step 3 was
  reached, the partial `_best.pt`.
- Every stop is in the interruption log with cause, error, stage, step and `incident_written`.
- No file in the project changed during the tests (`find -newer` on a stamp file).

## 5. Integrity
- Manifests v1–v7 unchanged (v7 `a4a19944…`, v6 `b4e852aa…`, v5 `d4cfcb74…`, v4 `b855b972…`).
- The 22 completed runs and the 12 pilot runs pass the result-hash, checkpoint-hash and reload checks.
- Partial folders L02 s1000, L06 s1000, L07 s1000 and L02 s2000 match their recorded hashes.
- INCIDENT_003, 004, 005 and 006 are recorded with hashes.
- Frozen artifacts unchanged; data-stream replay matches for all three seeds.
- The locked test set was not accessed. Nothing was committed or pushed.
- Environment at manifest time: no virtual machine, swap 752 MB, pressure normal. Preflight PASS.

## 6. Remaining risks
1. **Stops before the run folder exists.** A signal in the first seconds of a run, before
   `run_one_v2` creates the folder, writes no `incident.json` (test early_signal). The sequence
   still stops, and the guard and interruption logs record it.
2. **Reload stage.** An interruption during reload verification writes no `incident.json`,
   because `verify_reload` has no incident writer. The sequence stops, the run is not counted
   as completed, and the logs record the cause.
3. **Not tested on real training.** Real training was not run. MPS work is queued in short
   steps of about 0.7 s, and a validation tile is a few seconds, so a signal should be handled
   within seconds. Native calls that run for minutes would delay it; the 180 s SIGKILL
   fallback remains for that case.
4. **A second signal during incident writing** could interrupt the write. The guard sends
   only one; a manual stop should be sent once.
5. **A closed lid** suspends the Mac at once. The guard acts on the next wake, as before.
6. **Docker or other memory use** can still trip the 512 MB swap limit (INCIDENT_004/005).
   Docker remains advisory, not a stop condition.

## 7. Launch command (only after approval)
```
cd "/Users/siva/Documents/Major project/dssa/phase2d"
nohup caffeinate -dims ../venv/bin/python -B run_gate2_v8.py > ../artifacts/phase2d/logs/gate2_v8.log 2>&1 &
```
Manual stop: `kill -INT <sequence pid>` (forwarded to the run), or
`kill -INT $(pgrep -P <sequence pid> -f 'run_one_v8.py|verify_reload_v8.py')`.
