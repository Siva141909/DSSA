# DSSA: Domain Sensitivity Score for selective LoRA adaptation

Major project. Research question: can layer-wise representation drift, measured from a frozen
geospatial foundation model (Prithvi-EO-2.0-300M) using unlabeled target images, identify which
transformer layers are worth adapting with LoRA? The frozen question and hypothesis are in
`DSSA_PROJECT_FREEZE.md` §A–B.

## Result of record
**`dssa/artifacts/phase2d/gate2/GATE2_FINAL_REPORT.md`** (2026-11-05). This is the Gate 2 oracle
layer-utility sweep: 63 single-layer runs plus 12 pilot runs, across 3 seeds.

- **Verdict:** the hypothesis is not supported in the part Gate 2 tests.
  - DSS layer rankings are no better than random at top-k.
  - Their correlation with utility is explained by depth.
  - Layer utility peaks at mid-depth (L11–L17).
- **Untested:** the efficiency and competitiveness part, against uniform LoRA and full
  fine-tuning.
- **Data:** `dssa/artifacts/phase2d/gate2/gate2_analysis.json`.

## Folder layout
| Path | Contents |
|---|---|
| `DSSA_*.md` (root) | Design freezes and pre-freeze audits (Sept 2026). The freeze documents are approved protocols, cited by bare name from frozen code, so they stay at the root |
| `DSSA_Final_Project_Abstract.pdf`, `DSSA_HOD_Presentation.pptx`, `PRESENTATION_SCRIPT.md`, `RGUKT Logo.png` | Presentation materials (pre-results) |
| `dssa/` | All code, configuration, evidence and data. See **`dssa/README.md`** |
| `docs/organization/` | Project archive documentation: inventory, version register, documentation index, integrity verification, dependency analysis, organization report |
| `docs/browse/` | A **categorized view** of the project made of relative symbolic links (start at `docs/browse/00_START_HERE/`). The originals stay in place; nothing in `browse` is a copy |
| `.git/`, `.gitignore` | Private repository `Siva141909/DSSA`. HEAD is `3551dbf` (Phase 2C). Phase 2D is not committed yet |

## Which file is current?
`docs/organization/04_VERSION_REGISTER.md` lists every versioned script and manifest, and which
version actually ran. In short:
- **Final Gate 2 execution:** `manifest_gate2_recovery_v12.json`, run by `run_gate2_v12.py` →
  `run_one_v12.py` → `run_one_v2.main`.
- **Final analysis:** `gate2_analysis_v12.py`, a wrapper around the frozen `gate2_analysis.py`.

## Installing the data and model weights (not in Git)
Datasets, labels, pretrained weights and the Python environment are **excluded from Git** by
`.gitignore`. The excluded paths are:
- `dssa/Data/`, `dssa/data/`
- `dssa/checkpoint/*.pt`, `dssa/checkpoint/.cache/`
- `dssa/reference_sample/`
- `dssa/venv/`
- `*.pt` and `*.npz` under `dssa/artifacts/phase2c/` and `dssa/artifacts/phase2d/`
- per-run `telemetry.jsonl` (kept in the private release backup)

To reproduce, install the data and weights locally as follows.

### 1. ISPRS Potsdam and Vaihingen (licence-restricted)
1. Request access through the ISPRS data request form (`www2.isprs.org/data-request-form.html`),
   for the **2D Semantic Labeling Contest, Potsdam and Vaihingen**.
2. Download the official archives into **`dssa/Data/`**, keeping the ISPRS release structure:
   - `dssa/Data/Potsdam/`: includes `3_Ortho_IRRG.zip`
   - `dssa/Data/Vaihingen/`: includes `ISPRS_semantic_labeling_Vaihingen.zip` and
     `ISPRS_semantic_labeling_Vaihingen_ground_truth_COMPLETE.zip`
3. The code reads from **`dssa/data/`** (lowercase). On macOS, which is case-insensitive,
   `dssa/Data/` and `dssa/data/` are the same folder. On Linux, use `dssa/data/` as the folder name
   everywhere, or create the symbolic link `dssa/data -> Data`.

   Stage the imagery tiles exactly as described in `dssa/reports/DSSA_DATASET_INTEGRITY_REPORT.md` §6:

   | Folder | Contents | Source |
   |---|---|---|
   | `dssa/data/potsdam_irrg/` | 38 files `top_potsdam_<row>_<col>_IRRG.tif` | `3_Ortho_IRRG.zip`; `.tfw` files dropped |
   | `dssa/data/vaihingen_irrg/` | 33 files `top_mosaic_09cm_area<N>.tif` | the `top/` folder of `ISPRS_semantic_labeling_Vaihingen.zip` |
   | `dssa/data/Vaihingen/ISPRS_semantic_labeling_Vaihingen_ground_truth_COMPLETE.zip` | Labels; read directly from the ZIP by `dssa/train/dataset.py` | the download, kept as is |

4. The expected per-file shapes are recorded in `dssa/artifacts/dataset_integrity_raw.json`. The
   locked train/validation/test split is in `dssa/artifacts/splits/vaihingen_target_split_manifest.json`.
   **Never open the locked test tiles.**
5. Never commit, upload or redistribute these files. See
   `dssa/artifacts/phase2d/gate0/backup/ISPRS_LICENSING_POSITION.md`.

### 2. Prithvi-EO-2.0-300M backbone weights
- Download `Prithvi_EO_V2_300M.pt` from the Hugging Face repository
  `ibm-nasa-geospatial/Prithvi-EO-2.0-300M`.
- Place it at **`dssa/checkpoint/Prithvi_EO_V2_300M.pt`**, which is loaded by `dssa/sanity/model.py`.
- The model code in `dssa/checkpoint/` (`prithvi_mae.py`, `config.json`, `requirements.txt`) is
  tracked.
- The fingerprint of the loaded backbone parameters is recorded as `backbone_fp` in
  `dssa/artifacts/phase2d/gate0/baseline_hashes.json` and the Phase 2D manifests. Use it to confirm
  the correct weights.

### 3. Python environment
- Python 3.12, installed as a virtual environment at `dssa/venv/`. Phase 2D scripts are run as
  `../venv/bin/python -B <script>` from `dssa/phase2d/`.
- Package requirements are in `dssa/checkpoint/requirements.txt`: torch, torchvision, timm and others.

## Rules for anyone working here
- **Do not move, rename or add files in `dssa/phase2d/`.** Its code hash is recorded in every
  manifest, and the runner refuses to train if it changes.
- **Do not edit anything under `dssa/artifacts/phase2c/`, `dssa/artifacts/phase2d/`,
  `dssa/config/`, `dssa/artifacts/splits/` or `dssa/artifacts/dss/`.** These are frozen evidence,
  checked by hash.
- **Never open the locked test tiles** listed in `dssa/artifacts/splits/vaihingen_target_split_manifest.json`.
- **Imagery and labels (`dssa/Data/`) are licence-restricted.** Never upload or commit them. See
  `dssa/artifacts/phase2d/gate0/backup/ISPRS_LICENSING_POSITION.md`.

## Backups
Private GitHub draft release 431538319 (tag `backup-2026-11-02-gate0`) holds the cumulative
archives:
- `phase2d_gate0`
- `phase2d_v2`
- `phase2d_v3`
- `phase2d_pilot_final`
- `phase2d_gate2_final` (Gate 2 final)

Each comes with its `SHA256SUMS*` file.
