# INCIDENT 003: Gate 2 stopped at run 2 of 63 (runtime limit, caused by system sleep)

Date: 2026-11-03 (IST). The sequence stopped by rule. Nothing was retried, skipped or continued.

## Failed run
- Run: `p2d_oracle_L02_s1000` (Layer 2, seed 1000), run 2 of 63 under manifest v4.
- Stop condition: `RuntimeError('STOP: runtime above 1.5x estimate (3350s)')`, raised by
  the runtime check in `make_batch`.
- Exact stage: `train`, after optimizer step 1,804 of 2,000. 1,804 batches had been drawn
  and 9 of 10 validations (steps 200–1800) had completed. The step-2000 validation, the final
  checkpoint and the reload check did not run.
- Elapsed: 3,350.2 s, against an estimate of 2,233 s and a limit of 3,350 s.
- Memory: peak footprint 8,067 MB (limit 11,776 MB), maximum swap growth 250.8 MB (limit 512 MB).
  Pressure reached warning level in 569 of 8,197 samples (13:15–13:20), never critical.
- Evidence kept: `runs/p2d_oracle_L02_s1000/`, containing `IN_PROGRESS`, `incident.json`
  (traceback, telemetry tail, memory), `telemetry.jsonl` and the step-1800 best checkpoint
  `p2d_oracle_L02_s1000_best.pt`, plus `logs/p2d_oracle_L02_s1000.log`. The 9 completed
  validation results were held in process memory and were not written. This is the
  runner's normal behavior for a failed run.

## Cause: the Mac slept with the lid closed
From `pmset -g log` and the run telemetry:

| Time (IST) | Event |
|---|---|
| 11:42:38 | Run 1 (`p2d_oracle_L01_s1000`) starts, on AC power |
| 12:18:21 | Lid closed: "Entering DarkWake state due to 'Clamshell Sleep'", on AC |
| 12:18:26 | "Entering Sleep state due to 'Clamshell Sleep'", **on battery**; asleep 559 s |
| 12:18:28 | Run 1 telemetry gap of 556.6 s, during its final (step 2000) validation |
| 12:30:25 | Run 1 completes. Its final validation took 733 s instead of about 71 s |
| 12:31:43 | Run 2 starts. Repeated sleep and dark-wake cycles follow: 51 telemetry gaps of more than 2 s, 1,245 s in total, mostly in the first 600 steps |
| 12:47:26 | "Entering Sleep state due to 'Thermal Emergency Sleep'", on battery |
| 13:04:47 | Lid opened; "Display is turned on" |
| 13:27:33 | Run 2 reaches the 1.5x runtime limit at step 1,804 |

`caffeinate -dims` prevents idle sleep. It does not prevent clamshell sleep on a
MacBook without an external display, and its `-s` assertion only applies on AC power.
Training itself was normal whenever the machine was awake: 0.73–0.78 s per step and
71–75 s per validation, the same as the pilot. The time lost was entirely suspended time.

## Run 1 (completed before the stop)
- `p2d_oracle_L01_s1000` passed every integrity check:
  - status `completed`, 2,000 steps
  - decoder hash `ac1d8543`, backbone fingerprint `2d31df5d`, data stream ok
  - checkpoint and result hashes verified
  - reload confusion-matrix difference 0 for both the best and final checkpoints
- Process time was 2,868 s, against an estimate of 2,268 s (1.26x, inside the limit). The 556 s
  of sleep fell inside its final validation.
- On MPS a pause does not change the computation, and the validation history shows no
  discontinuity. A sleep during validation was not tested before, so this is recorded.

## State after the stop
- No Phase 2D process is running. Manifest v4 is unchanged (SHA-256 `b855b972…`).
- Frozen artifacts are unchanged. Nothing was committed or pushed.
- Thermal note: the machine reached a thermal emergency sleep while closed. Running GPU
  training with the lid closed, for example in a bag, is a hardware risk.
