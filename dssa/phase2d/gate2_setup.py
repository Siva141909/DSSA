"""Gate 2 pre-training checks and manifest v4. Subcommands, in order:
  layers    builds each of the 21 new layers once and checks the LoRA mapping
  equiv     re-runs the v2 8-bit cache equivalence test, into gate2/
  pilot     re-hashes the 12 completed pilot runs against their records
  manifest  writes manifest_gate2_v4.json (v1, v2, v3 are preserved unchanged)
No training happens here."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

C.install_guards()
OUT = C.ART / "gate2"
NEW_LAYERS = [l for l in range(24) if l not in (0, 12, 23)]
PILOT = {("K0", s): f"p2d_ctrl_K0_s{s}" for s in C.PILOT_SEEDS}
PILOT.update({(l, s): ("p2d_oracle_L00_s1000_a3" if (l, s) == (0, 1000) else f"p2d_oracle_L{l:02d}_s{s}") for l in (0, 12, 23) for s in C.PILOT_SEEDS})
est = lambda l: round(1472 + 34.6 * (24 - l))  # same fit as manifests v1 to v3


def layers():
    sys.path.insert(0, str(C.ROOT / "train"))
    import torch
    import lora as lora_mod
    import models as M
    import train as T
    base = json.load(open(C.BASELINE))
    out = {}
    for l in NEW_LAYERS:
        t0 = time.time()
        T.set_all_seeds(1000)  # as run_training does immediately before build_model
        model, mods = M.build([l], "mps", 1000 + C.LORA_SEED_OFFSET)
        lora_mod.assert_only_intended_trainable(model.encoder, {l})
        wrapped = [i for i, b in enumerate(model.encoder.blocks) if isinstance(b.attn.qkv, lora_mod.LoRAQKV)]
        enc_trainable = sorted(n for n, p in model.encoder.named_parameters() if p.requires_grad)
        ok_names = all(n.startswith(f"blocks.{l}.attn.qkv.lora_") for n in enc_trainable) and len(enc_trainable) == 4
        rec = {"wrapped_blocks": wrapped, "encoder_trainable": enc_trainable, "lora_params": sum(m.lora_param_count() for m in mods),
               "B_zero": all(int(torch.count_nonzero(m.lora_B_q)) == 0 and int(torch.count_nonzero(m.lora_B_v)) == 0 for m in mods),
               "A_hash_ok": M.tensor_hash([mods[0].lora_A_q, mods[0].lora_A_v]) == base["expected"]["1000"]["lora_A_hash"],
               "backbone_fp_ok": M.backbone_fingerprint(model) == base["expected_common"]["backbone_fp"],
               "probe_output_unchanged_with_B0": M.probe_output_hash(model, "mps") == base["expected_common"]["probe_hash"],
               "decoder_hash_ok": M.decoder_hash(model.decoder) == base["expected"]["1000"]["decoder_hash"], "seconds": round(time.time() - t0, 1)}
        rec["pass"] = rec["wrapped_blocks"] == [l] and ok_names and rec["lora_params"] == 32768 and all(rec[k] for k in ("B_zero", "A_hash_ok", "backbone_fp_ok", "probe_output_unchanged_with_B0", "decoder_hash_ok"))
        out[l] = rec
        print(l, rec["pass"], rec["seconds"], flush=True)
        del model, mods
        torch.mps.empty_cache()
    # DSS layer k is the output of encoder.blocks[k] (gate0_dss.py forward hooks); LoRA layer k wraps encoder.blocks[k].attn.qkv
    C.write_json_atomic(OUT / "layer_mapping_check.json", {"all_pass": all(v["pass"] for v in out.values()), "layers": out, "seed_used": 1000,
                                                           "note": "Decoder and LoRA A hashes for seeds 2000 and 3000 are asserted again before every run."})
    if not all(v["pass"] for v in out.values()):
        raise SystemExit("LAYER MAPPING CHECK FAILED")


def equiv():
    import gate_v2 as G
    G.OUT = OUT / "equivalence_v4_recheck.json"
    G.equiv()


def pilot():
    rec = json.load(open(C.ART / "pilot_completion_record_v3.json"))
    out, bad = {}, []
    for k, rid in PILOT.items():
        d = C.RUNS / rid
        h = json.load(open(d / "hashes.json"))
        res = json.load(open(d / "result.json"))
        now = {t: C.sha256_file(d / f"{rid}_{t}.pt") for t in ("best", "final")}
        ok = all(now[t] == h["checkpoints"][t]["sha256"] for t in now) and C.sha256_file(d / "result.json") == h["result_sha256"] and res["status"] == "completed" and res["post_run_checks"]["steps"] == 2000
        out[rid] = {"ok": ok, **now}
        bad += [] if ok else [rid]
    C.write_json_atomic(OUT / "pilot_evidence_recheck.json", {"all_ok": not bad, "bad": bad, "runs": out, "completion_record_sha256": C.sha256_file(C.ART / "pilot_completion_record_v3.json"),
                                                              "completion_record_keys": list(rec)[:20]})
    print("pilot evidence", "OK" if not bad else bad)
    if bad:
        raise SystemExit("PILOT EVIDENCE CHANGED")


def manifest():
    for f in ("layer_mapping_check.json", "equivalence_v4_recheck.json", "pilot_evidence_recheck.json", "backup_restore_recheck.json", "pilot_statistical_audit.json"):
        if not (OUT / f).exists():
            raise SystemExit(f"missing pre-training check: {f}")
    if not json.load(open(OUT / "layer_mapping_check.json"))["all_pass"] or not json.load(open(OUT / "pilot_evidence_recheck.json"))["all_ok"]:
        raise SystemExit("pre-training check failed")
    if json.load(open(OUT / "backup_restore_recheck.json")).get("result") != "PASS":
        raise SystemExit("backup restore check did not pass")
    if not json.load(open(OUT / "equivalence_v4_recheck.json"))["result"].startswith("PASS"):
        raise SystemExit("equivalence failed")
    C.assert_frozen_unchanged()
    base = json.load(open(C.BASELINE))
    streams = {str(s): C.simulate_data_stream(s) == base["expected"][str(s)]["data_stream_final"] for s in C.PILOT_SEEDS}
    if not all(streams.values()):
        raise SystemExit("data stream replay differs")
    # the pilot runs used the same per-seed decoder and RNG states that every Gate 2 run must match
    pol = {}
    for (a, s), rid in PILOT.items():
        r = json.load(open(C.RUNS / rid / "result.json"))
        e = base["expected"][str(s)]
        pol[rid] = r["pre_run_checks"]["decoder_hash"] == e["decoder_hash"] and r["pre_run_checks"]["torch_rng_hash"] == e["torch_rng_hash"] and r["entry"]["lora_init_seed"] == s + C.LORA_SEED_OFFSET and r["post_run_checks"]["data_stream_ok"]
    if not all(pol.values()):
        raise SystemExit("pilot runs do not match the paired policy")
    frz = {"protocol": C.ROOT / "config" / "phase2b_training_protocol.json", "addendum_v1": C.CODE / "PHASE2D_ADDENDUM.md", "addendum_v2": C.CODE / "PHASE2D_ADDENDUM_V2.md",
           "frozen_rankings": C.GATE0 / "frozen_rankings.json", "equivalence_v2": C.GATE0 / "equivalence_v2.json", "equivalence_v4_recheck": OUT / "equivalence_v4_recheck.json",
           "split_manifest": C.ROOT / "artifacts" / "splits" / "vaihingen_target_split_manifest.json", "dataset_integrity": C.ROOT / "artifacts" / "dataset_integrity_raw.json",
           "radiometric_transform": C.ROOT / "artifacts" / "radiometric_transform.json", "backbone_weights": C.ROOT / "checkpoint" / "Prithvi_EO_V2_300M.pt",
           "prithvi_mae_py": C.ROOT / "checkpoint" / "prithvi_mae.py", "pilot_completion_record_v3": C.ART / "pilot_completion_record_v3.json",
           "layer_mapping_check": OUT / "layer_mapping_check.json", "backup_restore_recheck": OUT / "backup_restore_recheck.json", "pilot_statistical_audit": OUT / "pilot_statistical_audit.json"}
    train_code = {p.name: C.sha256_file(p) for p in sorted((C.ROOT / "train").glob("*.py"))}
    train_code.update({f"sanity/{p.name}": C.sha256_file(p) for p in sorted((C.ROOT / "sanity").glob("*.py"))})
    runs = []
    for s in C.PILOT_SEEDS:  # seed-major: a complete 24-layer set for seed 1000 exists first
        for l in NEW_LAYERS:
            e = {"run_id": f"p2d_oracle_L{l:02d}_s{s}", "K": 1, "layer_indices": [l], "training_seed": s, "lora_init_seed": s + C.LORA_SEED_OFFSET, "condition_labels": [f"Oracle_L{l:02d}"],
                 "protocol_file_hash": C.sha256_file(frz["protocol"]), "addendum_sha256": C.sha256_file(frz["addendum_v2"]), "frozen_rankings_sha256": C.sha256_file(frz["frozen_rankings"]),
                 "equivalence_sha256": C.sha256_file(frz["equivalence_v2"]), "cache": "TargetSegDatasetU8", "phase": "2D-gate2-v4", "est_seconds": est(l)}
            e["config_hash"] = C.config_hash(e)
            if (C.RUNS / e["run_id"]).exists():
                raise SystemExit(f"{e['run_id']} already exists")
            runs.append(e)
    assert len(runs) == 63 and len({r["run_id"] for r in runs}) == 63
    m = {"authorization": "Gate 2: exactly these 63 single-layer runs (21 layers x seeds 1000, 2000, 3000). No other training.", "version": 4,
         "manifest_v1_sha256": C.sha256_file(C.MANIFEST), "manifest_v2_sha256": C.sha256_file(C.ART / "manifest_pilot_v2.json"), "manifest_v3_sha256": C.sha256_file(C.ART / "manifest_pilot_v3.json"),
         "completed_pilot_runs": {f"{a if a == 'K0' else 'L%02d' % a}_s{s}": r for (a, s), r in PILOT.items()},
         "code_hash": C.code_hash(), "train_and_sanity_code_hash": train_code, "fingerprints": {k: C.sha256_file(p) for k, p in frz.items()},
         "backbone_fp": base["expected_common"]["backbone_fp"], "probe_hash": base["expected_common"]["probe_hash"], "per_seed_expected": base["expected"], "data_stream_replay_ok": streams, "pilot_paired_policy_ok": pol,
         "limits": {"footprint_mb": C.MEM_LIMIT_MB, "swap_growth_mb": C.SWAP_GROWTH_LIMIT_MB, "runtime_factor": 1.5, "pressure": "stop at critical"},
         "failure_policy": "Stop the whole sequence at the first failure. No retry. Partial evidence kept.",
         "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=C.PROJECT, capture_output=True, text=True).stdout.strip(),
         "est_hours": sum(r["est_seconds"] for r in runs) / 3600, "runs": runs}
    C.write_json_atomic(C.ART / "manifest_gate2_v4.json", m)
    print("manifest v4:", len(runs), "runs, est h", round(m["est_hours"], 2))


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    {"layers": layers, "equiv": equiv, "pilot": pilot, "manifest": manifest}[sys.argv[1]]()
