# Gate 2 recovery v6 plan (awaiting research-lead approval)

Date: 2026-11-03. No training has started.

## Manifest
- `manifest_gate2_recovery_v6.json`, SHA-256
  `b4e852aaf9409b8e0bc9541b82a18f66e40bb5ab7f1113835cdefe3a572b428c`.
- 58 runs in v5 order, estimated 30.3 h:
  - first, the Layer 6 seed 1000 rerun, `p2d_oracle_L06_s1000_a2` (rerun_of `p2d_oracle_L06_s1000`)
  - then the 57 pending runs: s1000 L07–L11 and L13–L22; s2000 and s3000 each L01–L11 and L13–L22
- Every training field is copied from v5 and checked equal. Only the run ID, phase
  label and config hash differ. Manifests v1–v5 are unchanged.
- Analysis: `gate2_analysis_v6.py`, the frozen analysis with Layers 2 and 6 at seed 1000
  mapped to their `_a2` reruns.

## Inventory verified by `gate_v6.py` before writing
- Completed and kept, never rerun: L01, L02 (`_a2`), L03, L04 and L05 at seed 1000, plus
  the 12 pilot runs. They pass the result-hash, checkpoint-hash and reload checks.
- Preserved partial folders, unchanged: `p2d_oracle_L02_s1000` and `p2d_oracle_L06_s1000`,
  with four file hashes each.
- INCIDENT_003, INCIDENT_004 and both partial-results reports are recorded.
- Frozen artifacts and the data-stream replay are unchanged.

## Safety (all limits unchanged, including 512 MB swap growth)
- **Preflight before every run:**
  - AC power
  - lid open
  - no thermal or performance warning
  - memory pressure normal
  - at least 10 GB free
  - required files local
  - no other run
  - **new:** no virtual machine (Docker) running
- **Guard during every run:** sleep, charger, lid, thermal and memory pressure.
  - The guard stops on a sleep gap over 30 s or 2 polls without AC.
  - The manual stop is unchanged.
- **New interruption log:** every stop is written to `logs/gate2_interruptions_v6.jsonl` with
  its exact cause, error, stage and step, in addition to `incident.json` and the guard log.
- **Closing, unplugging or moving the Mac:**
  - The current run stops safely and is preserved with its incident record.
  - The sequence stops; there is no automatic retry, resume or skip.
  - To resume once the machine is stable, a new manifest version gives the
    interrupted run a new ID; it needs explicit approval.
  - A closed lid suspends the Mac at once, so the guard records the stop on the next wake.

## Launch command (only after approval)
```
cd "/Users/siva/Documents/Major project/dssa/phase2d"
nohup caffeinate -dims ../venv/bin/python -B run_gate2_v6.py > ../artifacts/phase2d/logs/gate2_v6.log 2>&1 &
```
