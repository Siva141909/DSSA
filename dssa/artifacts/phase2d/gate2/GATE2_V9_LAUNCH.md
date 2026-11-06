# Gate 2 recovery v9 launch

- Authorized by the research lead on 2026-11-04 for the complete 39-run sequence and its frozen analysis.
- Launched at 13:28:57 IST. Manifest `manifest_gate2_recovery_v9.json`, SHA-256
  `7e77b72c5b8b91847e948eb171dfed05f16a8e83e43e2095d590ed42751533db`. 39 runs, est 20.4 h.
- Final preflight at 13:28:53: PASS. No training process active. Code and config hashes
  match; no v9 run folder existed; frozen artifacts unchanged. Swap 470 MB, no thermal warning.
- Command (from `dssa/phase2d`):
  `nohup caffeinate -dims ../venv/bin/python -B run_gate2_v9.py > ../artifacts/phase2d/logs/gate2_v9.log 2>&1 &`

| Process | PID | Parent | SIGINT | SIGTERM |
|---|---|---|---|---|
| Sequence | 14585 | 14584 | caught | caught |
| caffeinate | 14587 | 14585 | — | — |
| Run 1 `p2d_oracle_L04_s2000_a2` | 14593 | 14585 | caught | caught |

Initial telemetry (step 95): footprint 6.88 GB, swap growth 0 MB, pressure 1.

Manual stop: `kill -INT 14585` (forwarded to the active run). Send once.
