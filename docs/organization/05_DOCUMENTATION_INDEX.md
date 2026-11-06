# Documentation index

All paths are relative to `~/Documents/Major project/`. Every document is at its original location
(see `08_UNRESOLVED_PATH_DEPENDENCIES.md` for why none was moved). The `docs/browse/` folder gives
the same documents in a categorized view, as relative symbolic links.

**Status labels:**
- **FINAL**: the final finding of record.
- **APPROVED PROTOCOL**: a frozen design or protocol that governs later work.
- **AUDIT**: a verification of something else.
- **INTERMEDIATE**: superseded by a later report and kept as history.
- **RECORD**: an operational record (incident, launch).
- **EXPLORATORY**: pre-freeze analysis.

## 1. Start here
| Document | Status | What it is |
|---|---|---|
| `dssa/artifacts/phase2d/gate2/GATE2_FINAL_REPORT.md` | **FINAL** | Gate 2 oracle layer-utility sweep: results, DSS-versus-oracle comparison, depth confound, statistics, limitations, verdict (hypothesis not supported in its tested part) |
| `dssa/artifacts/phase2d/gate2/gate2_analysis.json` | **FINAL (data)** | Output of the frozen analysis, run through `gate2_analysis_v12.py` |
| `DSSA_PROJECT_FREEZE.md` | APPROVED PROTOCOL | Frozen research question (§A), hypothesis and falsification criterion (§B), scope |
| `DSSA_IMPLEMENTATION_FREEZE.md` | APPROVED PROTOCOL | Single-source-of-truth consolidated design |

## 2. Approved protocols and frozen designs (in order)
| Document | Phase | Notes |
|---|---|---|
| `DSSA_PROJECT_FREEZE.md` | Design freeze | Research question, hypothesis, falsification |
| `DSSA_FREEZE_FINAL_REVIEW.md` | Design freeze | Consolidated statement of record for the freeze |
| `DSSA_IMPLEMENTATION_FREEZE.md` | Implementation freeze | DSS definition, pooling, metrics; cited by `dssa/sanity/*.py` |
| `DSSA_PHASE2B_B_TRAINING_PROTOCOL_FREEZE.md` | Phase 2B-B | Training and evaluation protocol; cited by `dssa/train/*.py`. Machine form: `dssa/config/phase2b_training_protocol.json` |
| `dssa/phase2d/PHASE2D_ADDENDUM.md` | Phase 2D | δ = 0.010, separation of uncertainty sources, R2 exploratory status, scope, memory limits |
| `dssa/phase2d/PHASE2D_ADDENDUM_V2.md` | Phase 2D | 8-bit training cache, with a bit-exact equivalence gate. Adds to the first addendum |
| `dssa/artifacts/splits/vaihingen_target_split_manifest.json` | Phase 2B-A | Locked split, including the locked test tiles that must not be opened |

## 3. Pre-freeze analyses and audits (exploratory, Sept 2026)
| Document | Content |
|---|---|
| `DSSA_ABSTRACT_GAP_ANALYSIS.md` | Gap analysis of `DSSA_Final_Project_Abstract.pdf` |
| `DSSA_DATASET_SELECTION_AUDIT.md` | Choice of the Potsdam → Vaihingen pair |
| `DSSA_PRITHVI_COMPATIBILITY_AUDIT.md` | Backbone compatibility |
| `DSSA_PREIMPLEMENTATION_CALIBRATION.md` | Calibration and non-degeneracy plan; source of `dssa/artifacts/radiometric_transform.json` |
| `DSSA_SANITY_CHECK_REPORT.md` | Section 7 sanity check (design-level) |

## 4. Phase reports (`dssa/reports/`) and Phase 2B/2C audits
| Document | Phase |
|---|---|
| `dssa/reports/DSSA_SANITY_EXECUTION_REPORT.md` | Phase 1/1B sanity execution |
| `dssa/reports/DSSA_DATASET_INTEGRITY_REPORT.md` | Dataset integrity |
| `dssa/reports/DSSA_PHASE2A_DSS_VALIDATION_REPORT.md` | Phase 2A DSS mechanism validation |
| `dssa/reports/DSSA_PHASE2B_A_FINAL_SPLIT_KSWEEP_REPORT.md` | Phase 2B-A locked split, final DSS, K sweep |
| `dssa/reports/DSSA_PHASE2B_PREFLIGHT_REPORT.md` | Phase 2B preflight |
| `dssa/artifacts/phase2b_b_protocol_audit.md` | Phase 2B-B protocol audit |
| `dssa/reports/DSSA_PHASE2C_PREFLIGHT_REPORT.md` | Phase 2C preflight; batch 1 (5 runs) is in `dssa/artifacts/phase2c/` |

## 5. Phase 2D pilot and Gate 2 (`dssa/artifacts/phase2d/gate2/`)
| Document | Status | Content |
|---|---|---|
| `PILOT_STATISTICAL_AUDIT.md` | AUDIT | Corrected pilot statistics (t intervals, seeds needed) |
| `GATE2_RECOVERY_PLAN.md` | INTERMEDIATE | Recovery plan after INCIDENT_003 (v4 stop) |
| `GATE2_PARTIAL_RESULTS.md` | INTERMEDIATE | Results after the v4 stop |
| `GATE2_V5_LAUNCH.md`, `GATE2_V5_PARTIAL_RESULTS.md` | RECORD, INTERMEDIATE | v5 |
| `GATE2_V6_RECOVERY_PLAN.md`, `GATE2_V6_LAUNCH.md` | RECORD | v6 |
| `GATE2_V7_RECOVERY_REPORT.md`, `GATE2_V7_PARTIAL_RESULTS.md` | AUDIT, INTERMEDIATE | v7 |
| `GATE2_V8_AUDIT.md`, `GATE2_V8_LAUNCH.md` | AUDIT, RECORD | v8 (signal repair) |
| `GATE2_V9_AUDIT.md`, `GATE2_V9_LAUNCH.md` | AUDIT, RECORD | v9 |
| `GATE2_V10_AUDIT.md`, `GATE2_V10_LAUNCH.md` | AUDIT, RECORD | v10 (closed lid advisory, health watchdogs) |
| `GATE2_V11_AUDIT.md` | AUDIT | v11 |
| `GATE2_V12_AUDIT.md` | AUDIT | v12 (final execution manifest) |
| **`GATE2_FINAL_REPORT.md`** | **FINAL** | Final findings |

The matching machine-readable audits are `recovery_v7_audit.json` … `recovery_v12_audit.json`,
`pilot_statistical_audit.json`, `layer_mapping_check.json`, `equivalence_v4_recheck.json`,
`pilot_evidence_recheck.json` and `backup_restore_recheck.json`.

## 6. Incident records (`dssa/artifacts/phase2d/logs/`)
| Incident | Version | Cause |
|---|---|---|
| INCIDENT_001 | pilot v1 | Swap growth, L00 s1000 |
| INCIDENT_002 | pilot (L0 retry) | Swap growth |
| INCIDENT_003 | Gate 2 v4 | Runtime limit after system sleep, L02 s1000 |
| INCIDENT_004 | v5 | Swap growth (Docker VM), L06 s1000 |
| INCIDENT_005 | v6 | Swap growth, L07 s1000 |
| INCIDENT_006 | v7 | Charger disconnected, L02 s2000; SIGINT-ignored defect |
| INCIDENT_007 | v8 | Lid closed, L04 s2000 |
| INCIDENT_008 | v9 | Lid closed, L15 s2000 |
| INCIDENT_009 | v10 | Real sleep on battery after lid close, L20 s2000 |
| INCIDENT_010 | v11 | Real sleep on battery after lid close, L05 s3000 |

## 7. Backup and licensing
| Document | Content |
|---|---|
| `dssa/artifacts/phase2d/gate0/backup/ISPRS_LICENSING_POSITION.md` | Why imagery and labels are never backed up off-machine or published |
| `dssa/artifacts/phase2d/gate0/backup/BACKUP_VERIFICATION.json` | Gate 0 backup verification |
| `dssa/artifacts/phase2d/gate2/backup_restore_recheck.json` | Pre-Gate-2 restore recheck |

## 8. Presentation materials (not research evidence)
- `DSSA_Final_Project_Abstract.pdf`
- `DSSA_HOD_Presentation.pptx`
- `PRESENTATION_SCRIPT.md`
- `RGUKT Logo.png`

**Caution:** these date from September 2026. They predate the Phase 2D results and do not reflect
the Gate 2 conclusion.
