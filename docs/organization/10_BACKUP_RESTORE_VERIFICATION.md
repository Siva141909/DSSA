# Gate 2 final backup: restore verification

Date: 2026-11-06. **Result: PASS.**

| Item | Value |
|---|---|
| Release | GitHub draft release 431538319, `Siva141909/DSSA` (private, still a draft, unchanged) |
| Archive | `phase2d_gate2_final.tgz`, asset ID 714129277, 1,639,684,508 bytes |
| Checksum file | `SHA256SUMS_gate2_final`, asset ID 714208274 |
| SHA-256 | `ab50f697767fbc93d21f80a2a29e95bca94fedaf9b38e4ad0dd3b317b6304bd6` |
| Download | Downloaded manually by the user to `~/Downloads` |
| Checksum match | `shasum -c SHA256SUMS_gate2_final` reports OK. Also matches the SHA-256 recorded at build time and GitHub's asset digest |
| Archive safety | No absolute paths and no `..` entries. Top level: `.gitignore`, `dssa/phase2d/`, `dssa/artifacts/phase2d/` |
| Restore location | A fresh folder in the temporary directory, outside the project |
| File list | 934 restored files, identical to the 934 backup-scope rows of `01_ORIGINAL_INVENTORY.tsv` |
| Sizes and SHA-256 | Identical for all 934 files |
| Restored vs current project | 932 identical. 2 expected differences, listed below |
| Frozen artifacts | `common.assert_frozen_unchanged()` passes |

## Expected differences from the current working tree (not backup errors)
1. **`.gitignore`:** after the backup was built, 3 lines were appended (a comment plus an ignore rule for
   the image-bearing `DSSA_Mid_Phase_Review_Final.pptx`). The restored copy matches the inventory hash.
2. **`dssa/artifacts/phase2d/.DS_Store`:** the macOS Finder metadata file was rewritten (same size,
   later timestamp). It is not research data.

## Archive contents
- **Included:** Phase 2D code (all versions), manifests v1–v12, status files, all 85 run folders,
  logs and incidents, Gate 0 records, and all Gate 2 reports and analysis.
- **Excluded by the established procedure:** `*.npz` and `gate0/smoke/`.
- **Restricted data:** no imagery, labels, pretrained weights or credentials (checked at build time).
