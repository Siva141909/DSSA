# INCIDENT_007: Gate 2 recovery (v8) stopped at run 3 of 41, lid closed

Date: 2026-11-04. Manifest v8 `fbb9dc0f97b3035fea2dd089c3bbad310c6e47189273c5882d72d00986f08427` (unchanged).

## What stopped
- Run: `p2d_oracle_L04_s2000` (Layer 4, seed 2000), run 3 of 41. Started 12:32:27 IST (PID 13214).
- **Cause:** the lid was closed. macOS logged `Clamshell Sleep` at 12:47:01 on AC, then
  entered sleep at 12:47:06 on battery (the charger was also disconnected).
- **Guard:** hazard `lid closed` logged at 12:47:05 IST (state: lid closed, AC false,
  no thermal warning, pressure 1), during the 5-second dark-wake before full sleep.
  SIGINT sent to PID 13214.
- **Run response:** exited 0.43 s later with return code −2 (SIGINT). `incident.json` written:
  `KeyboardInterrupt()`, **stage `train`, optimizer step 850** (851 batches drawn, 4 evaluations
  completed, elapsed 877.7 s), raised inside the optimizer step. SIGKILL was not needed.
- **Sequence:** stopped by rule; recorded in `logs/gate2_interruptions_v8.jsonl` with
  `incident_written: true`. Runs 4–41 not started. No retry, no skip.
- The Mac stayed asleep (brief maintenance wakes on battery) until the lid was opened at 13:23:51.

## Signal-repair verification on a real training run
This is the first real interruption since the v8 fix (INCIDENT_006). Behaviour matched the
audited dummy tests: the run process had SIGINT and SIGTERM `caught`, the guard's SIGINT
reached it, the existing `run_one_v2` handler wrote a complete `incident.json`, the process
exited within half a second, and no further run started.

## Telemetry
Swap growth 0 MB throughout (start 752 MB); footprint 7.61 GB at the stop; pressure normal.

## Preserved evidence (not modified)
`runs/p2d_oracle_L04_s2000/`:
- `IN_PROGRESS` `476afbe99ee85bbb440bb32f916a864d42459ec76d1b8410109b21c02033f178`
- `incident.json` `21b063fd75624a462fffd5d8dba4681d3e80bb5ab085e3680e05a940acce4af3`
- `p2d_oracle_L04_s2000_best.pt` `dec5eba0c41d7d256e14759bbcc4d529dd9765357ec00fbffa498808e5bc9135`
- `telemetry.jsonl` `a3ed282aa6feca1cd84f1e1e859903363cbbf9de6fa279dc6bc69ad929bbc35e`

Also `logs/p2d_oracle_L04_s2000.log`, `logs/gate2_v8.log`, `logs/gate2_guard_v8.jsonl`
(`16f41e87…`), `logs/gate2_interruptions_v8.jsonl` (`658aee0f…`), `gate2_status_v8.json`.

## Checks after the stop
- Runs 1–2 of v8 (`p2d_oracle_L02_s2000_a2`, `p2d_oracle_L03_s2000`) completed and pass every
  integrity check. Gate 2 total: 24 of 63 completed.
- Frozen artifacts and manifest v8 unchanged. No sequence or run process remains.
