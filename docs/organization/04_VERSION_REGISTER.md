# Historical version register

All paths are relative to `~/Documents/Major project/`. Every version listed here is preserved at
its original path. Nothing was renamed, merged or deleted.

**Why these files stay together in `dssa/phase2d/`:**
- `common.code_hash()` hashes every `*.py` and `*.md` file in `dssa/phase2d/`.
- Manifests v1–v12 record that hash.
- Moving historical versions into a subfolder, or adding any file there, would break the
  reproducibility check.

**Versions are execution wrappers, not new protocols.** One experimental protocol applies
throughout: Phase 2B-B training via `dssa/train/train.py`, unchanged; the Phase 2D addenda; and the
Gate 2 design of 21 layers × 3 seeds.
- Every `run_one_vN.py` from v3 onward is a few lines that point the **same** training runner,
  `run_one_v2.main`, at a different manifest.
- Every `run_gate2_vN.py` from v5 onward is the same sequence runner with operational safety
  changes.
- No training setting, seed, data stream or analysis definition changes between versions. Each
  `gate_vN.py` verifies this field by field before writing its manifest.

## 1. Version series and counts
| Series | Versions present | Count | Latest (active) |
|---|---|---|---|
| Training entry point `run_one*.py` | `run_one.py`, `run_one_v2.py` … `run_one_v12.py` | 12 | `run_one_v12.py` (wraps `run_one_v2.main`) |
| Sequence runner, pilot | `run_pilot.py`, `run_pilot_v3.py` | 2 | `run_pilot_v3.py` (pilot complete) |
| Sequence runner, Gate 2 | `run_gate2.py` (v4), `run_gate2_v5.py` … `run_gate2_v12.py` | 9 | `run_gate2_v12.py` |
| Manifest writer | `gate0_setup.py` (v1), `gate_v2.py`, `gate_v3.py`, `gate2_setup.py` (v4), `gate_v5.py` … `gate_v12.py` | 12 | `gate_v12.py` |
| Gate 2 analysis | `gate2_analysis.py` (frozen) + mapping wrappers `gate2_analysis_v5.py` … `_v12.py` | 1 + 8 | `gate2_analysis_v12.py` (produced the final result) |
| Pilot analysis | `pilot_analysis.py` (frozen) + `pilot_analysis_v3.py` | 2 | `pilot_analysis_v3.py` |
| Reload verification | `verify_reload.py`, `verify_reload_v8.py` | 2 | `verify_reload_v8.py` (wraps `verify_reload.main`) |
| Manifests | pilot v1, v2 draft, v2, v3; Gate 2 v4 … v12; v10 superseded draft | 14 files | `manifest_gate2_recovery_v12.json` |
| Addenda | `PHASE2D_ADDENDUM.md`, `PHASE2D_ADDENDUM_V2.md` | 2 | both in force (V2 adds to the first) |

There are **12 manifest versions** (v1–v12) plus 2 unused drafts. Version numbers are shared across
manifests, entry points, runners and writers. For example, `run_gate2_v9.py` executes
`manifest_gate2_recovery_v9.json` through `run_one_v9.py`.

## 2. Manifest and execution chain
In the table below:
- **Runs** is the number of runs in the manifest.
- **Done** is the number completed under that version.
- Paths are under `dssa/artifacts/phase2d/` and `dssa/phase2d/`.

| Ver | Manifest (SHA-256 prefix) | Runs | Writer | Sequence runner → entry → reload | Done | Ended by | What changed |
|---|---|---|---|---|---|---|---|
| v1 | `manifest_pilot.json` (5437ef3a) | 12 | `gate0_setup.py manifest` | `run_pilot.py` → `run_one.py` → `verify_reload.py` | 1 (K0 s1000) | INCIDENT_001: swap stop at L00 s1000 | Original pilot |
| (draft) | `manifest_pilot_v2_draft_unused_bug.json` (d4e9019a) | 1 | `gate_v2.py` | never executed | 0 | — | Unused draft. The defect is recorded only in its file name ("unused_bug"); no other document describes it. Replaced by v2 |
| v2 | `manifest_pilot_v2.json` (db5bac36) | 1 | `gate_v2.py manifest` | `run_one_v2.py` (direct) | 1 (L00 s1000 `_a3`) | complete | 8-bit training cache (`dataset_u8.py`, bit-exact equivalence gate), telemetry, `incident.json`. INCIDENT_002 was the L0 retry before it |
| v3 | `manifest_pilot_v3.json` (3099ca82) | 10 | `gate_v3.py` | `run_pilot_v3.py` → `run_one_v3.py` → `verify_reload.py` | 10 | complete | Remaining 10 pilot runs; `pilot_analysis_v3.py` maps L00 to `_a3` |
| v4 | `manifest_gate2_v4.json` (b855b972) | 63 | `gate2_setup.py` | `run_gate2.py` → `run_one_v4.py` → `verify_reload.py` | 1 | INCIDENT_003: runtime stop after system sleep (L02 s1000) | Gate 2 design: 21 layers × 3 seeds |
| v5 | `manifest_gate2_recovery_v5.json` (d4cfcb74) | 62 | `gate_v5.py` | `run_gate2_v5.py` → `run_one_v5.py` | 4 | INCIDENT_004: swap growth (Docker VM), L06 s1000 | Preflight and guard (AC, lid, thermal, pressure); first `_a2` rerun |
| v6 | `manifest_gate2_recovery_v6.json` (b4e852aa) | 58 | `gate_v6.py` | `run_gate2_v6.py` → `run_one_v6.py` | 1 | INCIDENT_005: swap growth, L07 s1000 | VM preflight check; interruption log |
| v7 | `manifest_gate2_recovery_v7.json` (a4a19944) | 57 | `gate_v7.py` | `run_gate2_v7.py` → `run_one_v7.py` | 16 | INCIDENT_006: charger, L02 s2000; SIGINT-ignored defect found | VM check advisory only |
| v8 | `manifest_gate2_recovery_v8.json` (fbb9dc0f) | 41 | `gate_v8.py` | `run_gate2_v8.py` → `run_one_v8.py` → `verify_reload_v8.py` | 2 | INCIDENT_007: lid closed, L04 s2000 | `sigsafe.py`: signal handling repaired |
| v9 | `manifest_gate2_recovery_v9.json` (7e77b72c) | 39 | `gate_v9.py` | `run_gate2_v9.py` → `run_one_v9.py` → `verify_reload_v8.py` | 10 | INCIDENT_008: lid closed, L15 s2000 | Names and count only |
| (draft) | `manifest_gate2_recovery_v10__superseded_lid_stop.json` (e954ce72) | 29 | `gate_v10.py` (earlier draft) | never launched | 0 | — | Kept the lid stop; superseded before approval |
| v10 | `manifest_gate2_recovery_v10.json` (006394f7) | 29 | `gate_v10.py` | `run_gate2_v10.py` → `run_one_v10.py` → `verify_reload_v8.py` | 5 | INCIDENT_009: real sleep on battery, L20 s2000 | Closed lid is advisory; telemetry (60 s) and optimizer-step (300 s) watchdogs |
| v11 | `manifest_gate2_recovery_v11.json` (7c60dee4) | 24 | `gate_v11.py` | `run_gate2_v11.py` → `run_one_v11.py` → `verify_reload_v8.py` | 7 | INCIDENT_010: real sleep on battery, L05 s3000 | Names and count only |
| **v12** | **`manifest_gate2_recovery_v12.json` (a6949527)** | 17 | `gate_v12.py` | `run_gate2_v12.py` → `run_one_v12.py` → `verify_reload_v8.py` | **17** | **complete** | Names and count only |

**Gate 2 completions:** 1 + 4 + 1 + 16 + 2 + 10 + 5 + 7 + 17 = **63**.
**Pilot completions:** 1 + 1 + 10 = **12**.
**Total:** 75 completed runs, every one read by the final analysis.

## 3. Analysis versions
- `gate2_analysis.py`: frozen before any Gate 2 training. Its definitions are never edited.
- `gate2_analysis_vN.py`: a wrapper that only changes `rid()`, so that each interrupted
  (layer, seed) is read from its `_a2` rerun.

| Wrapper | Mappings |
|---|---|
| v5 | L02 s1000 |
| v6 | + L06 s1000 |
| v7 | + L07 s1000 |
| v8 | + L02 s2000 |
| v9 | + L04 s2000 |
| v10 | + L15 s2000 |
| v11 | + L20 s2000 |
| **v12** | + L05 s3000 (8 mappings) |

- The final result `dssa/artifacts/phase2d/gate2/gate2_analysis.json` was produced by
  **`gate2_analysis_v12.py`** on 2026-11-05.
- The base `rid()` also maps L00 s1000 to the pilot's `p2d_oracle_L00_s1000_a3`.

## 4. Interrupted and aborted run folders (preserved; no results)
| Folder (`dssa/artifacts/phase2d/runs/`) | Replaced by | Record |
|---|---|---|
| `p2d_oracle_L00_s1000__ABORTED_attempt1_swapstop` | `p2d_oracle_L00_s1000_a3` | INCIDENT_001 |
| `p2d_oracle_L00_s1000` | `p2d_oracle_L00_s1000_a3` | INCIDENT_002 |
| `p2d_oracle_L02_s1000` | `_a2` | INCIDENT_003 |
| `p2d_oracle_L06_s1000` | `_a2` | INCIDENT_004 |
| `p2d_oracle_L07_s1000` | `_a2` | INCIDENT_005 |
| `p2d_oracle_L02_s2000` | `_a2` | INCIDENT_006 (killed; no `incident.json`) |
| `p2d_oracle_L04_s2000` | `_a2` | INCIDENT_007 |
| `p2d_oracle_L15_s2000` | `_a2` | INCIDENT_008 |
| `p2d_oracle_L20_s2000` | `_a2` | INCIDENT_009 |
| `p2d_oracle_L05_s3000` | `_a2` | INCIDENT_010 |

The hashes of the Gate 2 partial folders are recorded in `manifest_gate2_recovery_v12.json` under
`preserved_interrupted_runs`.

## 5. Status, guard and log files per version
For each version *N*:

| Kind | Location (under `dssa/artifacts/phase2d/`) | Versions |
|---|---|---|
| Status | `gate2_status_vN.json` | v4–v12 |
| Pilot status | `pilot_status.json`, `pilot_status_v3.json` | pilot |
| Sequence log | `logs/gate2_vN.log` | v4–v12 |
| Pilot sequence log | `logs/pilot.log`, `logs/pilot_v3.log` | pilot |
| Guard log | `logs/gate2_guard_vN.jsonl` | v5–v12 |
| Interruption log | `logs/gate2_interruptions_vN.jsonl` | v6–v11 (v12 had none) |
| Per-run log | `logs/<run_id>.log` | all runs |

Audits, launch records and test evidence are in `dssa/artifacts/phase2d/gate2/`:
- `GATE2_V*_AUDIT.md` and `_LAUNCH.md`
- `recovery_vN_audit.json`
- `vN_signal*_tests/`

## 6. Phase 2C and earlier code (single versions, frozen by hash)
- `dssa/train/*.py`: Phase 2B-B/2C training code. Hashed in every Phase 2D manifest
  (`train_and_sanity_code_hash`).
- `dssa/sanity/*.py`: sanity checks and DSS extraction for Phases 1 to 2B-A. Also hashed in the
  Phase 2D manifests.

Neither folder has versioned copies. The Phase 2C batch-1 results are in
`dssa/artifacts/phase2c/` (5 of the planned 39 runs). They are frozen evidence, checked by
`common.assert_frozen_unchanged()`.
