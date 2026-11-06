# File movement and rename map

## Moves and renames performed: **none**
| Original path | New path | Reason |
|---|---|---|
| — | — | No existing file was moved, renamed, edited, overwritten or deleted |

Every candidate move was assessed against the path dependencies in
`08_UNRESOLVED_PATH_DEPENDENCIES.md` (D1–D8). Each one was blocked:
- Some are hard dependencies: the code hash, imports, frozen-artifact paths and manifest hashes.
- Some are frozen bare-name citations that cannot be edited.
- The rest are git-tracked files that can't be moved without a commit, which is not authorized.

`06_INTEGRITY_VERIFICATION.md` verifies that every original file is still at its original path with
its original SHA-256.

## Moves considered and rejected
| Candidate | Proposed destination | Blocked by |
|---|---|---|
| Historical `dssa/phase2d/*_v2…v11.py` | `dssa/phase2d/history/` | D1: code hash in manifests v1–v12; the runner refuses to train when it differs |
| `dssa/phase2d/PHASE2D_ADDENDUM*.md` | `docs/protocols/` | D1: `*.md` files in `phase2d/` are part of the code hash |
| Root `DSSA_*FREEZE*.md` and audits | `docs/protocols/`, `docs/audits/` | D6: cited by bare name from hashed `dssa/train/*.py` and `dssa/sanity/*.py` docstrings and from the frozen `radiometric_transform.json`; D7: git-tracked |
| `dssa/reports/*.md` | `docs/reports/` | D7: git-tracked; cited by later reports |
| Gate 2 reports in `dssa/artifacts/phase2d/gate2/` | `docs/reports/gate2/` | D5: inside the hashed, backed-up evidence tree; cited by incident reports and manifests |
| `INCIDENT_*.md` | `docs/incidents/` | D5: the hash of each incident report is recorded in the manifests (`incident_report_sha256`) and checked by `gate_v*.py` |
| Old manifests and status files | `…/archive/` | D5: the manifest chain verifies earlier manifests by path and hash |
| Interrupted run folders | `runs/_interrupted/` | D5: their file hashes are recorded in the manifests by run ID; `locked_test_untouched()` scans `runs/` |
| Presentation files (PDF, PPTX, script, logo) | `docs/presentation/` | D7: git-tracked; `DSSA_ABSTRACT_GAP_ANALYSIS.md` cites the PDF by bare name. The benefit is small next to a dirty working tree |
| `__pycache__/`, `.DS_Store` | delete | Not permitted (no deletions) |

## Additions (new files only, all untracked; nothing existing touched)
| Path | Purpose |
|---|---|
| `README.md` | Root README |
| `dssa/README.md` | DSSA README. Outside `dssa/phase2d/`, so it does not affect the code hash |
| `docs/organization/01_ORIGINAL_INVENTORY.tsv` … `09_ORGANIZATION_REPORT.md` | Archive documentation (deliverables 1–9) |
| `docs/browse/` (14 folders, 158 relative symbolic links) | Categorized navigation view. The links point to the originals; there are no copies |

The organization adds nothing inside `dssa/phase2d/`, `dssa/artifacts/`, `dssa/train/`,
`dssa/sanity/`, `dssa/config/` or `dssa/Data/`.
