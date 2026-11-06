# Gate 2 recovery v12: manifest and audit (awaiting research-lead approval)

Date: 2026-11-05. Prepared and audited only. **No training has started.**

## Manifest
- `manifest_gate2_recovery_v12.json`, SHA-256
  **`a69495276999c140eda469d61ca7344b151d7f3d106203d97b5a19c974feae65`**
- 17 runs.
- **Runtime:** the estimated training time is **8.65 h**. Across v10 and v11, completed runs took about
  1–2% longer than estimated, which projects to **about 8.8 h** of wall time.
- **Code hash:** 59 files, matching the current code.
- **Writer:** `phase2d/gate_v12.py`. It verifies everything below before writing and refuses to
  overwrite an existing manifest.

| # | Seed | Layers | Run IDs |
|---|---|---|---|
| 1 | 3000 | 5 | `p2d_oracle_L05_s3000_a2` (rerun_of `p2d_oracle_L05_s3000`) |
| 2–17 | 3000 | 6–11, 13–22 | `p2d_oracle_L06_s3000` … `p2d_oracle_L11_s3000`, `p2d_oracle_L13_s3000` … `p2d_oracle_L22_s3000` |

| Status | Count |
|---|---|
| Completed, kept, not rerun | **46** (s1000: 21; s2000: 21; s3000: Layers 1–4) |
| Failed, partial folders preserved | **8** (L02, L06, L07 s1000; L02, L04, L15, L20 s2000; L05 s3000) |
| In v12 (pending) | **17** (1 rerun + 16 never started) |

- **Grid coverage:** 46 + 17 = 63, which covers the 21 × 3 Gate 2 grid exactly once. This was checked
  against every result folder.
- **Order:** the same as v11's, with completed runs removed.
- **Changes from v11:** only `run_id`, `rerun_of`, `phase` and `config_hash` differ.
- **Unchanged from v11:**
  - `limits`: footprint 11,776 MB, **swap growth 512 MB**, runtime 1.5× estimate, critical memory pressure
  - `failure_policy`
  - `safety_additions`, apart from the interruption-log file name

## Code (reuses the audited v11/v10 implementation)
| File | Status |
|---|---|
| `sigsafe.py`, `run_one_v2.py`, `verify_reload.py`, `verify_reload_v8.py` | Unchanged; hashes equal to manifest v11 |
| `run_gate2_v12.py` (`bded41d4…`) | Differs from v11 only in: the docstring line; the 4 file names (manifest, status, guard log, interruptions); `assert n == 17`; the log prefix; `run_one_v12.py`. No behavioural change |
| `run_one_v12.py` (`8220d7ee…`) | Differs from v11 only in the manifest path and docstring |
| `gate2_analysis_v12.py` (`ba227c25…`) | The v11 mappings plus `(5, 3000) → p2d_oracle_L05_s3000_a2` |
| `gate_v12.py` (`148ed3a5…`) | New manifest writer |

- **Closed lid:** logged only. That is unchanged.
- **Watchdogs:** telemetry 60 s and optimizer step 300 s, unchanged.
- **Other guards:** sleep 30 s, charger 2 polls, thermal and memory pressure, all unchanged.

## Dummy tests of the v12 files (production `nohup caffeinate … &` path)
- **Evidence:** `gate2/v12_signal_and_health_tests/`.
- **What ran:** the real `run_gate2_v12.main`, the real `run_one_v12.py` and the real
  `run_one_v2.main`. Only the training loop was replaced, by one with no model.
- **Signals:** in every test, both the sequence and the run reported SIGINT and SIGTERM as `caught`.

| Test | Expected | Result |
|---|---|---|
| lid_advisory: lid reported closed for 45 s | no stop | Lid event logged; run kept training (744 steps); ended only by the manual stop: exit −2, incident |
| guard_charger | stop | SIGINT; exit −2 after 0.24 s; incident (step 32); sequence stopped |
| manual_child_sigint (documented command) | stop | exit −2; incident (step 17); sequence stopped |
| guard_sleep (100 s gap) | stop | exit −2 after 0.19 s; incident (step 3) |
| guard_thermal | stop | exit −2 after 0.23 s; incident (step 1) |
| step_stall | stop at 300 s | "training stalled (no optimizer step for 300 s at step 5)"; exit −2 after 0.24 s; incident |
| telemetry_stale (SIGSTOP-frozen process) | stop at 60 s | "unresponsive (61 s)"; SIGKILL after 180 s (exit −9); no incident by design; cause logged |

In every stop case, the next run did not start. No test process remained.

## Real-training interruption evidence (from preserved logs)
| Run | Hazard | Signals (run / sequence) | Exit | SIGINT→exit | SIGKILL | Step | Later runs |
|---|---|---|---|---|---|---|---|
| L04 s2000 (v8) | lid closed | caught / caught | −2 | 0.429 s | no | 850 | none |
| L15 s2000 (v9) | lid closed | caught / caught | −2 | 0.441 s | no | 1,289 | none |
| L20 s2000 (v10) | system sleep (286 s) | caught / caught | −2 | 0.605 s | no | 1,508 | none |
| L05 s3000 (v11) | system sleep (937 s) | caught / caught | −2 | 0.382 s | no | 152 | none |

In all four cases:
- The run PID matched the guard's child PID.
- `incident.json` has all 15 fields.
- The interruption is logged.
- The sequence state is `stopped`.

## Integrity
- **Manifests:** v4–v11 unchanged (v11 `7c60dee4…`).
- **Completed runs:** all **46** Gate 2 runs and the **12** pilot runs pass the result-hash,
  checkpoint-hash and reload checks.
- **Partial folders:** all **8** match their recorded hashes.
  - L05 s3000 is preserved as recorded in INCIDENT_010 (`04dcd680…`, `826d780f…`, `abe6082f…`).
  - It has no checkpoint, because it stopped at step 152, before the first evaluation.
  - No `_a2` folder exists.
- **Incident reports:** INCIDENT_003 to 010 are recorded, with their hashes in the manifest.
- **Frozen artifacts:** unchanged. Data-stream replay matches for all seeds.
- **Locked test set:** 65 result and incident records list only approved tiles; **0 of 8 locked test
  tiles opened**.
- **Preflight `--check`: PASS.**
  - Charger connected (99%, finishing charge), no thermal warning, memory pressure 1, 185 GB free.
  - No other run, lid open, no virtual machine. Swap used: 413.6 MB.
- No training process is running. No system settings were changed. Nothing was committed or pushed.

## Remaining operational risks
1. **Charger loss after a lid close (INCIDENT_009 and 010).**
   - In both cases, macOS switched to battery 3–5 s after the lid closed. It then slept for real, and
     the guard stopped the run safely.
   - Power returned only with a charger-attach event.
   - No charge-limiting software is installed.
   - The logs cannot tell a physical unplug apart from the connection dropping when the lid closes.
   - Until closed-lid operation on AC has been verified to hold, the **safest plan is to keep the lid
     open for the whole run** (about 8.8 h).
2. **Sustained closed-lid training on AC has not been demonstrated.** The longest period seen so far is
   about 6 s.
3. **Heat:** a closed lid may run warmer. The thermal guard is unchanged.
4. **Memory:** Docker or other memory use can still trip the 512 MB swap-growth limit.
   - The Docker helper is running, but its automatic start is off.
   - The seed-3000 shallow-layer runs peaked at about 8.1 GB, below the 11,776 MB footprint limit.
5. **Stops that do not write `incident.json`:**
   - a stop in the first second of a run
   - a stop during reload verification
   - a frozen-process kill

   The logs record the cause in each case.
6. **Early stops leave no checkpoint:** a stop before step 200 leaves none, as with L05 s3000. This does
   not affect the evidence chain.

## Launch command (only after approval)
```
cd "/Users/siva/Documents/Major project/dssa/phase2d"
nohup caffeinate -dims ../venv/bin/python -B run_gate2_v12.py > ../artifacts/phase2d/logs/gate2_v12.log 2>&1 &
```
Manual stop: `kill -INT <sequence pid>` (send once).
