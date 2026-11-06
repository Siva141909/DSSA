# Final organized folder tree

The originals are unchanged. The new items are `README.md`, `dssa/README.md` and `docs/`. Large or repetitive folders are collapsed and annotated: `.git/`, `Data/`, `venv/`, `runs/`, `logs/`, `gate2/`, caches.

```
Major project/
├── .claude/
├── .git/ (10 entries)   # repository (HEAD 3551dbf; unchanged)
├── .gitignore
├── DSSA_ABSTRACT_GAP_ANALYSIS.md
├── DSSA_DATASET_SELECTION_AUDIT.md
├── DSSA_FREEZE_FINAL_REVIEW.md
├── DSSA_Final_Project_Abstract.pdf
├── DSSA_HOD_Presentation.pptx
├── DSSA_IMPLEMENTATION_FREEZE.md
├── DSSA_PHASE2B_B_TRAINING_PROTOCOL_FREEZE.md
├── DSSA_PREIMPLEMENTATION_CALIBRATION.md
├── DSSA_PRITHVI_COMPATIBILITY_AUDIT.md
├── DSSA_PROJECT_FREEZE.md
├── DSSA_SANITY_CHECK_REPORT.md
├── PRESENTATION_SCRIPT.md
├── README.md   # NEW
├── RGUKT Logo.png
├── docs/   # NEW
│   ├── browse/   # categorized symlink view (no copies)
│   │   ├── 00_START_HERE/
│   │   │   ├── DSSA_IMPLEMENTATION_FREEZE.md -> ../../../DSSA_IMPLEMENTATION_FREEZE.md
│   │   │   ├── DSSA_PROJECT_FREEZE.md -> ../../../DSSA_PROJECT_FREEZE.md
│   │   │   ├── GATE2_FINAL_REPORT.md -> ../../../dssa/artifacts/phase2d/gate2/GATE2_FINAL_REPORT.md
│   │   │   └── gate2_analysis.json -> ../../../dssa/artifacts/phase2d/gate2/gate2_analysis.json
│   │   ├── 01_approved_protocols/
│   │   │   ├── DSSA_FREEZE_FINAL_REVIEW.md -> ../../../DSSA_FREEZE_FINAL_REVIEW.md
│   │   │   ├── DSSA_IMPLEMENTATION_FREEZE.md -> ../../../DSSA_IMPLEMENTATION_FREEZE.md
│   │   │   ├── DSSA_PHASE2B_B_TRAINING_PROTOCOL_FREEZE.md -> ../../../DSSA_PHASE2B_B_TRAINING_PROTOCOL_FREEZE.md
│   │   │   ├── DSSA_PROJECT_FREEZE.md -> ../../../DSSA_PROJECT_FREEZE.md
│   │   │   ├── PHASE2D_ADDENDUM.md -> ../../../dssa/phase2d/PHASE2D_ADDENDUM.md
│   │   │   ├── PHASE2D_ADDENDUM_V2.md -> ../../../dssa/phase2d/PHASE2D_ADDENDUM_V2.md
│   │   │   ├── phase2b_training_protocol.json -> ../../../dssa/config/phase2b_training_protocol.json
│   │   │   └── sanity_config.yaml -> ../../../dssa/configs/sanity_config.yaml
│   │   ├── 02_pre_freeze_exploratory/
│   │   │   ├── DSSA_ABSTRACT_GAP_ANALYSIS.md -> ../../../DSSA_ABSTRACT_GAP_ANALYSIS.md
│   │   │   ├── DSSA_DATASET_SELECTION_AUDIT.md -> ../../../DSSA_DATASET_SELECTION_AUDIT.md
│   │   │   ├── DSSA_PREIMPLEMENTATION_CALIBRATION.md -> ../../../DSSA_PREIMPLEMENTATION_CALIBRATION.md
│   │   │   ├── DSSA_PRITHVI_COMPATIBILITY_AUDIT.md -> ../../../DSSA_PRITHVI_COMPATIBILITY_AUDIT.md
│   │   │   └── DSSA_SANITY_CHECK_REPORT.md -> ../../../DSSA_SANITY_CHECK_REPORT.md
│   │   ├── 03_phase_reports/
│   │   │   ├── DSSA_DATASET_INTEGRITY_REPORT.md -> ../../../dssa/reports/DSSA_DATASET_INTEGRITY_REPORT.md
│   │   │   ├── DSSA_PHASE2A_DSS_VALIDATION_REPORT.md -> ../../../dssa/reports/DSSA_PHASE2A_DSS_VALIDATION_REPORT.md
│   │   │   ├── DSSA_PHASE2B_A_FINAL_SPLIT_KSWEEP_REPORT.md -> ../../../dssa/reports/DSSA_PHASE2B_A_FINAL_SPLIT_KSWEEP_REPORT.md
│   │   │   ├── DSSA_PHASE2B_PREFLIGHT_REPORT.md -> ../../../dssa/reports/DSSA_PHASE2B_PREFLIGHT_REPORT.md
│   │   │   ├── DSSA_PHASE2C_PREFLIGHT_REPORT.md -> ../../../dssa/reports/DSSA_PHASE2C_PREFLIGHT_REPORT.md
│   │   │   ├── DSSA_SANITY_EXECUTION_REPORT.md -> ../../../dssa/reports/DSSA_SANITY_EXECUTION_REPORT.md
│   │   │   ├── PILOT_STATISTICAL_AUDIT.md -> ../../../dssa/artifacts/phase2d/gate2/PILOT_STATISTICAL_AUDIT.md
│   │   │   └── phase2b_b_protocol_audit.md -> ../../../dssa/artifacts/phase2b_b_protocol_audit.md
│   │   ├── 04_gate2_final_findings/
│   │   │   ├── GATE2_FINAL_REPORT.md -> ../../../dssa/artifacts/phase2d/gate2/GATE2_FINAL_REPORT.md
│   │   │   └── gate2_analysis.json -> ../../../dssa/artifacts/phase2d/gate2/gate2_analysis.json
│   │   ├── 05_gate2_intermediate_reports_and_audits/
│   │   │   ├── GATE2_PARTIAL_RESULTS.md -> ../../../dssa/artifacts/phase2d/gate2/GATE2_PARTIAL_RESULTS.md
│   │   │   ├── GATE2_RECOVERY_PLAN.md -> ../../../dssa/artifacts/phase2d/gate2/GATE2_RECOVERY_PLAN.md
│   │   │   ├── GATE2_V10_AUDIT.md -> ../../../dssa/artifacts/phase2d/gate2/GATE2_V10_AUDIT.md
│   │   │   ├── GATE2_V10_LAUNCH.md -> ../../../dssa/artifacts/phase2d/gate2/GATE2_V10_LAUNCH.md
│   │   │   ├── GATE2_V11_AUDIT.md -> ../../../dssa/artifacts/phase2d/gate2/GATE2_V11_AUDIT.md
│   │   │   ├── GATE2_V12_AUDIT.md -> ../../../dssa/artifacts/phase2d/gate2/GATE2_V12_AUDIT.md
│   │   │   ├── GATE2_V5_LAUNCH.md -> ../../../dssa/artifacts/phase2d/gate2/GATE2_V5_LAUNCH.md
│   │   │   ├── GATE2_V5_PARTIAL_RESULTS.md -> ../../../dssa/artifacts/phase2d/gate2/GATE2_V5_PARTIAL_RESULTS.md
│   │   │   ├── GATE2_V6_LAUNCH.md -> ../../../dssa/artifacts/phase2d/gate2/GATE2_V6_LAUNCH.md
│   │   │   ├── GATE2_V6_RECOVERY_PLAN.md -> ../../../dssa/artifacts/phase2d/gate2/GATE2_V6_RECOVERY_PLAN.md
│   │   │   ├── GATE2_V7_PARTIAL_RESULTS.md -> ../../../dssa/artifacts/phase2d/gate2/GATE2_V7_PARTIAL_RESULTS.md
│   │   │   ├── GATE2_V7_RECOVERY_REPORT.md -> ../../../dssa/artifacts/phase2d/gate2/GATE2_V7_RECOVERY_REPORT.md
│   │   │   ├── GATE2_V8_AUDIT.md -> ../../../dssa/artifacts/phase2d/gate2/GATE2_V8_AUDIT.md
│   │   │   ├── GATE2_V8_LAUNCH.md -> ../../../dssa/artifacts/phase2d/gate2/GATE2_V8_LAUNCH.md
│   │   │   ├── GATE2_V9_AUDIT.md -> ../../../dssa/artifacts/phase2d/gate2/GATE2_V9_AUDIT.md
│   │   │   ├── GATE2_V9_LAUNCH.md -> ../../../dssa/artifacts/phase2d/gate2/GATE2_V9_LAUNCH.md
│   │   │   ├── backup_restore_recheck.json -> ../../../dssa/artifacts/phase2d/gate2/backup_restore_recheck.json
│   │   │   ├── equivalence_v4_recheck.json -> ../../../dssa/artifacts/phase2d/gate2/equivalence_v4_recheck.json
│   │   │   ├── layer_mapping_check.json -> ../../../dssa/artifacts/phase2d/gate2/layer_mapping_check.json
│   │   │   ├── layer_mapping_check__FAILED_attempt1_unseeded_decoder.json -> ../../../dssa/artifacts/phase2d/gate2/layer_mapping_check__FAILED_attempt1_unseeded_decoder.json
│   │   │   ├── pilot_evidence_recheck.json -> ../../../dssa/artifacts/phase2d/gate2/pilot_evidence_recheck.json
│   │   │   ├── pilot_statistical_audit.json -> ../../../dssa/artifacts/phase2d/gate2/pilot_statistical_audit.json
│   │   │   ├── recovery_v10_audit.json -> ../../../dssa/artifacts/phase2d/gate2/recovery_v10_audit.json
│   │   │   ├── recovery_v10_audit__superseded_lid_stop.json -> ../../../dssa/artifacts/phase2d/gate2/recovery_v10_audit__superseded_lid_stop.json
│   │   │   ├── recovery_v11_audit.json -> ../../../dssa/artifacts/phase2d/gate2/recovery_v11_audit.json
│   │   │   ├── recovery_v12_audit.json -> ../../../dssa/artifacts/phase2d/gate2/recovery_v12_audit.json
│   │   │   ├── recovery_v7_audit.json -> ../../../dssa/artifacts/phase2d/gate2/recovery_v7_audit.json
│   │   │   ├── recovery_v8_audit.json -> ../../../dssa/artifacts/phase2d/gate2/recovery_v8_audit.json
│   │   │   └── recovery_v9_audit.json -> ../../../dssa/artifacts/phase2d/gate2/recovery_v9_audit.json
│   │   ├── 06_incidents/
│   │   │   ├── INCIDENT_001_swap_stop.md -> ../../../dssa/artifacts/phase2d/logs/INCIDENT_001_swap_stop.md
│   │   │   ├── INCIDENT_002_l0_retry_swap_stop.md -> ../../../dssa/artifacts/phase2d/logs/INCIDENT_002_l0_retry_swap_stop.md
│   │   │   ├── INCIDENT_003_gate2_runtime_stop_system_sleep.md -> ../../../dssa/artifacts/phase2d/logs/INCIDENT_003_gate2_runtime_stop_system_sleep.md
│   │   │   ├── INCIDENT_004_gate2_v5_swap_growth_stop.md -> ../../../dssa/artifacts/phase2d/logs/INCIDENT_004_gate2_v5_swap_growth_stop.md
│   │   │   ├── INCIDENT_005_gate2_v6_swap_growth_stop.md -> ../../../dssa/artifacts/phase2d/logs/INCIDENT_005_gate2_v6_swap_growth_stop.md
│   │   │   ├── INCIDENT_006_gate2_v7_charger_disconnected.md -> ../../../dssa/artifacts/phase2d/logs/INCIDENT_006_gate2_v7_charger_disconnected.md
│   │   │   ├── INCIDENT_007_gate2_v8_lid_closed.md -> ../../../dssa/artifacts/phase2d/logs/INCIDENT_007_gate2_v8_lid_closed.md
│   │   │   ├── INCIDENT_008_gate2_v9_lid_closed.md -> ../../../dssa/artifacts/phase2d/logs/INCIDENT_008_gate2_v9_lid_closed.md
│   │   │   ├── INCIDENT_009_gate2_v10_charger_sleep.md -> ../../../dssa/artifacts/phase2d/logs/INCIDENT_009_gate2_v10_charger_sleep.md
│   │   │   └── INCIDENT_010_gate2_v11_lid_close_power_loss_sleep.md -> ../../../dssa/artifacts/phase2d/logs/INCIDENT_010_gate2_v11_lid_close_power_loss_sleep.md
│   │   ├── 07_manifests_execution_chain/
│   │   │   ├── manifest_gate2_recovery_v10.json -> ../../../dssa/artifacts/phase2d/manifest_gate2_recovery_v10.json
│   │   │   ├── manifest_gate2_recovery_v10__superseded_lid_stop.json -> ../../../dssa/artifacts/phase2d/manifest_gate2_recovery_v10__superseded_lid_stop.json
│   │   │   ├── manifest_gate2_recovery_v11.json -> ../../../dssa/artifacts/phase2d/manifest_gate2_recovery_v11.json
│   │   │   ├── manifest_gate2_recovery_v12.json -> ../../../dssa/artifacts/phase2d/manifest_gate2_recovery_v12.json
│   │   │   ├── manifest_gate2_recovery_v5.json -> ../../../dssa/artifacts/phase2d/manifest_gate2_recovery_v5.json
│   │   │   ├── manifest_gate2_recovery_v6.json -> ../../../dssa/artifacts/phase2d/manifest_gate2_recovery_v6.json
│   │   │   ├── manifest_gate2_recovery_v7.json -> ../../../dssa/artifacts/phase2d/manifest_gate2_recovery_v7.json
│   │   │   ├── manifest_gate2_recovery_v8.json -> ../../../dssa/artifacts/phase2d/manifest_gate2_recovery_v8.json
│   │   │   ├── manifest_gate2_recovery_v9.json -> ../../../dssa/artifacts/phase2d/manifest_gate2_recovery_v9.json
│   │   │   ├── manifest_gate2_v4.json -> ../../../dssa/artifacts/phase2d/manifest_gate2_v4.json
│   │   │   ├── manifest_pilot.json -> ../../../dssa/artifacts/phase2d/manifest_pilot.json
│   │   │   ├── manifest_pilot_v2.json -> ../../../dssa/artifacts/phase2d/manifest_pilot_v2.json
│   │   │   ├── manifest_pilot_v2_draft_unused_bug.json -> ../../../dssa/artifacts/phase2d/manifest_pilot_v2_draft_unused_bug.json
│   │   │   └── manifest_pilot_v3.json -> ../../../dssa/artifacts/phase2d/manifest_pilot_v3.json
│   │   ├── 08_frozen_inputs/
│   │   │   ├── baseline_hashes.json -> ../../../dssa/artifacts/phase2d/gate0/baseline_hashes.json
│   │   │   ├── frozen_rankings.json -> ../../../dssa/artifacts/phase2d/gate0/frozen_rankings.json
│   │   │   ├── phase2b_final_dss_results.json -> ../../../dssa/artifacts/dss/phase2b_final_dss_results.json
│   │   │   ├── phase2c_batch1_checkpoint_report.json -> ../../../dssa/artifacts/phase2c/phase2c_batch1_checkpoint_report.json
│   │   │   ├── radiometric_transform.json -> ../../../dssa/artifacts/radiometric_transform.json
│   │   │   └── vaihingen_target_split_manifest.json -> ../../../dssa/artifacts/splits/vaihingen_target_split_manifest.json
│   │   ├── 09_code_current_gate2/
│   │   │   ├── common.py -> ../../../dssa/phase2d/common.py
│   │   │   ├── dataset_u8.py -> ../../../dssa/phase2d/dataset_u8.py
│   │   │   ├── evaluation.py -> ../../../dssa/phase2d/evaluation.py
│   │   │   ├── gate2_analysis.py -> ../../../dssa/phase2d/gate2_analysis.py
│   │   │   ├── gate2_analysis_v12.py -> ../../../dssa/phase2d/gate2_analysis_v12.py
│   │   │   ├── gate_v12.py -> ../../../dssa/phase2d/gate_v12.py
│   │   │   ├── models.py -> ../../../dssa/phase2d/models.py
│   │   │   ├── oracle_analysis.py -> ../../../dssa/phase2d/oracle_analysis.py
│   │   │   ├── run_gate2_v12.py -> ../../../dssa/phase2d/run_gate2_v12.py
│   │   │   ├── run_one_v12.py -> ../../../dssa/phase2d/run_one_v12.py
│   │   │   ├── run_one_v2.py -> ../../../dssa/phase2d/run_one_v2.py
│   │   │   ├── sigsafe.py -> ../../../dssa/phase2d/sigsafe.py
│   │   │   ├── tstat.py -> ../../../dssa/phase2d/tstat.py
│   │   │   ├── verify_reload.py -> ../../../dssa/phase2d/verify_reload.py
│   │   │   └── verify_reload_v8.py -> ../../../dssa/phase2d/verify_reload_v8.py
│   │   ├── 10_code_historical_versions/
│   │   │   ├── gate0_dss.py -> ../../../dssa/phase2d/gate0_dss.py
│   │   │   ├── gate0_setup.py -> ../../../dssa/phase2d/gate0_setup.py
│   │   │   ├── gate2_analysis_v10.py -> ../../../dssa/phase2d/gate2_analysis_v10.py
│   │   │   ├── gate2_analysis_v11.py -> ../../../dssa/phase2d/gate2_analysis_v11.py
│   │   │   ├── gate2_analysis_v5.py -> ../../../dssa/phase2d/gate2_analysis_v5.py
│   │   │   ├── gate2_analysis_v6.py -> ../../../dssa/phase2d/gate2_analysis_v6.py
│   │   │   ├── gate2_analysis_v7.py -> ../../../dssa/phase2d/gate2_analysis_v7.py
│   │   │   ├── gate2_analysis_v8.py -> ../../../dssa/phase2d/gate2_analysis_v8.py
│   │   │   ├── gate2_analysis_v9.py -> ../../../dssa/phase2d/gate2_analysis_v9.py
│   │   │   ├── gate2_setup.py -> ../../../dssa/phase2d/gate2_setup.py
│   │   │   ├── gate_v10.py -> ../../../dssa/phase2d/gate_v10.py
│   │   │   ├── gate_v11.py -> ../../../dssa/phase2d/gate_v11.py
│   │   │   ├── gate_v2.py -> ../../../dssa/phase2d/gate_v2.py
│   │   │   ├── gate_v3.py -> ../../../dssa/phase2d/gate_v3.py
│   │   │   ├── gate_v5.py -> ../../../dssa/phase2d/gate_v5.py
│   │   │   ├── gate_v6.py -> ../../../dssa/phase2d/gate_v6.py
│   │   │   ├── gate_v7.py -> ../../../dssa/phase2d/gate_v7.py
│   │   │   ├── gate_v8.py -> ../../../dssa/phase2d/gate_v8.py
│   │   │   ├── gate_v9.py -> ../../../dssa/phase2d/gate_v9.py
│   │   │   ├── pilot_analysis.py -> ../../../dssa/phase2d/pilot_analysis.py
│   │   │   ├── pilot_analysis_v3.py -> ../../../dssa/phase2d/pilot_analysis_v3.py
│   │   │   ├── pilot_stats_audit.py -> ../../../dssa/phase2d/pilot_stats_audit.py
│   │   │   ├── run_gate2.py -> ../../../dssa/phase2d/run_gate2.py
│   │   │   ├── run_gate2_v10.py -> ../../../dssa/phase2d/run_gate2_v10.py
│   │   │   ├── run_gate2_v11.py -> ../../../dssa/phase2d/run_gate2_v11.py
│   │   │   ├── run_gate2_v5.py -> ../../../dssa/phase2d/run_gate2_v5.py
│   │   │   ├── run_gate2_v6.py -> ../../../dssa/phase2d/run_gate2_v6.py
│   │   │   ├── run_gate2_v7.py -> ../../../dssa/phase2d/run_gate2_v7.py
│   │   │   ├── run_gate2_v8.py -> ../../../dssa/phase2d/run_gate2_v8.py
│   │   │   ├── run_gate2_v9.py -> ../../../dssa/phase2d/run_gate2_v9.py
│   │   │   ├── run_one.py -> ../../../dssa/phase2d/run_one.py
│   │   │   ├── run_one_v10.py -> ../../../dssa/phase2d/run_one_v10.py
│   │   │   ├── run_one_v11.py -> ../../../dssa/phase2d/run_one_v11.py
│   │   │   ├── run_one_v3.py -> ../../../dssa/phase2d/run_one_v3.py
│   │   │   ├── run_one_v4.py -> ../../../dssa/phase2d/run_one_v4.py
│   │   │   ├── run_one_v5.py -> ../../../dssa/phase2d/run_one_v5.py
│   │   │   ├── run_one_v6.py -> ../../../dssa/phase2d/run_one_v6.py
│   │   │   ├── run_one_v7.py -> ../../../dssa/phase2d/run_one_v7.py
│   │   │   ├── run_one_v8.py -> ../../../dssa/phase2d/run_one_v8.py
│   │   │   ├── run_one_v9.py -> ../../../dssa/phase2d/run_one_v9.py
│   │   │   ├── run_pilot.py -> ../../../dssa/phase2d/run_pilot.py
│   │   │   └── run_pilot_v3.py -> ../../../dssa/phase2d/run_pilot_v3.py
│   │   ├── 11_backup_and_licensing/
│   │   │   ├── BACKUP_VERIFICATION.json -> ../../../dssa/artifacts/phase2d/gate0/backup/BACKUP_VERIFICATION.json
│   │   │   ├── ISPRS_LICENSING_POSITION.md -> ../../../dssa/artifacts/phase2d/gate0/backup/ISPRS_LICENSING_POSITION.md
│   │   │   └── backup_restore_recheck.json -> ../../../dssa/artifacts/phase2d/gate2/backup_restore_recheck.json
│   │   ├── 12_presentation_materials/
│   │   │   ├── DSSA_Final_Project_Abstract.pdf -> ../../../DSSA_Final_Project_Abstract.pdf
│   │   │   ├── DSSA_HOD_Presentation.pptx -> ../../../DSSA_HOD_Presentation.pptx
│   │   │   ├── PRESENTATION_SCRIPT.md -> ../../../PRESENTATION_SCRIPT.md
│   │   │   └── RGUKT Logo.png -> ../../../RGUKT Logo.png
│   │   └── 13_folders/
│   │       ├── dssa__artifacts__phase2c -> ../../../dssa/artifacts/phase2c
│   │       ├── dssa__artifacts__phase2d__gate2 -> ../../../dssa/artifacts/phase2d/gate2
│   │       ├── dssa__artifacts__phase2d__logs -> ../../../dssa/artifacts/phase2d/logs
│   │       ├── dssa__artifacts__phase2d__runs -> ../../../dssa/artifacts/phase2d/runs
│   │       ├── dssa__phase2d -> ../../../dssa/phase2d
│   │       ├── dssa__reports -> ../../../dssa/reports
│   │       ├── dssa__sanity -> ../../../dssa/sanity
│   │       └── dssa__train -> ../../../dssa/train
│   └── organization/   # archive documentation (deliverables 1–9)
│       ├── 01_ORIGINAL_INVENTORY.tsv
│       ├── 03_MOVE_AND_RENAME_MAP.md
│       ├── 04_VERSION_REGISTER.md
│       ├── 05_DOCUMENTATION_INDEX.md
│       ├── 06_INTEGRITY_VERIFICATION.md
│       ├── 07_DUPLICATES.md
│       └── 08_UNRESOLVED_PATH_DEPENDENCIES.md
└── dssa/
    ├── Data/   # licensed imagery + locked test set (not opened)
    ├── README.md   # NEW
    ├── artifacts/
    │   ├── dataset_integrity_raw.json
    │   ├── dss/
    │   │   ├── phase2a_dss_results.json
    │   │   ├── phase2a_run.log
    │   │   ├── phase2b_a_repeatability_check.json
    │   │   ├── phase2b_final_dss_results.json
    │   │   └── phase2b_final_dss_run.log
    │   ├── hls_reference_layer_norms.json
    │   ├── phase2b_b_protocol_audit.md
    │   ├── phase2c/   # frozen Phase 2C batch 1
    │   │   ├── phase2c_batch1_checkpoint_report.json
    │   │   ├── phase2c_preflight_report.json
    │   │   ├── preflight_checkpoints/ (3 entries)
    │   │   ├── run_matrix_batch1.log
    │   │   └── runs/ (5 entries)
    │   ├── phase2d/
    │   │   ├── gate0/   # frozen rankings, baseline hashes, backup records
    │   │   ├── gate2/ (40 entries)   # Gate 2 reports, audits, signal-test evidence, FINAL REPORT, analysis JSON
    │   │   ├── gate2_status_v10.json
    │   │   ├── gate2_status_v11.json
    │   │   ├── gate2_status_v12.json
    │   │   ├── gate2_status_v4.json
    │   │   ├── gate2_status_v5.json
    │   │   ├── gate2_status_v6.json
    │   │   ├── gate2_status_v7.json
    │   │   ├── gate2_status_v8.json
    │   │   ├── gate2_status_v9.json
    │   │   ├── logs/ (124 entries)   # per-run logs, guard/interruption logs, INCIDENT_001–010
    │   │   ├── manifest_gate2_recovery_v10.json
    │   │   ├── manifest_gate2_recovery_v10__superseded_lid_stop.json
    │   │   ├── manifest_gate2_recovery_v11.json
    │   │   ├── manifest_gate2_recovery_v12.json
    │   │   ├── manifest_gate2_recovery_v5.json
    │   │   ├── manifest_gate2_recovery_v6.json
    │   │   ├── manifest_gate2_recovery_v7.json
    │   │   ├── manifest_gate2_recovery_v8.json
    │   │   ├── manifest_gate2_recovery_v9.json
    │   │   ├── manifest_gate2_v4.json
    │   │   ├── manifest_pilot.json
    │   │   ├── manifest_pilot_v2.json
    │   │   ├── manifest_pilot_v2_draft_unused_bug.json
    │   │   ├── manifest_pilot_v3.json
    │   │   ├── pilot_analysis.json
    │   │   ├── pilot_completion_record_v3.json
    │   │   ├── pilot_per_class_v3.json
    │   │   ├── pilot_status.json
    │   │   ├── pilot_status_v3.json
    │   │   └── runs/ (86 entries)   # 75 complete + 10 interrupted/aborted run folders
    │   ├── radiometric_transform.json
    │   ├── real_data_sanity_metrics.json
    │   ├── real_data_sanity_run.log
    │   ├── sanity_metrics.json
    │   ├── splits/
    │   │   └── vaihingen_target_split_manifest.json
    │   └── target_train_class_distribution.json
    ├── checkpoint/   # Prithvi weights + model code
    │   ├── .cache/ (1 entries)
    │   ├── Prithvi_EO_V2_300M.pt
    │   ├── __pycache__/ (1 entries)
    │   ├── config.json
    │   ├── inference.py
    │   ├── prithvi_mae.py
    │   └── requirements.txt
    ├── config/
    │   └── phase2b_training_protocol.json
    ├── configs/
    │   └── sanity_config.yaml
    ├── phase2d/   # HASH-LOCKED code, all versions v1–v12
    │   ├── PHASE2D_ADDENDUM.md
    │   ├── PHASE2D_ADDENDUM_V2.md
    │   ├── common.py
    │   ├── dataset_u8.py
    │   ├── evaluation.py
    │   ├── gate0_dss.py
    │   ├── gate0_setup.py
    │   ├── gate2_analysis.py
    │   ├── gate2_analysis_v10.py
    │   ├── gate2_analysis_v11.py
    │   ├── gate2_analysis_v12.py
    │   ├── gate2_analysis_v5.py
    │   ├── gate2_analysis_v6.py
    │   ├── gate2_analysis_v7.py
    │   ├── gate2_analysis_v8.py
    │   ├── gate2_analysis_v9.py
    │   ├── gate2_setup.py
    │   ├── gate_v10.py
    │   ├── gate_v11.py
    │   ├── gate_v12.py
    │   ├── gate_v2.py
    │   ├── gate_v3.py
    │   ├── gate_v5.py
    │   ├── gate_v6.py
    │   ├── gate_v7.py
    │   ├── gate_v8.py
    │   ├── gate_v9.py
    │   ├── models.py
    │   ├── oracle_analysis.py
    │   ├── pilot_analysis.py
    │   ├── pilot_analysis_v3.py
    │   ├── pilot_stats_audit.py
    │   ├── run_gate2.py
    │   ├── run_gate2_v10.py
    │   ├── run_gate2_v11.py
    │   ├── run_gate2_v12.py
    │   ├── run_gate2_v5.py
    │   ├── run_gate2_v6.py
    │   ├── run_gate2_v7.py
    │   ├── run_gate2_v8.py
    │   ├── run_gate2_v9.py
    │   ├── run_one.py
    │   ├── run_one_v10.py
    │   ├── run_one_v11.py
    │   ├── run_one_v12.py
    │   ├── run_one_v2.py
    │   ├── run_one_v3.py
    │   ├── run_one_v4.py
    │   ├── run_one_v5.py
    │   ├── run_one_v6.py
    │   ├── run_one_v7.py
    │   ├── run_one_v8.py
    │   ├── run_one_v9.py
    │   ├── run_pilot.py
    │   ├── run_pilot_v3.py
    │   ├── sigsafe.py
    │   ├── tstat.py
    │   ├── verify_reload.py
    │   └── verify_reload_v8.py
    ├── reference_sample/
    │   ├── .cache/ (1 entries)
    │   └── examples/
    │       └── Mexico_HLS.S30.T13REM.2018026T173609.v2.0_cropped.tif
    ├── reports/
    │   ├── DSSA_DATASET_INTEGRITY_REPORT.md
    │   ├── DSSA_PHASE2A_DSS_VALIDATION_REPORT.md
    │   ├── DSSA_PHASE2B_A_FINAL_SPLIT_KSWEEP_REPORT.md
    │   ├── DSSA_PHASE2B_PREFLIGHT_REPORT.md
    │   ├── DSSA_PHASE2C_PREFLIGHT_REPORT.md
    │   └── DSSA_SANITY_EXECUTION_REPORT.md
    ├── sanity/   # hash-locked DSS/sanity code
    │   ├── __pycache__/ (5 entries)
    │   ├── diagnostics.py
    │   ├── mmd.py
    │   ├── model.py
    │   ├── preprocessing.py
    │   ├── run_phase2a_dss.py
    │   ├── run_phase2b_final_dss.py
    │   ├── run_real_data_sanity.py
    │   ├── run_repeatability_check.py
    │   └── run_sanity_check.py
    ├── train/   # hash-locked training code
    │   ├── __pycache__/ (11 entries)
    │   ├── checkpoint.py
    │   ├── dataset.py
    │   ├── decoder.py
    │   ├── efficiency.py
    │   ├── lora.py
    │   ├── losses.py
    │   ├── manifest.py
    │   ├── metrics.py
    │   ├── model_wrapper.py
    │   ├── preflight.py
    │   ├── run_matrix.py
    │   ├── tiling.py
    │   └── train.py
    └── venv/ (5 entries)   # python environment
```

Each `docs/browse/<category>/` folder contains relative symbolic links to the original files. For the full list, run `ls -l docs/browse/*`.
