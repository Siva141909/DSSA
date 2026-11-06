"""Writes manifest v3. Earlier manifests are preserved and referenced by hash."""
import json
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

C.install_guards()
ORDER = [(12, 1000), (23, 1000), (None, 2000), (0, 2000), (12, 2000), (23, 2000), (None, 3000), (0, 3000), (12, 3000), (23, 3000)]
est = lambda l: 1467 if l is None else round(1472 + 34.6 * (24 - l))
proto, add, frz, eq = (C.sha256_file(p) for p in (C.ROOT / "config" / "phase2b_training_protocol.json", C.CODE / "PHASE2D_ADDENDUM_V2.md", C.GATE0 / "frozen_rankings.json", C.GATE0 / "equivalence_v2.json"))
runs = []
for l, s in ORDER:
    rid = f"p2d_ctrl_K0_s{s}" if l is None else f"p2d_oracle_L{l:02d}_s{s}"
    e = {"run_id": rid, "K": 0 if l is None else 1, "layer_indices": [] if l is None else [l], "training_seed": s, "lora_init_seed": s + C.LORA_SEED_OFFSET,
         "condition_labels": ["K0_control"] if l is None else [f"Oracle_L{l:02d}"], "protocol_file_hash": proto, "addendum_sha256": add, "frozen_rankings_sha256": frz, "equivalence_sha256": eq,
         "cache": "TargetSegDatasetU8", "phase": "2D-pilot-v3", "est_seconds": est(l)}
    e["config_hash"] = C.config_hash(e)
    runs.append(e)
done = {r: json.load(open(C.RUNS / r / "hashes.json")) for r in ("p2d_ctrl_K0_s1000", "p2d_oracle_L00_s1000_a3")}
C.write_json_atomic(C.ART / "manifest_pilot_v3.json", {"authorization": "Exactly these 10 runs. No other training.", "version": 3, "manifest_v1_sha256": C.sha256_file(C.MANIFEST), "manifest_v2_sha256": C.sha256_file(C.ART / "manifest_pilot_v2.json"),
                                                        "completed_runs_kept": done, "code_hash": C.code_hash(), "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=C.PROJECT, capture_output=True, text=True).stdout.strip(), "runs": runs})
print("manifest v3:", [r["run_id"] for r in runs], "est h", sum(r["est_seconds"] for r in runs) / 3600)
