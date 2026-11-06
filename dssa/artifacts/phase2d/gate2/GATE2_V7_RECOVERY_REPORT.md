# Gate 2 recovery v7: manifest and audit (awaiting research-lead approval)

Date: 2026-11-03, 23:27 IST. Prepared and audited only. No training has started.

## Manifest
- `manifest_gate2_recovery_v7.json`, SHA-256
  **`a4a19944816713cd938fefb475894f1980af44f89df7552bce2f90579f8b3e56`**
- 57 runs, estimated **29.7 h**.
- Analysis: `gate2_analysis_v7.py`, the frozen analysis with Layers 2, 6 and 7 at seed 1000
  read from their `_a2` reruns.

## Run counts (Gate 2, 63 authorized)
| Status | Count | Runs |
|---|---|---|
| Completed, kept, not rerun | 6 | L01, L02 (`_a2`), L03, L04, L05, L06 (`_a2`); all seed 1000 |
| Failed, partial folder preserved | 3 | `p2d_oracle_L02_s1000`, `p2d_oracle_L06_s1000`, `p2d_oracle_L07_s1000` |
| In v7 | 57 | 1 rerun (`p2d_oracle_L07_s1000_a2`) + 56 never started |

6 completed + 57 in v7 = 63.

## 57-run inventory (in order)
| # | Seed | Layers | Run IDs |
|---|---|---|---|
| 1 | 1000 | 7 | `p2d_oracle_L07_s1000_a2` (rerun_of `p2d_oracle_L07_s1000`) |
| 2–15 | 1000 | 8–11, 13–22 | `p2d_oracle_L08_s1000` … `p2d_oracle_L22_s1000` |
| 16–36 | 2000 | 1–11, 13–22 | `p2d_oracle_L01_s2000` … `p2d_oracle_L22_s2000` |
| 37–57 | 3000 | 1–11, 13–22 | `p2d_oracle_L01_s3000` … `p2d_oracle_L22_s3000` |

Layer 12 (pilot), Layer 0 and Layer 23 are pilot runs and are not in Gate 2.

## Manifest audit
- 57 run IDs, all unique; no run folder exists for any of them.
- No completed run appears in v7.
- The order equals v6's with the completed runs removed.
- Every training field matches v6: K, layer, seed, LoRA seed, condition labels, protocol,
  addendum, rankings, equivalence and cache hashes, runtime estimate. Only the run ID,
  phase label and config hash differ.
- All 57 config hashes are valid. The code hash (37 files) matches the current code.
- Fingerprints, probe hash, per-seed expectations and pilot records are identical to v6.
- Limits are unchanged: footprint 11,776 MB, **swap growth 512 MB**, runtime 1.5×,
  stop at critical pressure.

## Integrity
- Manifests v1–v6 unchanged (v6 `b4e852aa…`, v5 `d4cfcb74…`, v4 `b855b972…`, v3 `3099ca82…`,
  v2 `db5bac36…`, v1 `5437ef3a…`).
- The six completed runs and the 12 pilot runs pass: status, 2,000 steps, result hash,
  checkpoint hashes, reload difference 0.
- Partial folders unchanged: Layer 2 and Layer 6 match their recorded hashes; Layer 7 matches
  the four hashes in INCIDENT_005 (now recorded in v7).
- INCIDENT_003 and INCIDENT_004 match their recorded hashes; INCIDENT_005 is recorded.
- Frozen artifacts unchanged. Data-stream replay for seeds 1000/2000/3000 matches.

## Safety (unchanged except the advisory VM check)
- Preflight before each run: AC, lid open, no thermal or performance warning, pressure
  normal, ≥10 GB free, files local, no other run. PASS at 23:27.
- Guard during each run: sleep, charger, lid, thermal, critical pressure. Runner limits and
  the manual stop are unchanged.
- Docker or a virtual machine running is **logged before each run, not a stop condition**,
  as instructed. Built into `run_gate2_v7.py`, so no separate launcher is needed.
- Every stop is recorded in `logs/gate2_interruptions_v7.jsonl` with its cause, stage and step.

## Docker and memory findings
- At 23:27:30 IST: no Docker Desktop and no virtual machine running. The only Docker
  process is the root network helper `com.docker.vmnetd` (4 MB, running since boot).
  Swap used 800 MB of 2,048 MB; memory pressure normal. Recorded in `gate2/recovery_v7_audit.json`.
- Docker Desktop's "start at login" (`AutoStart`) is **false**, and it is not a login item.
  Login auto-start is not the cause, so disabling it would not help.
- Docker's own log shows three launches today, all non-login, `reason: open-tray`:
  17:15:34, 19:06:07 and 22:36:26 IST.
- Each matches an `open -a Docker` command from another Claude Code session working in
  `~/Documents/Ecosystem` (session `0d312ac2…`), at 17:15:30, 19:06:04 and 22:36:23 IST.
  It starts Docker to run Postgres-backed tests.
- The two swap stops (Layer 6 at 17:17, Layer 7 at 19:07) each began 35–110 s after
  one of these launches. The virtual machine uses 0.8–1 GB.
- Run 1 of v6 also completed with 209 MB of swap growth, without Docker running.
  The margin under 512 MB is therefore smaller than in the v5 runs (0 MB).

## Recommendation (no settings changed)
- During the run, don't use the Ecosystem Claude session, or anything else that starts Docker.
  Closing that session, or telling it not to run `open -a Docker`, removes the observed cause.
- Disabling "Open Docker Desktop at login" is not needed: it is already off.

## Launch command (only after approval)
```
cd "/Users/siva/Documents/Major project/dssa/phase2d"
nohup caffeinate -dims ../venv/bin/python -B run_gate2_v7.py > ../artifacts/phase2d/logs/gate2_v7.log 2>&1 &
```
