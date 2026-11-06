# Final organization report

Date: 2026-11-05. Scope: `~/Documents/Major project/`.
- Training and evaluation: none run.
- Locked test set: not opened.
- Git: no commit and no push.

## Summary
- **Inventory:** the project was inventoried in full. 1,088 files were hashed, excluding `.git/`,
  `venv/` and the licensed `Data/`.
- **History:** reconstructed from the code, manifests, status files and incident records.
- **Physical moves: none.** The dependency analysis showed that every meaningful move would break a
  reproducibility check or a frozen reference:
  - the `dssa/phase2d/` code hash recorded in manifests v1–v12, which the runner enforces
  - relative imports
  - the frozen-artifact path list
  - manifest-recorded hashes of incident reports and partial run folders
  - bare-name citations of root documents inside hashed code
- **Organization added as a navigation layer**, with nothing moved, overwritten or deleted:
  - `README.md` (root) and `dssa/README.md`
  - `docs/organization/`: deliverables 1–9
  - `docs/browse/`: a categorized view made of 158 relative symbolic links
- **Integrity after the change: PASS** on all 14 checks (`06_INTEGRITY_VERIFICATION.md`).

## Deliverables
| # | Deliverable | File |
|---|---|---|
| 1 | Complete original folder inventory (path, size, SHA-256) | `01_ORIGINAL_INVENTORY.tsv` |
| 2 | Final organized folder tree | `02_ORGANIZED_TREE.md` |
| 3 | File movement and rename map (none; considered moves and why they were rejected) | `03_MOVE_AND_RENAME_MAP.md` |
| 4 | Historical version register | `04_VERSION_REGISTER.md` |
| 5 | Documentation index | `05_DOCUMENTATION_INDEX.md` |
| 6 | Frozen artifact integrity verification | `06_INTEGRITY_VERIFICATION.md` |
| 7 | Duplicates (8 exact groups, all intentional or boilerplate; none deleted) | `07_DUPLICATES.md` |
| 8 | Unresolved path dependencies | `08_UNRESOLVED_PATH_DEPENDENCIES.md` |
| 9 | This report | `09_ORGANIZATION_REPORT.md` |

## What the inventory found
| Category | Count | Location |
|---|---|---|
| Phase 2D Python source (including all versions) | 57 `.py` files | `dssa/phase2d/` |
| Phase 2D addenda (approved protocol) | 2 | `dssa/phase2d/` |
| Phase 2B-C training code | 13 | `dssa/train/` |
| Sanity and DSS code | 9 | `dssa/sanity/` |
| Model reference code | 2 + config | `dssa/checkpoint/` |
| Manifests | 14 (v1–v12 + 2 unused drafts) | `dssa/artifacts/phase2d/` |
| Status files | 11 | `dssa/artifacts/phase2d/` |
| Run folders | 85 (75 complete; 10 interrupted or aborted) | `dssa/artifacts/phase2d/runs/` |
| Incident records | 10 | `dssa/artifacts/phase2d/logs/` |
| Gate 2 reports, audits and launch records | 18 Markdown + 14 JSON | `dssa/artifacts/phase2d/gate2/` |
| Signal and health test evidence sets | 6 folders | `dssa/artifacts/phase2d/gate2/v*_signal*` |
| Root design freezes and audits | 9 Markdown | project root |
| Phase reports | 6 | `dssa/reports/` |
| Presentation materials | 4 | project root |
| Frozen earlier-phase artifacts | 15 files checked by hash | `dssa/artifacts/{phase2c,dss,splits}`, `dssa/config` |
| Off-machine backups | private draft release 431538319: 5 archive generations + checksums | GitHub (see the backup record) |

## Version history in one paragraph
There are **12 manifest versions**, not 11:
- **Pilot:** v1 to v3.
- **Gate 2:** v4 is the original 63-run design. v5 to v12 are recovery manifests.
- **Unused drafts:** two, both kept: `manifest_pilot_v2_draft_unused_bug.json` and
  `manifest_gate2_recovery_v10__superseded_lid_stop.json`.

Each recovery version carries the remaining runs forward and gives the one interrupted run a new
`_a2` ID. It changes **only execution safety**:
- v5: guards
- v6: VM check
- v7: VM check advisory
- v8: signal repair
- v10: closed lid advisory and health watchdogs

No version changes the experimental protocol. Every completion is attributable to exactly one
version: 1 + 4 + 1 + 16 + 2 + 10 + 5 + 7 + 17 = 63 Gate 2 runs, plus 12 pilot runs. The result of
record was produced by `gate2_analysis_v12.py` → `gate2_analysis.py`.

## Distinctions made explicit
| Distinction | Where it is recorded |
|---|---|
| Current vs historical implementation | `04_VERSION_REGISTER.md` §1; `docs/browse/09_code_current_gate2` vs `10_code_historical_versions` |
| Approved protocols vs exploratory documents | `05_DOCUMENTATION_INDEX.md` §2–3; `docs/browse/01_…` vs `02_…` |
| Frozen results vs temporary outputs | `dssa/README.md` folder table; `08_…` D4–D5 |
| Final findings vs intermediate reports | `05_…` §5; `docs/browse/04_…` vs `05_…` |
| Original vs revised scripts | `04_…` (frozen base files vs `_vN` wrappers) |

## Items left for a research-lead decision
1. **Physical reorganization**, such as moving root documents into `docs/`. This needs an authorized
   commit and acceptance that bare-name citations inside frozen files will no longer resolve to the
   same folder.
2. **Committing Phase 2D.** `dssa/phase2d/`, `dssa/artifacts/phase2d/` and the new documentation are
   untracked. The `.gitignore` rule already excludes `*.pt` and `*.npz` under Phase 2D.
3. **Generated clutter** (`__pycache__/`, `.DS_Store`). It was left in place because deletion is not
   permitted.
4. **Presentation materials predate the results.** They do not reflect the Gate 2 conclusion.
