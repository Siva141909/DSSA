# `dssa/`: code, configuration, evidence and data

Every path here is fixed. Code imports by relative path, and the manifests and frozen-artifact
checks record hashes by path (see `../docs/organization/08_UNRESOLVED_PATH_DEPENDENCIES.md`). Do
not move or rename anything.

## Phases and where they live
| Phase | What happened | Code | Evidence | Report |
|---|---|---|---|---|
| 1/1B | Sanity checks: pipeline and backbone | `sanity/run_sanity_check.py`, `run_real_data_sanity.py`, `configs/sanity_config.yaml` | `artifacts/sanity_metrics.json`, `real_data_sanity_*` | `reports/DSSA_SANITY_EXECUTION_REPORT.md` |
| Data | Dataset integrity | `sanity/` | `artifacts/dataset_integrity_raw.json` | `reports/DSSA_DATASET_INTEGRITY_REPORT.md` |
| 2A | DSS mechanism validation | `sanity/run_phase2a_dss.py`, `mmd.py` | `artifacts/dss/phase2a_*` | `reports/DSSA_PHASE2A_DSS_VALIDATION_REPORT.md` |
| 2B-A | Locked split, final DSS, K sweep | `sanity/run_phase2b_final_dss.py`, `run_repeatability_check.py` | `artifacts/splits/`, `artifacts/dss/phase2b_*` (frozen) | `reports/DSSA_PHASE2B_A_FINAL_SPLIT_KSWEEP_REPORT.md` |
| 2B-B | Training and evaluation protocol freeze | — | `config/phase2b_training_protocol.json` (frozen), `artifacts/phase2b_b_protocol_audit.md` | `../DSSA_PHASE2B_B_TRAINING_PROTOCOL_FREEZE.md`, `reports/DSSA_PHASE2B_PREFLIGHT_REPORT.md` |
| 2C | Training infrastructure; first batch of 5 runs (K0 and four K2 selectors) of the frozen 39-run matrix | `train/*.py` (frozen by hash) | `artifacts/phase2c/` (frozen) | `reports/DSSA_PHASE2C_PREFLIGHT_REPORT.md` |
| 2D Gate 0 | Selector rankings frozen; baseline hashes | `phase2d/gate0_dss.py`, `gate0_setup.py` | `artifacts/phase2d/gate0/` | `phase2d/PHASE2D_ADDENDUM*.md` |
| 2D pilot | 12 runs: K0, L0, L12, L23 × 3 seeds | `phase2d/run_pilot*.py`, `run_one*.py`, `pilot_analysis*.py` | `artifacts/phase2d/runs/`, `pilot_*.json` | `artifacts/phase2d/gate2/PILOT_STATISTICAL_AUDIT.md` |
| **2D Gate 2** | **63 single-layer oracle runs (21 layers × 3 seeds)** | `phase2d/run_gate2*.py`, `gate*_v*.py`, `gate2_analysis*.py` | `artifacts/phase2d/` | **`artifacts/phase2d/gate2/GATE2_FINAL_REPORT.md`** |

## Folders
| Folder | Contents | Status |
|---|---|---|
| `phase2d/` | All Phase 2D code, with every historical version side by side (v1–v12) | **Hash-locked**: do not add, move or rename files (the runner checks `code_hash`) |
| `artifacts/phase2d/` | Manifests v1–v12, status files, `runs/` (85 folders), `logs/` (incidents, guard logs), `gate0/`, `gate2/` (reports, audits, signal-test evidence) | Frozen evidence |
| `artifacts/phase2c/`, `artifacts/dss/`, `artifacts/splits/`, `config/` | Earlier-phase results and protocol | Frozen; checked by `common.assert_frozen_unchanged()` |
| `train/` | Phase 2B-B/2C training code, used unchanged by Phase 2D | Hash-locked |
| `sanity/`, `configs/` | Phase 1–2B-A code and configuration | Hash-locked (`sanity/*.py`) |
| `reports/` | Phase reports up to 2C | Final for their phase |
| `checkpoint/` | Prithvi-EO-2.0-300M weights and reference model code | Pretrained weights; never upload |
| `reference_sample/` | Upstream HLS example image | Reference only |
| `Data/` | Potsdam and Vaihingen imagery and labels (65 GB), **including the locked test tiles** | Licence-restricted; never upload; never open the test tiles |
| `venv/` | Python environment | Environment |

## Run folders (`artifacts/phase2d/runs/`)
- **75 complete runs**, each with `result.json`, `hashes.json`, best and final checkpoints, and
  `telemetry.jsonl`.
- **10 failed or aborted folders**, kept as evidence:
  - 8 Gate 2 interruptions, each rerun under an `_a2` ID
  - 2 pilot Layer 0 attempts, rerun as `_a3`
- The mapping is in `../docs/organization/04_VERSION_REGISTER.md` §4.

## Current versus historical code
- **The latest version is the one that ran last.** It is current only for the Gate 2 sequence,
  which is now complete.
- **Earlier versions are preserved** because each manifest names the exact entry point that ran
  its runs.
- **Full register:** `../docs/organization/04_VERSION_REGISTER.md`.
- **Navigation:** a categorized link view is at `../docs/browse/09_code_current_gate2/` and
  `../docs/browse/10_code_historical_versions/`.
