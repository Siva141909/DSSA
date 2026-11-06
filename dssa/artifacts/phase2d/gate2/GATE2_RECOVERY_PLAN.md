# Gate 2 recovery plan (awaiting research-lead approval)

Date: 2026-11-03. No training has started.

## 1. Run identities
- Layer 2 seed 1000 rerun: **`p2d_oracle_L02_s1000_a2`**. This follows the pilot's
  `p2d_oracle_L00_s1000_a3` convention.
- Preserved and never reused: `p2d_oracle_L02_s1000` (interrupted, with incident) and
  `p2d_oracle_L01_s1000` (completed).

## 2. Manifest
- `manifest_gate2_recovery_v5.json`, SHA-256
  `d4cfcb74fd298aa468dc4d3949a739255d32db3b1917a5860b175ddd332341d4`.
- 62 runs in v4 order: the Layer 2 rerun first, then the 61 pending runs. That is
  Layers 3–11 and 13–22 for seed 1000, then Layers 1–11 and 13–22 for seed 2000,
  then the same for seed 3000. The estimate is 32.7 h.
- Every training field is copied from v4 and checked equal: K, layer, seed, LoRA
  seed, condition label, protocol, addendum, rankings, equivalence hash, cache and
  runtime estimate. Only the run ID, phase label and config hash differ.
- v1–v4 are unchanged: v4 `b855b972…`, v3 `3099ca82…`, v2 `db5bac36…`, v1 `5437ef3a…`.
- Analysis: `gate2_analysis_v5.py` is the frozen `gate2_analysis.py` with one change:
  Layer 2 seed 1000 is read from the `_a2` run.

## 3. Verified before writing v5
- **Layer 1 seed 1000:** completed, 2,000 steps. Best checkpoint `8078eca0…`, final
  `fc255773…`, result `8272b839…`. Hashes and reload check (0 differences) pass.
- **Layer 2 seed 1000 partial folder**, unchanged and recorded in v5. It holds exactly:
  - `IN_PROGRESS` `612a4d8b…`
  - `incident.json` `3c3f2e5e…`
  - `p2d_oracle_L02_s1000_best.pt` `cf24e1f1…`
  - `telemetry.jsonl` `b0c539b0…`
- **Reports:** `INCIDENT_003` `ab2fdd37…` and `GATE2_PARTIAL_RESULTS.md` `8f5b41ea…`.
- **Pilot:** all 12 pilot runs re-verified.
- **Frozen artifacts:** unchanged. Data-stream replay for all three seeds matches.
- **Code:** the current code hash equals v5's (29 files) and all 62 config hashes are valid.

## 4. Preflight checklist (automatic before every run; a failure stops the sequence before the run starts)
- [ ] Charger connected (AC power)
- [ ] Lid open
- [ ] No thermal or performance warning recorded
- [ ] Memory pressure normal
- [ ] At least 10 GB free disk
- [ ] Training/validation tiles, label zip, backbone and all code present locally (not cloud-only)
- [ ] No other Phase 2D run active

Manual, before launch:
- [ ] The Mac is on a hard, open surface, not enclosed, with ventilation clear
- [ ] Heavy apps are closed, such as browser tabs and Docker
- [ ] No travel planned for about 33 h

Run `venv/bin/python -B phase2d/run_gate2_v5.py --check` to test the checklist at any
time. It passed at 2026-11-03 14:41.

## 5. Safe stop if the Mac sleeps or overheats
A guard in the sequence process polls every 5 s during every run and reload check. On any of
the following it sends SIGINT to the run:
- system sleep: wall clock against `CLOCK_UPTIME_RAW` shows more than 30 s suspended
- charger disconnected for two consecutive polls
- lid closed
- a thermal or performance warning recorded
- critical memory pressure

What happens then:
- The run writes `incident.json` with the exact step and stage.
- The guard records the event in `logs/gate2_guard_v5.jsonl`.
- The sequence stops. There is no retry or skip, and all evidence is kept.
- If the run has not exited within 180 s, it is killed, and the kill is logged.

Caveats:
- A closed lid suspends the Mac at once, so the guard acts at the next wake.
- The existing limits are unchanged: 11.5 GB footprint, 512 MB swap growth, 1.5x runtime,
  critical pressure.

Manual stop for the operator:
- `pkill -INT -f run_one_v5.py` interrupts the current run and writes its incident record.
- The sequence then stops by rule.
- Never close the lid to stop a run.

Tests run (dummy `/bin/sleep` children, no training):
- A normal child: no stop.
- A simulated lid-closed hazard: stopped in 1.1 s.
- A simulated 100 s sleep: stopped in 2.1 s.

Not tested: a SIGINT to a real training run. Its handling relies on the existing
runner's catch-all exception handler, which writes `incident.json`.

## 6. Launch command (only after approval)
```
cd "/Users/siva/Documents/Major project/dssa/phase2d"
nohup caffeinate -dims ../venv/bin/python -B run_gate2_v5.py > ../artifacts/phase2d/logs/gate2_v5.log 2>&1 &
```
