# INCIDENT_008: Gate 2 recovery (v9) stopped at run 11 of 39, lid closed

Date: 2026-11-04. Manifest v9 `7e77b72c5b8b91847e948eb171dfed05f16a8e83e43e2095d590ed42751533db` (unchanged).

## What stopped
- Run: `p2d_oracle_L15_s2000` (Layer 15, seed 2000), run 11 of 39. Started 19:01:53 IST (PID 32541).
- **Cause:** the lid was closed. macOS logged `Clamshell Sleep` (dark wake) at 19:20:15 IST,
  on AC power. The Mac returned to full wake through user activity at 19:20:45.
- **Guard:** hazard `lid closed` at 19:20:17 IST (state: lid closed, AC true, no thermal
  warning, pressure 1). SIGINT sent to PID 32541.
- **Run response:** exit code −2, 0.44 s after the SIGINT. `incident.json` written:
  `KeyboardInterrupt()`, **stage `train`, optimizer step 1,289** (1,290 batches, 6 evaluations,
  elapsed 1,102.9 s). No SIGKILL.
- **Sequence:** stopped by rule; logged in `logs/gate2_interruptions_v9.jsonl` with
  `incident_written: true`. Runs 12–39 not started. No retry, no skip.
- Swap growth 0 MB throughout; no VM at any v9 preflight.

## Preserved evidence (not modified)
`runs/p2d_oracle_L15_s2000/`:
- `IN_PROGRESS` `c9948e58126fa7c6704d3d1afe318dc81f81a2b286e60a48a82cf87fd6e0909f`
- `incident.json` `d2ce925fdb432749cacaaf7249b789c2cc6f44397b391a338fd9b7e76fcde8db`
- `p2d_oracle_L15_s2000_best.pt` `2b9f267bb82b8205fa685c93c4cceb7b60dafc0b00c89e0fd8655c2951986ec1`
- `telemetry.jsonl` `932dfd11b7aa1578d988e5ae7738c0c80f183a64e4fe326a92236954367bf7eb`

Also `logs/p2d_oracle_L15_s2000.log`, `logs/gate2_v9.log`, `logs/gate2_guard_v9.jsonl`
(`fcf84179…`), `logs/gate2_interruptions_v9.jsonl` (`b1684ef5…`), `gate2_status_v9.json`.

## Checks after the stop
- v9 runs 1–10 (L04 `_a2`, L05–L11, L13, L14 at seed 2000) completed; all pass every integrity
  check. Gate 2 total: 34 of 63 completed.
- Frozen artifacts and manifest v9 unchanged. No sequence or run process remains.
