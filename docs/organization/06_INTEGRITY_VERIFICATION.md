# Frozen artifact and organization integrity verification

Run on 2026-11-05, after all organizational changes. The check is read-only:
- no training, evaluation or analysis was run
- the locked test set was not opened

The raw output is reproduced in §2.

## 1. Results
| # | Check | Result |
|---|---|---|
| 1 | All 1,088 inventoried original files still exist at their original paths | **PASS**: 0 missing |
| 1b | No original file overwritten or changed (SHA-256 against `01_ORIGINAL_INVENTORY.tsv`) | **PASS**: 0 changed |
| 2 | New paths are confined to `docs/`, `README.md` and `dssa/README.md` | **PASS**: 166 new paths (158 links, 6 organization documents, 2 READMEs), none elsewhere |
| 3 | Frozen Phase 2C / 2B artifacts (`common.assert_frozen_unchanged()`, 15 files against `gate0/baseline_hashes.json`) | **PASS** |
| 4 | `dssa/phase2d` code hash equals manifest v12 `code_hash` (59 files) | **PASS** |
| 5 | `dssa/train` + `dssa/sanity` code hash equals manifest v12 `train_and_sanity_code_hash` | **PASS** |
| 6 | Manifest chain: the v1, v4–v12 file hashes match the recorded values, and each predecessor hash recorded in v12 matches its file | **PASS** |
| 7 | 8 preserved interrupted Gate 2 folders match their recorded file hashes; their incident reports match the recorded hashes | **PASS** |
| 8 | 75 completed runs (63 Gate 2 + 12 pilot) pass the frozen analysis's integrity loader. Per run: status, 2,000 steps, layer, seed, decoder and RNG hashes, backbone fingerprint, data-stream replay, allowed tiles only, result hash, best and final checkpoint hashes, reload confusion-matrix difference 0 | **PASS**: 0 problems |
| 9 | Pilot hashes recorded in manifest v12 | **PASS** |
| 10 | Final report and analysis are unchanged: `GATE2_FINAL_REPORT.md` `091fb435…abdb8`, `gate2_analysis.json` `034f7027…ee2f`, `frozen_rankings.json` `55667a67…f9b8` | **PASS** |
| 11 | `docs/browse/`: 158 symbolic links, 0 broken, 0 copied files | **PASS** |
| 12 | Git: HEAD `3551dbf` unchanged, 2 refs, no commit, no push. Status shows only pre-existing changes (`.gitignore`, `dssa/phase2d/`, `dssa/artifacts/phase2d/`) plus the new untracked `README.md`, `dssa/README.md` and `docs/` | **PASS** |
| 13 | `dssa/Data/` top-level listing only (not opened) | Unchanged |
| 14 | No bytecode cache created in `dssa/phase2d/`; no file in `dssa/phase2d/` or `dssa/artifacts/phase2d/` newer than the inventory | **PASS** |

**Overall: PASS.** The organization moved nothing, overwrote nothing and deleted nothing. All
reproducibility checks still hold.

Note on the two `.gitignore` items:
- `.gitignore` is shown as modified because of the Phase 2D rule added before this task (Addendum §7).
- The untracked Phase 2D folders are the uncommitted Phase 2D work.

## 2. Raw output
```
1. original files: 1088 missing: 0 content changed: 0 []
2. new paths: 166 outside docs/ and READMEs: []
3. frozen artifacts (common.assert_frozen_unchanged): PASS, 15 files
4. dssa/phase2d code_hash == manifest v12: True 59 files
5. train+sanity code hash == manifest v12: True
6. manifest chain hashes: True | recorded predecessor hashes in v12: True True True
7. preserved interrupted folders match recorded hashes: True 8 | incident reports: True
8. 75-run integrity (...): 75 runs, problems: []
9. pilot hashes in v12: True
10. gate2/GATE2_FINAL_REPORT.md 091fb4353dc0909231f921b9f3241c70c39a53ad7ed1cf8b60e0aa06c71abdb8 == inventory: True
10. gate2/gate2_analysis.json 034f702738c872a284d786678bd3a53a473b35e403e420aa35fe6d6a80a2ee2f == inventory: True
10. gate0/frozen_rankings.json 55667a6707204fa9eba5ff8bf17c97fa2a2edf6d0e6bb9cf64da212df05af9b8 == inventory: True
11. browse links: 158 broken: 0 non-link files in browse: 0
12. git HEAD: 3551dbff5083e2d67df6a01139e5d5a4ee84271a | refs: 2 | status: M .gitignore, ?? README.md, ?? docs/, ?? dssa/README.md, ?? dssa/artifacts/phase2d/, ?? dssa/phase2d/
13. Data top level: .DS_Store, Potsdam, Potsdam.zip, Vaihingen, Vaihingen.zip, potsdam_irrg, vaihingen_irrg
```

## 3. Scope notes
- **`01_ORIGINAL_INVENTORY.tsv`** hashes every file except `.git/`, `dssa/venv/` (Python environment)
  and `dssa/Data/`. `Data/` holds licensed imagery and the locked test set, and was listed at the top
  level only.
- **Inventory timing:** it was taken while the Gate 2 final backup was being prepared. The backup
  archive is in the scratchpad, outside the project, so it is not part of the project inventory.
