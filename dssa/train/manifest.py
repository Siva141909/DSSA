"""
DSSA Phase 2C - experiment manifest.

Builds the 42 condition-slots -> 39 unique-run deduplication directly from
the frozen dssa/config/phase2b_training_protocol.json (experimental_conditions
.layer_sets), rather than hand-copying numbers - so any accidental drift from
the frozen JSON would show up as a mismatch against the pre-registered counts
(42 slots, 39 unique runs), not silently.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "phase2b_training_protocol.json"

TRAINING_SEED = 1000
N_LAYERS = 24


def load_protocol() -> dict:
    with open(CONFIG_PATH) as f:
        return json.load(f)


def build_condition_slots(protocol: dict) -> list[dict]:
    ec = protocol["experimental_conditions"]
    layer_sets = ec["layer_sets"]
    slots = []
    slots.append({"label": "K0_decoder_only", "K": 0, "layers": []})
    slots.append({"label": "K24_all", "K": N_LAYERS, "layers": list(range(N_LAYERS))})
    for k_str, conds in layer_sets.items():
        K = int(k_str.split("=")[1])
        for cond_name, layers in conds.items():
            if cond_name.startswith("RandomK_seed"):
                seed = int(cond_name.replace("RandomK_seed", ""))
                label = f"RandomK_seed{seed}@K{K}"
            else:
                label = f"{cond_name}@K{K}"
            slots.append({"label": label, "K": K, "layers": sorted(layers)})
    return slots


def dedup_runs(slots: list[dict]) -> list[dict]:
    groups: dict[tuple, list[str]] = {}
    for s in slots:
        key = (s["K"], tuple(s["layers"]))
        groups.setdefault(key, []).append(s["label"])
    runs = []
    for i, (key, labels) in enumerate(sorted(groups.items(), key=lambda kv: (kv[0][0], kv[1]))):
        K, layers = key
        primary_names = sorted({l.split("@")[0] for l in labels})
        run_id = f"run{i:03d}_K{K}_" + "_".join(primary_names)
        runs.append({
            "run_id": run_id,
            "K": K,
            "layer_indices": list(layers),
            "condition_labels": sorted(labels),
            "is_collision": len(labels) > 1,
            "training_seed": TRAINING_SEED,
        })
    return runs


def build_manifest() -> dict:
    protocol = load_protocol()
    slots = build_condition_slots(protocol)
    runs = dedup_runs(slots)
    collisions = [r for r in runs if r["is_collision"]]
    return {
        "total_condition_slots": len(slots),
        "unique_training_runs": len(runs),
        "expected_total_condition_slots": protocol["experimental_conditions"]["total_condition_slots"],
        "expected_unique_training_runs": protocol["experimental_conditions"]["unique_training_runs_required"],
        "runs": runs,
        "collisions": collisions,
    }


if __name__ == "__main__":
    m = build_manifest()
    print(f"total_condition_slots={m['total_condition_slots']} (expected {m['expected_total_condition_slots']})")
    print(f"unique_training_runs={m['unique_training_runs']} (expected {m['expected_unique_training_runs']})")
    assert m["total_condition_slots"] == m["expected_total_condition_slots"]
    assert m["unique_training_runs"] == m["expected_unique_training_runs"]
    print("\ncollision runs:")
    for r in m["collisions"]:
        print(f"  {r['run_id']}: {r['condition_labels']}")
