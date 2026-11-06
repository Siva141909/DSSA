# Path dependencies and why files were not moved

**Decision: no existing file was moved or renamed.** Every candidate move is blocked by at least one of
the dependencies below. Breaking any of them would either stop the reproducibility checks from
passing or leave frozen documents pointing to files that are no longer where the text says.

None of these dependencies is broken today. Each would be broken by a reorganization, so each is
recorded here instead.

## D1. `dssa/phase2d/` code hash (hard dependency)
- `common.code_hash()` is defined as
  `{p.name: sha256 for p in sorted(CODE.glob("*")) if p.suffix in (".py", ".md")}`, where
  `CODE = dssa/phase2d`.
- Manifests v1–v12 store this dictionary, and the runner checks it before training.
- **Consequences:**
  - Moving any historical `run_one_vN.py`, `run_gate2_vN.py`, `gate_vN.py` or
    `gate2_analysis_vN.py` into a subfolder removes it from the hash.
  - Adding a README to this folder adds a file to the hash.
  - Either way, the code no longer matches manifest v12.
- **Resolution:** the folder is left exactly as it is. Its documentation lives outside it: see
  `dssa/README.md` and `docs/organization/04_VERSION_REGISTER.md`.

## D2. Imports by relative path (hard dependency)
- `dssa/phase2d/run_one_v2.py` and `models.py` insert `dssa/train` into `sys.path` through
  `Path(__file__).parent.parent / "train"`.
- Every `run_one_vN.py` imports `run_one_v2` from its own folder.
- The runners call `C.CODE / "run_one_vN.py"` and `verify_reload*.py`.
- **Resolution:** `dssa/train`, `dssa/phase2d` and their relative position cannot change.

## D3. Hashed train and sanity code (hard dependency)
- Each manifest's `train_and_sanity_code_hash` keys `dssa/train/*.py` by name and
  `dssa/sanity/*.py` as `sanity/<name>`.
- **Resolution:** both folders stay in place.

## D4. Frozen-artifact paths (hard dependency)
`common.frozen_files()`, which `assert_frozen_unchanged()` checks against
`dssa/artifacts/phase2d/gate0/baseline_hashes.json`, lists these paths **relative to the project
root**:
- `dssa/artifacts/phase2c/runs/run00{0..4}_*/` (`result.json` and `*_best.pt`)
- `dssa/config/phase2b_training_protocol.json`
- `dssa/artifacts/splits/vaihingen_target_split_manifest.json`
- `dssa/artifacts/dss/phase2b_final_dss_results.json`
- `dssa/artifacts/radiometric_transform.json`
- `dssa/artifacts/phase2c/phase2c_batch1_checkpoint_report.json`

Further paths are hard-coded:
- `common.py` reads `dssa/artifacts/dataset_integrity_raw.json`.
- `gate_v2.py` and later writers hash the protocol JSON as `protocol_file_hash`.

**Resolution:** all of these stay in place.

## D5. Phase 2D artifact layout (hard dependency)
These locations are fixed in code:
- `C.ART = dssa/artifacts/phase2d`
- `C.RUNS = …/runs`
- `C.GATE0 = …/gate0`
- `C.BASELINE = …/gate0/baseline_hashes.json`

How they are used:
- **Recorded hashes:** the manifests record hashes of run folders, partial folders and incident
  reports by run ID or file name under these locations.
- **Run IDs:** `gate2_analysis.py` resolves runs by ID under `RUNS`.
- **Tile check:** `locked_test_untouched()` iterates over **every** folder in `RUNS`, so adding a
  folder there would also change what it checks.
- **Backup:** the established backup procedure archives `dssa/phase2d`, `dssa/artifacts/phase2d`
  and `.gitignore` by these paths.

**Resolution:** the folder stays in place, and no file was added to or removed from it.

## D6. Bare-name citations of root documents (soft dependency, frozen text)
The root design documents cite each other, and are cited by frozen code and reports, **by bare file
name**, which is read as the project root:

| Document | Cited by |
|---|---|
| `DSSA_PROJECT_FREEZE.md` | 17 files, including the Phase 2D Gate 2 final report |
| `DSSA_IMPLEMENTATION_FREEZE.md` | 13 files, including `dssa/sanity/*.py` docstrings and `dssa/configs/sanity_config.yaml` |
| `DSSA_PREIMPLEMENTATION_CALIBRATION.md` | 11 files, including `dssa/artifacts/radiometric_transform.json`, which is frozen |
| `DSSA_PHASE2B_B_TRAINING_PROTOCOL_FREEZE.md` | 9 files, including `dssa/train/*.py` docstrings, which are hashed |

Moving these documents into a `docs/protocols/` folder would leave hashed code and frozen artifacts
pointing to a location where the file no longer is, and those citing files cannot be edited.
**Resolution:** the root documents stay at the root. They are categorized through `docs/browse/`
links instead.

## D7. Git-tracked files (repository state)
- 70 files are tracked at HEAD `3551dbf`, including every root document, `dssa/train`,
  `dssa/sanity`, `dssa/reports`, `dssa/config(s)`, `dssa/checkpoint/*.py` and the Phase 2C
  evidence.
- Moving them without committing, and commits are not permitted, would leave the working tree
  showing deletions and untracked copies.
- **Resolution:** none were moved. The only additions are untracked documentation:
  - `README.md`
  - `dssa/README.md`
  - `docs/`

## D8. Data and model weights (excluded by rule)
| Path | Treatment |
|---|---|
| `dssa/Data/` (65 GB; Potsdam, Vaihingen and their ZIP files) | Contains the locked test set. Listed at the top level only; not opened or hashed |
| `dssa/checkpoint/Prithvi_EO_V2_300M.pt` | Pretrained backbone, loaded by path from `dssa/checkpoint/`. Hashed in place, not moved |
| `dssa/venv/` | Python environment with absolute interpreter paths. Not inventoried file by file; not moved |

## Remaining unresolved items (need a research-lead decision)
1. A physical reorganization, for example moving the root documents into `docs/`, would need a
   commit that is explicitly authorized. It would also need a decision on whether the
   bare-name citations in frozen files are acceptable once they no longer resolve.
2. The `__pycache__` folders under `dssa/train`, `dssa/sanity` and `dssa/checkpoint`, and the
   `.DS_Store` files, are generated clutter. They were left in place because the rules forbid
   deleting files.
