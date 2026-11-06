# Gate 2 recovery v6 launch

- Authorized by the research lead on 2026-11-03. Launched at 18:24:47 IST.
- Manifest: `manifest_gate2_recovery_v6.json`, SHA-256
  `b4e852aaf9409b8e0bc9541b82a18f66e40bb5ab7f1113835cdefe3a572b428c`. 58 runs, est 30.3 h.
- Final preflight at 18:24:43: all seven checks passed (AC, lid open, no thermal warning,
  pressure 1, 185.5 GB free, files local, no other run). No VM running. Swap 684 MB.
- Launched through `gate2/launch_v6_docker_advisory.py`, per the authorization that Docker
  starting is not a stop condition: the VM preflight check is logged as advisory only.
  All other checks, the guard and the limits are unchanged; code hash matches v6.
- Command (from `dssa/phase2d`):
  `nohup caffeinate -dims ../venv/bin/python -B ../artifacts/phase2d/gate2/launch_v6_docker_advisory.py > ../artifacts/phase2d/logs/gate2_v6.log 2>&1 &`

## Processes
- Sequence: PID 56147 (parent launchd).
- caffeinate: PID 56149.
- Run 1 `p2d_oracle_L06_s1000_a2`: PID 56155.

## Initial telemetry (step 165, about 2 min)
Footprint 5.40 GB (limit 11.5 GB), swap growth 0 MB (limit 512 MB), pressure 1, AC power,
lid open, no thermal or performance warning.

## Manual safe stop
`kill -INT $(pgrep -P 56147 -f 'run_one_v6.py|verify_reload.py')`
The run writes `incident.json`; the sequence stops and logs the cause in
`logs/gate2_interruptions_v6.jsonl`.
