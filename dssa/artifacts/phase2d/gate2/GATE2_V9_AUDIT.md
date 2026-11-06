# Gate 2 recovery v9: manifest and audit (awaiting research-lead approval)

Date: 2026-11-04, 13:26 IST. Prepared and audited only. **No training has started.**

## Manifest
- `manifest_gate2_recovery_v9.json`, SHA-256
  **`7e77b72c5b8b91847e948eb171dfed05f16a8e83e43e2095d590ed42751533db`**
- 39 runs, estimated **20.4 h**. Code hash: 47 files, matching the current code.
- Analysis: `gate2_analysis_v9.py` (Layers 2, 6, 7 at s1000 and Layers 2, 4 at s2000 read from `_a2`).

| # | Seed | Layers | Run IDs |
|---|---|---|---|
| 1 | 2000 | 4 | `p2d_oracle_L04_s2000_a2` (rerun_of `p2d_oracle_L04_s2000`) |
| 2–18 | 2000 | 5–11, 13–22 | `p2d_oracle_L05_s2000` … `p2d_oracle_L22_s2000` |
| 19–39 | 3000 | 1–11, 13–22 | `p2d_oracle_L01_s3000` … `p2d_oracle_L22_s3000` |

| Status | Count |
|---|---|
| Completed, kept, not rerun | 24 (s1000: 21 layers; s2000: Layers 1, 2, 3) |
| Failed, partial folders preserved | 5 (L02 s1000, L06 s1000, L07 s1000, L02 s2000, L04 s2000) |
| In v9 (pending) | 39 (1 rerun + 38 never started) |

24 + 39 = 63, and together they cover the Gate 2 grid (21 layers × 3 seeds) exactly once.

## Code changes since v8 (name-only; no logic change)
- No existing file changed. The audited `sigsafe.py`, `run_one_v2.py`, `verify_reload.py`,
  `verify_reload_v8.py`, `run_one_v8.py` and `run_gate2_v8.py` have the same hashes as in v8.
- **`run_one_v9.py`**: `run_one_v8.py` with the manifest path set to v9 (2 lines differ).
- **`run_gate2_v9.py`**: `run_gate2_v8.py` with v9 file names, `run_one_v9.py`, an assertion of
  39 runs and a docstring change. It still uses `verify_reload_v8.py`, which does not depend on
  the manifest.
- **`gate2_analysis_v9.py`**: adds the mapping (4, 2000) → `p2d_oracle_L04_s2000_a2`.
- **`gate_v9.py`**: manifest writer and audit, including the v8 evidence and test-set checks below.

## Manifest audit
- 39 unique IDs; no run folder exists for any of them; no completed run is included.
- The order equals v8's with completed runs removed. No training field differs from v8.
- All 39 config hashes are valid.
- Limits and safety settings are identical to v8: footprint 11,776 MB, swap growth 512 MB,
  runtime 1.5×, critical pressure; sleep, charger, lid and thermal guards; VM advisory.

## Signal handling verification
**Real training interruption under v8** (INCIDENT_007), checked from preserved logs by `gate_v9.py`:
| Check | Result |
|---|---|
| Sequence process (PID 9020) SIGINT / SIGTERM | caught / caught |
| Run process (PID 13214) SIGINT / SIGTERM, from its own `[signals]` line | caught / caught |
| Guard's child PID equals the run's own PID | yes (13214) |
| Hazard and action | lid closed → SIGINT |
| Run exit code | −2 (SIGINT) |
| Time from SIGINT to exit | 0.429 s; no SIGKILL |
| `incident.json` | `KeyboardInterrupt()`, stage `train`, step 850, 851 batches, 4 evaluations, elapsed 877.7 s; all 15 fields present |
| Sequence | stopped; interruption logged with `incident_written: true` |
| Later v8 runs started | none |

**Dummy tests of the v9 files**, run through `nohup caffeinate … &` like production
(`gate2/v9_signal_tests/`):
- **Documented manual stop**: the run exited −2. `incident.json` reported KeyboardInterrupt,
  train, step 10. The sequence stopped 2.1 s after the action and the next run did not start.
- **Charger hazard**: the run exited −2 with `incident_written: true`, step 20. The sequence
  stopped 1.1 s after the hazard and the next run did not start.
- **Signal dispositions**: the sequence and run processes had SIGINT and SIGTERM caught.
- No test process remained and no project file changed.

## Integrity
- Manifests v1–v8 unchanged (v8 `fbb9dc0f…`, v7 `a4a19944…`, v6 `b4e852aa…`, v5 `d4cfcb74…`, v4 `b855b972…`).
- The 24 completed runs and the 12 pilot runs pass the result-hash, checkpoint-hash and reload checks.
- All five partial folders match their recorded hashes, including L04 s2000:
  `476afbe9…`, `21b063fd…`, `dec5eba0…`, `a3ed282a…`.
- INCIDENT_003 to 007 are recorded with hashes.
- Frozen artifacts unchanged; data-stream replay matches for seeds 1000/2000/3000.
- **Locked test set:** 40 result and incident records across all run folders list only approved
  training and validation tiles. 0 of the 8 locked test tiles were opened. The runner's
  file-open guard blocks them in every process.
- Environment at manifest time: no virtual machine, swap 752 MB, pressure normal. Preflight PASS.
- Nothing was committed or pushed. No system settings were changed.

## Remaining risks
1. **Lid close and charger**: every lid close, unplug or sleep stops the run (INCIDENT_003/006/007).
   20.4 h needs the Mac to stay open, plugged in and awake for the whole period.
2. **Docker or other memory use** can trip the 512 MB swap limit (INCIDENT_004/005).
3. **Edge cases without `incident.json`**: a stop in the first second of a run or during the
   reload check writes none. The sequence still stops and the logs record the cause.
4. **A second stop signal** could interrupt the incident write. Send the manual stop once.

## Launch command (only after approval)
```
cd "/Users/siva/Documents/Major project/dssa/phase2d"
nohup caffeinate -dims ../venv/bin/python -B run_gate2_v9.py > ../artifacts/phase2d/logs/gate2_v9.log 2>&1 &
```
Manual stop: `kill -INT <sequence pid>`, or `kill -INT $(pgrep -P <sequence pid> -f 'run_one_v9.py|verify_reload_v8.py')`.
