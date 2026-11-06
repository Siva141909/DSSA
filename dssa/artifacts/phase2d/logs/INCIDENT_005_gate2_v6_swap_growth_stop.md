# INCIDENT_005: Gate 2 recovery (v6) stopped at run 2 of 58, swap growth limit

Date: 2026-11-03. Manifest v6 `b4e852aaf9409b8e0bc9541b82a18f66e40bb5ab7f1113835cdefe3a572b428c` (unchanged).

## What stopped
- Run: `p2d_oracle_L07_s1000` (Layer 7, seed 1000), run 2 of 58.
- Started 19:00:45 IST; stopped 19:07:07 IST (elapsed 377.2 s).
- Stop condition: `RuntimeError('STOP: swap growth 564 MB above limit')` (limit 512 MB),
  from the runner's monitor. The v6 guard logged no hazard.
- **Failure stage:** `validation`, optimizer step 400.
- Sequence stopped by rule. Recorded in `logs/gate2_interruptions_v6.jsonl`.
  Runs 3–58 not started. No retry, no skip.

## Telemetry
- Preflight before the run passed; no virtual machine was running at 19:00:45.
- Swap at run start 885 MB (run 1 left 209 MB of growth); at stop 1,449 MB.
- Swap growth stayed at or below 0 for training steps 0–399. It jumped from 29 MB to
  564 MB between elapsed 356 s and 371 s (19:06:41–19:06:56), during the step-400 validation.
- Training process footprint 5.1–6.1 GB during the jump (limit 11.5 GB). Pressure 2.

## Likely cause (correlation, same pattern as INCIDENT_004)
Docker Desktop started at 19:06:05 IST (`--reason=open-tray --name=dashboard`, opened from
the menu-bar tray or dashboard). Its virtual machine (`com.apple.Virtualization.VirtualMachine`,
about 800 MB resident) started at 19:06:06, 35 s before swap began rising. Per the launch
authorization, Docker starting is not itself a stop condition; the stop came from the
unchanged swap-growth limit.

## Completed before the stop
- `p2d_oracle_L06_s1000_a2`: completed, all integrity checks pass. U = +0.0024 (6-class),
  +0.0029 (5-class); swap growth 209 MB (under the limit), peak 7.67 GB.

## Preserved evidence (not modified)
`runs/p2d_oracle_L07_s1000/`:
- `IN_PROGRESS` `83c34d97354f4427550d41567109a5a64c21e41887cec622057f121c401942e6`
- `incident.json` `b686d7056bf97199e059e5c2af0683afd2a25512611a13b7e3b355729e28e840`
- `p2d_oracle_L07_s1000_best.pt` `c0872e01b8e5f4d2e75d9ad746ed00e3a1edc3b0b375498dc5a4804572c996af`
- `telemetry.jsonl` `0b5193ecd47fd7a123216a9380a0f93edd9273bdb12533c9ab1d4114c7303ab1`

Also: `logs/p2d_oracle_L07_s1000.log`, `logs/gate2_v6.log`, `logs/gate2_guard_v6.jsonl`,
`logs/gate2_interruptions_v6.jsonl`, `gate2_status_v6.json`. Frozen artifacts unchanged.
