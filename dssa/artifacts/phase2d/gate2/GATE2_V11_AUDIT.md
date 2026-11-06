# Gate 2 recovery v11: manifest and audit (awaiting research-lead approval)

Date: 2026-11-04. Prepared and audited only. **No training has started.**

## Manifest
- `manifest_gate2_recovery_v11.json`, SHA-256
  **`7c60dee4490ef828a33b0fe54df500375b513a063b0df211ce6e7e765ae77538`**
- 24 runs. Estimated training time is **12.43 h**. v10 runs 1–5 took 144.8 min of wall time against an
  estimated 142.8 min (+1.4%), which projects to **about 12.6 h** of wall time.
- Code hash: 55 files, matching the current code.
- Written by `phase2d/gate_v11.py`. That script verifies everything below before writing, and refuses
  to overwrite an existing manifest.

| # | Seed | Layers | Run IDs |
|---|---|---|---|
| 1 | 2000 | 20 | `p2d_oracle_L20_s2000_a2` (rerun_of `p2d_oracle_L20_s2000`) |
| 2–3 | 2000 | 21, 22 | `p2d_oracle_L21_s2000`, `p2d_oracle_L22_s2000` |
| 4–24 | 3000 | 1–11, 13–22 | `p2d_oracle_L01_s3000` … `p2d_oracle_L22_s3000` |

| Status | Count |
|---|---|
| Completed, kept, not rerun | **39** (s1000: 21; s2000: Layers 1–11 and 13–19) |
| Failed, partial folders preserved | **7** (L02/L06/L07 s1000; L02/L04/L15/L20 s2000) |
| In v11 (pending) | **24** (1 rerun + 23 never started) |

- **Grid coverage:** 39 + 24 = 63. Together they cover the 21 × 3 Gate 2 grid exactly once
  (checked against every result folder).
- **Order:** the same as v10's, with completed runs removed.
- **Fields changed from v10:** only `run_id`, `rerun_of`, `phase` and `config_hash`.
  - Training settings, seeds, K, caches, frozen hashes and estimates are identical.
- **Unchanged from v10:** `limits` (footprint 11,776 MB, **swap growth 512 MB**, runtime 1.5×, critical
  pressure) and `failure_policy`.
- **`safety_additions`:** differ from v10 only in the interruption-log file name.

## Code (reuses the audited v10 implementation)
| File | Status |
|---|---|
| `sigsafe.py` `07a79495…`, `run_one_v2.py` `62484988…`, `verify_reload.py` `a6ddbe41…`, `verify_reload_v8.py` `398f4984…` | Unchanged; hashes match manifest v10 |
| `run_gate2_v11.py` | Diff from v10: docstring line, the 4 file names (manifest, status, guard log, interruptions), `assert n == 24`, log prefix, `run_one_v11.py`. No behavioural change |
| `run_one_v11.py` | Diff from v10: manifest path and docstring only |
| `gate2_analysis_v11.py` | v10 mappings + `(20, 2000) → p2d_oracle_L20_s2000_a2` |
| `gate_v11.py` | Manifest writer (new) |

The closed-lid behaviour is unchanged: lid changes are logged only. The 60 s telemetry and 300 s
optimizer-step watchdogs are unchanged.

## Dummy tests of the v11 files (production `nohup caffeinate … &` path)
Evidence: `gate2/v11_signal_and_health_tests/`. The tests use the real `run_gate2_v11.main`, the real
`run_one_v11.py` and the real `run_one_v2.main`, with a model-free training loop. In every test, the
sequence and the run reported SIGINT and SIGTERM as `caught`.

| Test | Expected | Result |
|---|---|---|
| lid_advisory: lid reported closed for 45 s | no stop | Lid event logged; the run kept training (757 steps). Ended only by the manual stop: exit −2, incident written |
| guard_charger | stop | SIGINT; exit −2 after 0.19 s; incident written (step 21); sequence stopped |
| manual_child_sigint (documented command) | stop | Exit −2; incident written (step 18); sequence stopped |
| guard_sleep (100 s gap) | stop | Exit −2 after 0.19 s; incident written (step 3) |
| guard_thermal | stop | Exit −2 after 0.19 s; incident written (step 3) |
| step_stall | stop at 300 s | "training stalled (no optimizer step for 300 s at step 5)"; exit −2; incident written |
| telemetry_stale (SIGSTOP-frozen process) | stop at 60 s | "unresponsive (61 s)"; SIGKILL after 180 s (exit −9); no incident by design; cause logged |

- In every stop case the next run did not start.
- No test process remained.

## Real-training interruption evidence (from preserved logs)
| Run | Hazard | Signals (run / sequence) | Exit | SIGINT→exit | SIGKILL | Step | Later runs |
|---|---|---|---|---|---|---|---|
| L04 s2000 (v8) | lid closed | caught / caught | −2 | 0.429 s | no | 850 | none |
| L15 s2000 (v9) | lid closed | caught / caught | −2 | 0.441 s | no | 1,289 | none |
| L20 s2000 (v10) | system sleep (286 s) | caught / caught | −2 | 0.605 s | no | 1,508 | none |

In all three, the run PID matched the guard's child PID, `incident.json` has all 15 fields, the
interruption is logged, and the sequence state is `stopped`.

## Integrity
- **Manifests v4–v10:** unchanged (v10 `006394f7…`).
- **Completed runs:** all **39** Gate 2 runs and the **12** pilot runs pass the result-hash,
  checkpoint-hash and reload checks.
- **Partial folders:** all **7** match their recorded hashes. L20 s2000 is preserved as recorded in
  INCIDENT_009 (`87e3ecd2…`, `a9e06a48…`, `6a374c61…`, `1f9a8fc8…`), and no `_a2` folder exists.
- **Incidents:** INCIDENT_003 to 009 are recorded, and their hashes are in the manifest.
- **Frozen artifacts:** unchanged. Data-stream replay matches for all seeds.
- **Locked test set:** 57 result and incident records list only approved tiles; **0 of 8 locked test
  tiles opened**.
- **Preflight `--check`: PASS.**
  - Charger on, no thermal warning, memory pressure 1, 185 GB free disk, no other run, lid open.
  - Docker's `vmnetd` helper is present but no virtual machine is running.
  - Swap used: 429.6 MB.
- No training process is running and no system settings were changed. Nothing was committed or pushed.

## Remaining operational risks
1. **A closed lid on battery means real sleep (INCIDENT_009).**
   - Unplugging the charger 5 s after closing the lid suspended training for 286 s and stopped the
     sequence safely.
   - **The charger must stay connected whenever the lid is closed.**
2. **Sustained closed-lid training on AC is still unverified.** The longest observed period is about
   5 s (14 steps at the normal rate). The 60 s and 300 s watchdogs and the sleep check protect a longer
   one.
3. **Heat:** a closed lid may run warmer. The thermal guard is unchanged.
4. **Swap:** Docker or other memory use can still trip the 512 MB swap-growth limit. The Docker helper
   runs, but its automatic start is off.
5. **No `incident.json` in some cases:**
   - a stop in the first second of a run
   - a stop during reload verification
   - a frozen-process kill
   In each case the logs record the cause.
6. **Runtime:** about 12.6 h in one sitting.
   - Seed-3000 runs at shallow layers are longer (up to 37.8 min).
   - Each run's runtime limit is 1.5 times its estimate.

## Launch command (only after approval)
```
cd "/Users/siva/Documents/Major project/dssa/phase2d"
nohup caffeinate -dims ../venv/bin/python -B run_gate2_v11.py > ../artifacts/phase2d/logs/gate2_v11.log 2>&1 &
```
Manual stop: `kill -INT <sequence pid>` (send once).
