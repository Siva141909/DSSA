# Duplicates register (exact SHA-256 matches; nothing deleted)

Scope: the 1,088 files in `01_ORIGINAL_INVENTORY.tsv`. That excludes `.git/`, `dssa/venv/` and `dssa/Data/`. Empty files are ignored.

**8 groups of byte-identical files.** None of them is research evidence that is duplicated by mistake:

| # | Size (bytes) | Files | Explanation |
|---|---|---|---|
| 1 | 730 | `dssa/artifacts/phase2d/gate2/v10_signal_and_health_tests/dummy_children/verify_reload_v8.py`<br>`dssa/artifacts/phase2d/gate2/v10_signal_tests__superseded_lid_stop/dummy_children/verify_reload_v8.py`<br>`dssa/artifacts/phase2d/gate2/v11_signal_and_health_tests/code/verify_reload_v8.py`<br>`dssa/artifacts/phase2d/gate2/v12_signal_and_health_tests/code/verify_reload_v8.py`<br>`dssa/artifacts/phase2d/gate2/v8_signal_tests/dummy_children/verify_reload_v8.py`<br>`dssa/artifacts/phase2d/gate2/v9_signal_tests/dummy_children/verify_reload_v8.py` | Copies of the dummy reload child script, archived with each signal-test evidence folder (v8–v12). Intentional: each test folder is self-contained evidence |
| 2 | 220 | `dssa/artifacts/phase2d/gate2/v10_signal_and_health_tests/guard_charger/run_files.txt`<br>`dssa/artifacts/phase2d/gate2/v10_signal_and_health_tests/lid_advisory/run_files.txt`<br>`dssa/artifacts/phase2d/gate2/v10_signal_and_health_tests/manual_child_sigint/run_files.txt`<br>`dssa/artifacts/phase2d/gate2/v10_signal_and_health_tests/step_stall/run_files.txt` | File listings of the dummy run folder from different signal tests. They are identical because the tests stopped at the same stage. Intentional evidence |
| 3 | 220 | `dssa/artifacts/phase2d/gate2/v8_signal_tests/child_sigterm/run_files.txt`<br>`dssa/artifacts/phase2d/gate2/v8_signal_tests/guard_charger/run_files.txt`<br>`dssa/artifacts/phase2d/gate2/v8_signal_tests/guard_lid/run_files.txt`<br>`dssa/artifacts/phase2d/gate2/v8_signal_tests/manual_child_sigint/run_files.txt`<br>`dssa/artifacts/phase2d/gate2/v8_signal_tests/seq_sigint/run_files.txt`<br>`dssa/artifacts/phase2d/gate2/v8_signal_tests/seq_sigterm/run_files.txt` | File listings of the dummy run folder from different signal tests. They are identical because the tests stopped at the same stage. Intentional evidence |
| 4 | 220 | `dssa/artifacts/phase2d/gate2/v9_signal_tests/guard_charger/run_files.txt`<br>`dssa/artifacts/phase2d/gate2/v9_signal_tests/manual_child_sigint/run_files.txt` | File listings of the dummy run folder from different signal tests. They are identical because the tests stopped at the same stage. Intentional evidence |
| 5 | 191 | `dssa/checkpoint/.cache/huggingface/CACHEDIR.TAG`<br>`dssa/reference_sample/.cache/huggingface/CACHEDIR.TAG` | Hugging Face cache markers (standard boilerplate) |
| 6 | 168 | `dssa/artifacts/phase2d/gate2/v10_signal_and_health_tests/guard_sleep/run_files.txt`<br>`dssa/artifacts/phase2d/gate2/v10_signal_and_health_tests/guard_thermal/run_files.txt` | File listings of the dummy run folder from different signal tests. They are identical because the tests stopped at the same stage. Intentional evidence |
| 7 | 168 | `dssa/artifacts/phase2d/gate2/v8_signal_tests/guard_sleep/run_files.txt`<br>`dssa/artifacts/phase2d/gate2/v8_signal_tests/guard_thermal/run_files.txt` | File listings of the dummy run folder from different signal tests. They are identical because the tests stopped at the same stage. Intentional evidence |
| 8 | 1 | `dssa/checkpoint/.cache/huggingface/.gitignore`<br>`dssa/reference_sample/.cache/huggingface/.gitignore` | Hugging Face cache markers (standard boilerplate) |

## Known duplicates outside the hashed scope (not opened)
- **`dssa/Data/Potsdam.zip` and `dssa/Data/Vaihingen.zip`** are presumably the source archives of the extracted `Potsdam/`, `Vaihingen/`, `potsdam_irrg/` and `vaihingen_irrg/` folders. They were not opened, because `Data/` contains the locked test set. This is unverified.
- **`docs/browse/`** contains 158 symbolic links, not copies. They point to the original files.

## Near-duplicates by design (different content, same role)
- **`run_one_v3.py` … `run_one_v12.py`, `run_gate2_v5.py` … `run_gate2_v12.py`, `gate_v5.py` … `gate_v12.py`, `gate2_analysis_v5.py` … `_v12.py`:** successive versions. Each is tied by name to the manifest it executed, so none can be merged or removed (see `04_VERSION_REGISTER.md`).
- **`manifest_gate2_recovery_v10.json` and `manifest_gate2_recovery_v10__superseded_lid_stop.json`:** the approved v10 and an unapproved, never-launched draft. Both are kept.
