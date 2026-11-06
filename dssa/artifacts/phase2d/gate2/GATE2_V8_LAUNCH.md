# Gate 2 recovery v8 launch

- Authorized by the research lead on 2026-11-04. Launched at 11:19:48 IST.
- Manifest `manifest_gate2_recovery_v8.json`, SHA-256
  `fbb9dc0f97b3035fea2dd089c3bbad310c6e47189273c5882d72d00986f08427`. 41 runs, est 21.6 h.
- Final preflight at 11:19:43: PASS (AC, lid open, no thermal warning, pressure 1, 186.3 GB
  free, files local, no other run, no VM). No training process active. Swap 752 MB.
- Code hash equals the manifest (43 files), including the audited signal-handling files:
  `sigsafe.py` 07a79495…, `run_one_v8.py` 6ecec2be…, `verify_reload_v8.py` 398f4984…,
  `run_gate2_v8.py` 7caa514c…. Frozen artifacts unchanged.
- Command (from `dssa/phase2d`):
  `nohup caffeinate -dims ../venv/bin/python -B run_gate2_v8.py > ../artifacts/phase2d/logs/gate2_v8.log 2>&1 &`

## Processes and signal check (first real run)
| Process | PID | Parent | SIGINT | SIGTERM |
|---|---|---|---|---|
| Sequence | 9020 | 9019 | caught | caught |
| caffeinate | 9022 | 9020 | — | — |
| Run 1 `p2d_oracle_L02_s2000_a2` | 9028 | 9020 | caught | caught |

The run's PID matches the guard log's `child_pid`. All three share process group 9019.

## Initial telemetry (step 111)
Footprint 6.85 GB (limit 11.5 GB), swap growth 0 MB (limit 512 MB), pressure 1.

## Manual stop
`kill -INT 9020` (forwarded to the active run), or
`kill -INT $(pgrep -P 9020 -f 'run_one_v8.py|verify_reload_v8.py')`. Send once.
