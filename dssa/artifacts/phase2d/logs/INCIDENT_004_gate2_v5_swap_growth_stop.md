# INCIDENT_004: Gate 2 recovery (v5) stopped at run 5 of 62, swap growth limit

Date: 2026-11-03. Manifest v5 `d4cfcb74fd298aa468dc4d3949a739255d32db3b1917a5860b175ddd332341d4`.

## What stopped
- Run: `p2d_oracle_L06_s1000` (Layer 6, seed 1000), run 5 of 62.
- Started 17:11:32 IST; stopped 17:17:34 IST (elapsed 361.5 s).
- Stop condition: `RuntimeError('STOP: swap growth 513 MB above limit')` (limit 512 MB),
  raised by the runner's own monitor, not by the v5 safety guard.
- **Failure stage:** `validation`, at optimizer step 400 (400 batches drawn), evaluations
  completed 1. Raised inside `run_training -> evaluate -> p_eval -> tick`.
- Sequence: stopped by rule (`gate2_status_v5.json` state `stopped`). No retry, no skip.
  Runs 6–62 were not started.

## Telemetry
- Preflight before the run passed all seven checks: AC, lid open, no thermal warning,
  pressure normal (1), 186.8 GB free, files local, no other run.
- System swap at run start: 395 MB. At stop: 908 MB.
- Swap growth was 0 through training (step 0–399). It rose from 64 MB to 521 MB within
  about 10 s after validation began (elapsed 349–359 s).
- The training process was not growing: footprint 5.56–5.57 GB during the rise, lifetime
  peak 7.10 GB (limit 11.5 GB). Memory pressure was 2 (warning) from about 240 s; earlier
  v5 runs also reached pressure 2 with 0 swap growth.
- AC power, lid open and no thermal warning throughout; the guard logged no hazard.

## Likely cause (correlation, not proven)
Docker Desktop and its virtual machine (`com.apple.Virtualization.VirtualMachine`, about
1 GB resident) started at about 17:15:33 IST, during this run and roughly 2 minutes before
swap began rising. Other new processes at the time: a second Claude Code session. The
manual pre-launch checklist asked for Docker to be closed; it was not running at launch.
How Docker was started cannot be determined from the evidence here.

## Preserved evidence (not modified)
`runs/p2d_oracle_L06_s1000/`:
- `IN_PROGRESS` `5deab8babbfbb89759b92ae12a44195f1d9ca9212e754f94fa33243c02338ae4`
- `incident.json` `73cec8dea26b1124a1a299f08d8aab1865573c7f77967e8bfc2a37819e9a9646`
- `p2d_oracle_L06_s1000_best.pt` `b417d855c83436b605e824b21eab79be0e2165687cc4e2de6b701c004bebb98e`
- `telemetry.jsonl` `e5ebaf661e76caac4331b42510c4c4fe56f16d2388a336cc901d2d0d5ec5d2cd`

Also: `logs/p2d_oracle_L06_s1000.log`, `logs/gate2_v5.log`, `logs/gate2_guard_v5.jsonl`,
`gate2_status_v5.json`.

## Checks after the stop
- The four completed v5 runs pass every frozen-analysis integrity check (status, 2,000
  steps, last evaluation at 2000, layer, seed, decoder and RNG hashes, backbone
  fingerprint, data stream, allowed tiles only, result and checkpoint hashes, reload
  difference 0).
- Frozen artifacts unchanged. Manifests v4 and v5 unchanged. The preserved Layer 2
  partial folder still matches its four recorded hashes.
- No process from the sequence remains.
