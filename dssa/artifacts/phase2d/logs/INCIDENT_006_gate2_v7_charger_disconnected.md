# INCIDENT_006: Gate 2 recovery (v7) stopped at run 17 of 57, charger disconnected

Date: 2026-11-04. Manifest v7 `a4a19944816713cd938fefb475894f1980af44f89df7552bce2f90579f8b3e56` (unchanged).

## What stopped
- Run: `p2d_oracle_L02_s2000` (Layer 2, seed 2000), run 17 of 57. Started 07:31:43 IST.
- Guard hazard: **charger disconnected** (AC false on 2 consecutive polls), logged at
  07:55:54 IST. State then: battery power, lid open, no thermal warning, pressure 1.
- **Stage and step at the hazard:** `train`, optimizer step 1,398 (last telemetry before
  the hazard, 9 s earlier). The step-1,400 validation then ran from about 07:55:59 to 07:57:00
  and training continued.
- Guard action: SIGINT at 07:55:54. The run did not exit. SIGKILL at 07:58:54 after the
  180 s wait, at optimizer step **1,561**, stage `train` (last telemetry record).
- Sequence stopped by rule; recorded in `logs/gate2_interruptions_v7.jsonl`. Runs 18–57 not
  started. No retry, no skip.
- After the stop, the Mac went into clamshell sleep on battery at 10:22 and woke at 11:05
  (lid). Nothing was running then.

## Defect found: the guard's SIGINT was ignored
- `incident.json` was **not written**, because the run never received a KeyboardInterrupt.
- Cause (verified): the sequence was launched with `nohup … &` from a non-interactive
  shell. POSIX shells set SIGINT to *ignored* for background jobs, and the ignored state is
  inherited by every child. Python does not install its KeyboardInterrupt handler when
  SIGINT is already ignored. Test: a `nohup python3 … &` child reports
  `signal.getsignal(SIGINT) == 1` (SIG_IGN); a foreground child reports `default_int_handler`.
- Effect: the guard's SIGINT, and the documented manual stop
  (`kill -INT $(pgrep -P <seq> -f 'run_one_v7.py|verify_reload.py')`), cannot stop a run
  launched this way. Only the 180 s SIGKILL fallback works, and it writes no incident record.
  This applied to the v5, v6 and v7 launches. The earlier stops (INCIDENT_004/005) were
  raised inside the runner and were not affected. The dummy guard tests passed because the
  harness did not launch through `nohup … &`.
- The stop itself still happened, the sequence stopped by rule, and the guard log recorded
  the hazard and the SIGKILL.

## Preserved evidence (not modified)
`runs/p2d_oracle_L02_s2000/` (no `incident.json`, no final checkpoint):
- `IN_PROGRESS` `e32b59c352f1eabd358476de257cd0df6481c06c684dab119040c8bb31b8cb95`
- `p2d_oracle_L02_s2000_best.pt` `c5eed1466da22452c20424143a69c2e773091433107510151cd5f9aba884414c`
- `telemetry.jsonl` `5557da8a0059e96539719fd8d21cb184bdde65802447d169e878da4361bad80e`

Also `logs/p2d_oracle_L02_s2000.log`, `logs/gate2_v7.log`,
`logs/gate2_guard_v7.jsonl` (`da01699b…`), `logs/gate2_interruptions_v7.jsonl` (`ffff7ed2…`),
`gate2_status_v7.json`.

## Checks after the stop
- The 16 runs completed in v7 pass every frozen-analysis integrity check. Swap growth was
  0 MB in all 16; peak footprint 5.56–8.24 GB.
- Frozen artifacts and manifest v7 unchanged. No sequence process remains.
