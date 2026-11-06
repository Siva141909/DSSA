# Gate 2 recovery v10 launch

- Authorized by the research lead on 2026-11-04 for the complete 29-run sequence and its frozen analysis.
- Launched at 20:08:56 IST. Manifest `manifest_gate2_recovery_v10.json`, SHA-256
  `006394f7b27b57089cc42e29c8aa91d91650c3147a5551f74712a28f6401da96`. 29 runs, est 14.8 h.
- Final preflight at 20:08:48: PASS. No training process. Code and config hashes match; no v10
  run folder existed; frozen artifacts unchanged. Swap 454 MB; no thermal or performance warning; lid open.
- Command (from `dssa/phase2d`):
  `nohup caffeinate -dims ../venv/bin/python -B run_gate2_v10.py > ../artifacts/phase2d/logs/gate2_v10.log 2>&1 &`

| Process | PID | Parent | SIGINT | SIGTERM |
|---|---|---|---|---|
| Sequence | 38257 | 38256 | caught | caught |
| caffeinate | 38259 | 38257 | — | — |
| Run 1 `p2d_oracle_L15_s2000_a2` | 38265 | 38257 | caught | caught |

Initial telemetry (step 97): footprint 4.81 GB, swap growth 0 MB, pressure 1.

Lid policy: a closed lid is logged, not a stop. Telemetry watchdog 60 s and optimizer-step
watchdog 300 s active. Run 1 lid, progress and thermal observations every 30 s:
`gate2/v10_run1_lid_observation.tsv`. Temperatures are reported through macOS thermal and
performance warning levels and `CPU_Speed_Limit`; raw sensor temperatures need administrator
tools that were not used.

Note: a `pmset -g thermlog` started during the launch check streamed indefinitely; it was stopped
by its exact PID (38350). The sequence was unaffected.

Manual stop: `kill -INT 38257` (forwarded to the active run). Send once.
