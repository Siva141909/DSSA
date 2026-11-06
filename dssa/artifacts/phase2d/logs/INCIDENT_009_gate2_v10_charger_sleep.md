# INCIDENT_009: Gate 2 recovery (v10) stopped at run 6 of 29, real system sleep on battery

Date: 2026-11-04. Manifest v10 `006394f7b27b57089cc42e29c8aa91d91650c3147a5551f74712a28f6401da96` (unchanged).

## What stopped
- Run: `p2d_oracle_L20_s2000` (Layer 20, seed 2000), run 6 of 29. Started 22:33:44 IST (PID 48282).
- **Cause:** real system sleep. A lid close alone did not cause it. macOS power log:
  - 22:52:55 lid closed on AC, DarkWake ("Clamshell Sleep … Using AC"); 22:52:56 back to FullWake (HID activity).
  - 22:53:06 lid closed again on AC, so DarkWake.
  - **22:53:11 "Entering Sleep state due to 'Clamshell Sleep' … Using Batt", 288 s.** The charger was
    disconnected within about 5 s of the lid close. With the lid closed and on battery, macOS sleeps for real.
  - 22:57:59 DarkWake on battery (SMC/wifi maintenance wake).
- **Guard:**
  - 22:53:08 logged "lid closed (logged only, not a stop condition)" with state AC true. Training continued.
  - 22:57:59.55, the first poll after wake: hazard "system sleep detected (286 s suspended)", with state
    AC false and the lid closed. SIGINT sent to PID 48282.
- **Run response:** exit code −2, 0.6 s after the SIGINT. `incident.json` written: `KeyboardInterrupt()`,
  **stage `train`, optimizer step 1,508** (1,509 batches, 7 evaluations, elapsed 1,454.2 s). No SIGKILL.
- **Sequence:** stopped by rule; logged in `logs/gate2_interruptions_v10.jsonl` (`incident_written: true`).
  Runs 7–29 not started. No retry, no skip.
- Swap growth 0 MB; peak footprint 6,094 MB; pressure normal; no thermal or performance warning; no VM.

## Closed-lid observation (first real data)
Training telemetry, recorded every 0.26 s:
- **Lid closed on AC (22:53:06 to 22:53:11):** training continued at its normal rate, steps 1,490 → 1,504,
  about 2 steps/s. Telemetry did not pause, and there was no thermal warning.
- **On battery (22:53:13.24 to 22:57:59.32):** telemetry gap of 286.1 s at step 1,507. The process was
  suspended with the system, as expected for real sleep. On wake it took one step (1,508) before the
  guard's SIGINT.
- Observed lid-closed running on AC lasted only about 5 s, so it is still too short to establish
  sustained closed-lid training.

## Preserved evidence (not modified)
`runs/p2d_oracle_L20_s2000/`:
- `IN_PROGRESS` `87e3ecd2fedf9fe85654fe6f23a082d6342b2b243700180fd5afbc2fb7a11f01`
- `incident.json` `a9e06a48a7d6d179b08ee378651ce08d156b902a8ee305eaaa215cf5c5680c15`
- `p2d_oracle_L20_s2000_best.pt` `6a374c618fc4088bf3b8f425489727a320b6909cd710b3abd2ef044e56c804b7`
- `telemetry.jsonl` `1f9a8fc8a9b94688bddead0d9c9aeab1239827c5aabee007c894749fb4ded7b7`

Logs:
- `logs/gate2_guard_v10.jsonl` `2f07d2ae8b52067bc2f05a2cb080fccd9c5bbdb425297db5199424009442a326`
- `logs/gate2_interruptions_v10.jsonl` `6a786b7ac619abae72fde43a42c8abd9f934b4f61c4f21afb319854cc26220d1`
- `logs/gate2_v10.log` `9d0b703af4a94559c0f18ebbadee3917a9617ecec0bf2f46f03e62fef1bf6053`
- `logs/p2d_oracle_L20_s2000.log` `07f4fb36c64df12e3f1534d75fe84c189f59edc9830d2c29ccbf13aced017b18`
- `gate2_status_v10.json` `6939e8043095a5745a58ae2ee6cc620c6deb601b9cc15b34f9abc8d0cbe865cd`

## Checks after the stop
v10 runs 1–5 completed, and each passes the result-hash, checkpoint-hash and reload checks with swap growth 0 MB:

| Run | U6 | U5 |
|---|---|---|
| L15 s2000 `_a2` | +0.0361 | +0.0247 |
| L16 s2000 | +0.0391 | +0.0263 |
| L17 s2000 | +0.0290 | +0.0199 |
| L18 s2000 | +0.0274 | +0.0279 |
| L19 s2000 | +0.0405 | +0.0295 |

- **Gate 2 total: 39 of 63 completed.**
  - s1000: 21/21.
  - s2000: 18/21 (Layers 1–11 and 13–19); remaining L20 (needs a new ID), L21, L22.
  - s3000: 0/21.
  - Remaining: 24 runs.
- Frozen artifacts and manifest v10 unchanged. No sequence or run process remains.
- The charger was reconnected at 23:10:40 (100% charge).
- Continuing requires a v11 manifest (L20 s2000 → `p2d_oracle_L20_s2000_a2`) and explicit approval.
