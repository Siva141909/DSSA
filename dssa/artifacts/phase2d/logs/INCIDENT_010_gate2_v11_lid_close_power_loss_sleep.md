# INCIDENT_010: Gate 2 recovery (v11) stopped at run 8 of 24, real system sleep on battery

Date: 2026-11-05. Manifest v11 `7c60dee4490ef828a33b0fe54df500375b513a063b0df211ce6e7e765ae77538` (unchanged).

## What stopped
- **Run:** `p2d_oracle_L05_s3000` (Layer 5, seed 3000), run 8 of 24. Started 03:10:53 IST (PID 64605).
- **Cause:** real system sleep on battery, the same sequence as INCIDENT_009. From the macOS power log:
  - **03:12:37** the lid closed while on AC. The Mac entered DarkWake ("Clamshell Sleep … Using AC"),
    and the sequence's caffeinate assertion was active.
  - **03:12:40** the power-source summary changes to **"Using Batt"**, 3 s after the lid close.
  - **03:12:42** "Entering Sleep state due to 'Clamshell Sleep' … Using Batt", lasting 938 s.
  - The Mac then cycled between maintenance DarkWakes and sleep on battery until **13:19:20**. At that
    point "Using AC" returned, with the PowerChime `chimeOnAttach` (charger attach) assertion.
- **Guard:**
  - The guard's first poll after the first DarkWake was at 03:28:20.9.
  - It logged "lid closed (logged only, not a stop condition)" and hazard **"system sleep detected
    (937 s suspended)"**, with state AC false, the lid closed and no thermal warning. It sent SIGINT to
    PID 64605.
- **Run response:**
  - Exit code −2, 0.38 s after the SIGINT. No SIGKILL.
  - `incident.json` written: `KeyboardInterrupt()`, **stage `train`, optimizer step 152** (153
    batches, 0 evaluations, elapsed 1,046.3 s).
  - The run stopped before the first evaluation (step 200), so **there is no checkpoint**.
- **Sequence:**
  - Stopped by rule, and logged in `logs/gate2_interruptions_v11.jsonl` (`incident_written: true`).
  - Runs 9–24 were not started. No retry, no skip.
- **Resources:** swap growth 0 MB; maximum physical footprint 5,749 MB; memory pressure ≤ 1.

## Telemetry
- Training ran at its normal rate up to 03:12:43.88 (step 152). That includes the roughly 6 s of
  DarkWake with the lid closed and the 3 s after the power source changed.
- The next record is at 03:28:20.81: a **936.9 s gap**, during which the process was suspended with
  the system.

## Power-source finding (both v10 and v11 stops)
| | Lid close (DarkWake, on AC) | "Using Batt" | Real sleep | Charger re-attached |
|---|---|---|---|---|
| INCIDENT_009 | 2026-11-04 22:53:06 | 22:53:11 | 22:53:11 | 23:10:40 (`chimeOnAttach`) |
| INCIDENT_010 | 2026-11-05 03:12:37 | 03:12:40 | 03:12:42 | 13:19:20 (`chimeOnAttach`) |

- Both times, external power was lost **3–5 s after the lid closed**. Power came back only with an
  attach event, so macOS treated the charger as disconnected rather than as paused charging.
- **No battery-management or charge-limiting software is installed.**
- **Adapter:** Apple 70 W USB-C (68 W negotiated). It is currently connected and charging.
- **The logs cannot distinguish** a physical unplug from the cable or connection dropping power when
  the lid closes.
- The one closed-lid period that stayed on AC (2026-11-04 22:52:55) lasted 1 s.

## Preserved evidence (not modified)
`runs/p2d_oracle_L05_s3000/`:
- `IN_PROGRESS` `04dcd68083e88131b5037b3990d6566c24fe603cc8969680add7c145d3d9024f`
- `incident.json` `826d780fb9c5d3f9293a1a940a1dc096edd985b31e9f0d83a19a68b5a53c08b0`
- `telemetry.jsonl` `abe6082f48fb5f46c2d8bf90f34df6ef24c3f453b81d21ff7873d6f6f88e67bc`
- (No checkpoint; the stop came before the first evaluation.)

Logs:
- `logs/gate2_guard_v11.jsonl` `07f49e39e0e37097a6dd8fe54b4b25a96bf5d1da921866d2a90b8be07058253a`
- `logs/gate2_interruptions_v11.jsonl` `c6146ebbea5b4ce8b8a78861bc3a8dee38f8a43f8a62300403149ee61d4cc2f8`
- `logs/gate2_v11.log` `c58a0360b1b0dc696cb33fbd0c32aedc8993bf76425bb6e9ce4c5348856a1c58`
- `logs/p2d_oracle_L05_s3000.log` `4b988c0b5f966614f8387876061cc5ca94069b84e2c963340ea2166b2dac0749`
- `gate2_status_v11.json` `f10512cee53ba1706b4dcbc4c5eeaf2e4fd5858f8817ea88978c9067efa3a1c6`

## Checks after the stop
v11 runs 1–7 completed. Each passes the result-hash, checkpoint-hash and reload checks, with swap
growth 0 MB:

| Run | U6 | U5 | Peak footprint |
|---|---|---|---|
| L20 s2000 `_a2` | +0.0344 | +0.0345 | 6,092 MB |
| L21 s2000 | +0.0256 | +0.0249 | 5,654 MB |
| L22 s2000 | +0.0255 | +0.0294 | 5,618 MB |
| L01 s3000 | +0.0215 | +0.0072 | 8,098 MB |
| L02 s3000 | +0.0273 | +0.0150 | 8,055 MB |
| L03 s3000 | +0.0177 | +0.0092 | 8,084 MB |
| L04 s3000 | +0.0425 | +0.0281 | 8,077 MB |

- **Gate 2 total: 46 of 63 completed.**
  - s1000: 21/21.
  - s2000: 21/21.
  - s3000: 4/21 (Layers 1–4).
- **Remaining: 17 runs.** L05 s3000 needs a new ID; then Layers 6–11 and 13–22.
- Frozen artifacts and manifest v11 are unchanged. No sequence or run process remains.
- Continuing requires a v12 manifest (L05 s3000 → `p2d_oracle_L05_s3000_a2`) and explicit approval.
