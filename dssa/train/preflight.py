"""
DSSA Phase 2C - IMPLEMENTATION PREFLIGHT (not an experimental result).

Verifies the training/evaluation infrastructure end-to-end using a tiny
number of steps, purely to confirm the implementation is correct before the
39-run frozen matrix is authorized and launched. Target-test labels are
never loaded anywhere in this script - only target-train and
target-validation partitions are referenced (plus a disjointness check
against the target-test filename list, which does not load any test image
or label content).

Every check below corresponds 1:1 to an item in the Phase 2C authorization's
"CRITICAL: PRE-FLIGHT BEFORE 39 RUNS" list.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import torch
import torch.nn as nn

sys.path.insert(0, str(Path(__file__).resolve().parent))
from decoder import SegDecoder, EXPECTED_DECODER_PARAMS, count_params  # noqa: E402
from lora import LoRAQKV, EXPECTED_LORA_PARAMS_PER_BLOCK, assert_only_intended_trainable  # noqa: E402
from model_wrapper import build_model, count_total, count_trainable  # noqa: E402
from losses import CEDiceLoss  # noqa: E402
from checkpoint import save_checkpoint, load_checkpoint  # noqa: E402
from metrics import ConfusionMatrixAccumulator  # noqa: E402
import train as train_mod  # noqa: E402
import manifest as manifest_mod  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "artifacts" / "phase2c"
CKPT_DIR = OUT_DIR / "preflight_checkpoints"
PROTOCOL = manifest_mod.load_protocol()

results = []


def check(name: str, fn):
    t0 = time.time()
    try:
        detail = fn()
        results.append({"check": name, "status": "PASS", "detail": detail, "seconds": round(time.time() - t0, 3)})
        print(f"[PASS] {name}  ({time.time()-t0:.2f}s)" + (f" - {detail}" if detail else ""))
        return detail
    except Exception as e:
        results.append({"check": name, "status": "FAIL", "detail": str(e), "seconds": round(time.time() - t0, 3)})
        print(f"[FAIL] {name}: {e}")
        raise


def main():
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"IMPLEMENTATION PREFLIGHT - NOT EXPERIMENTAL RESULT (device={device})\n")
    CKPT_DIR.mkdir(parents=True, exist_ok=True)

    # ---- 0. manifest sanity (42 slots -> 39 unique runs, matches frozen JSON) ----
    def _manifest_check():
        m = manifest_mod.build_manifest()
        assert m["total_condition_slots"] == m["expected_total_condition_slots"] == 42
        assert m["unique_training_runs"] == m["expected_unique_training_runs"] == 39
        return f"42 slots -> 39 unique runs, {len(m['collisions'])} collisions"
    check("experiment manifest matches frozen 42-slot/39-run accounting", _manifest_check)

    # ---- 1. decoder parameter count ----
    def _decoder_count():
        d = SegDecoder()
        n = count_params(d)
        assert n == EXPECTED_DECODER_PARAMS, f"decoder params {n} != expected {EXPECTED_DECODER_PARAMS}"
        return f"{n} params"
    check("decoder parameter count = 2,766,726", _decoder_count)

    # ---- 2. LoRA parameter count per block ----
    def _lora_count():
        dummy = nn.Linear(1024, 3072, bias=True)
        wrapped = LoRAQKV(dummy, rank=8, alpha=16, dropout=0.0)
        n = wrapped.lora_param_count()
        assert n == EXPECTED_LORA_PARAMS_PER_BLOCK, f"lora params {n} != expected {EXPECTED_LORA_PARAMS_PER_BLOCK}"
        return f"{n} params/block"
    check("LoRA parameter count per selected block = 32,768", _lora_count)

    # ---- 3. K=0 model: decoder parameters only, zero LoRA ----
    def _k0_model():
        model, lora_modules = build_model([], device=device)
        assert len(lora_modules) == 0
        assert_only_intended_trainable(model.encoder, set())
        trainable = count_trainable(model)
        decoder_params = sum(p.numel() for p in model.decoder.parameters())
        assert trainable == decoder_params, f"K=0 trainable={trainable} != decoder_params={decoder_params}"
        expected = PROTOCOL["architecture"]["lora"]["parameter_accounting"]["K=0"]["total_trainable"]
        assert trainable == expected, f"K=0 trainable={trainable} != frozen expected {expected}"
        del model
        return f"trainable={trainable} (decoder-only, matches frozen K=0 accounting)"
    check("K=0 model contains decoder parameters only", _k0_model)

    # ---- 4. K=8 model: LoRA on intended Q/V slices only, param count matches frozen accounting ----
    K8_LAYERS = [16, 17, 18, 19, 20, 21, 22, 23]  # DSSA@K8 == Late@K8 (frozen collision) - used here as an
                                                    # IMPLEMENTATION test only, not as an experimental run.
    model8 = None

    def _k8_model():
        nonlocal model8
        model8, lora_modules = build_model(K8_LAYERS, device=device)
        assert len(lora_modules) == 8
        assert_only_intended_trainable(model8.encoder, set(K8_LAYERS))
        total = count_total(model8)
        trainable = count_trainable(model8)
        decoder_params = sum(p.numel() for p in model8.decoder.parameters())
        lora_params = sum(lm.lora_param_count() for lm in lora_modules)
        expected = PROTOCOL["architecture"]["lora"]["parameter_accounting"]["K=8"]["total_trainable"]
        assert trainable == expected, f"K=8 trainable={trainable} != frozen expected {expected}"
        assert trainable == decoder_params + lora_params
        expected_backbone = PROTOCOL["architecture"]["lora"]["backbone_frozen_params"]
        backbone_params = total - decoder_params - lora_params
        assert backbone_params == expected_backbone, f"backbone params {backbone_params} != expected {expected_backbone}"
        return f"total={total} trainable={trainable} (decoder={decoder_params}, lora={lora_params}), backbone_frozen={backbone_params}"
    check("K=8 model: LoRA only on selected Q/V slices, params match frozen accounting", _k8_model)

    # ---- 5/6/7. forward pass shape, loss finite, backward finite ----
    def _forward_backward():
        x = torch.randn(4, 6, 1, 224, 224, device=device)
        y = torch.randint(0, 6, (4, 224, 224), device=device)
        model8.train()
        logits = model8(x)
        assert logits.shape == (4, 6, 224, 224), f"unexpected logits shape {logits.shape}"
        loss_fn = CEDiceLoss()
        loss = loss_fn(logits, y)
        assert torch.isfinite(loss), f"non-finite loss {loss}"
        trainable_params = [p for p in model8.parameters() if p.requires_grad]
        loss.backward()
        n_with_grad = sum(1 for p in trainable_params if p.grad is not None)
        assert n_with_grad == len(trainable_params), f"only {n_with_grad}/{len(trainable_params)} trainable params got a grad"
        all_finite = all(torch.isfinite(p.grad).all() for p in trainable_params)
        assert all_finite, "non-finite gradient found"
        model8.zero_grad(set_to_none=True)
        return f"logits shape (4,6,224,224), loss={loss.item():.4f}, {n_with_grad} trainable tensors received finite grads"
    check("forward pass shape correct, loss finite, backward finite", _forward_backward)

    # ---- 8/9. optimizer updates only intended trainable params; frozen backbone unchanged ----
    def _optimizer_isolation():
        backbone_frozen_before = model8.encoder.blocks[0].mlp.fc1.weight.detach().clone()
        lora_frozen_orig_before = model8.encoder.blocks[16].attn.qkv.orig_qkv.weight.detach().clone()
        decoder_before = model8.decoder.final_conv.weight.detach().clone()
        lora_before = model8.encoder.blocks[16].attn.qkv.lora_B_q.detach().clone()

        trainable = [p for p in model8.parameters() if p.requires_grad]
        optimizer = torch.optim.AdamW(trainable, lr=1e-3, betas=(0.9, 0.999), weight_decay=0.01)
        x = torch.randn(4, 6, 1, 224, 224, device=device)
        y = torch.randint(0, 6, (4, 224, 224), device=device)
        model8.train()
        logits = model8(x)
        loss = CEDiceLoss()(logits, y)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(trainable, 1.0)
        optimizer.step()

        backbone_frozen_after = model8.encoder.blocks[0].mlp.fc1.weight.detach()
        lora_frozen_orig_after = model8.encoder.blocks[16].attn.qkv.orig_qkv.weight.detach()
        decoder_after = model8.decoder.final_conv.weight.detach()
        lora_after = model8.encoder.blocks[16].attn.qkv.lora_B_q.detach()

        assert torch.equal(backbone_frozen_before, backbone_frozen_after), "frozen non-LoRA backbone weight changed!"
        assert torch.equal(lora_frozen_orig_before, lora_frozen_orig_after), "frozen original qkv weight changed!"
        assert not torch.equal(decoder_before, decoder_after), "decoder weight did NOT change after optimizer step"
        assert not torch.equal(lora_before, lora_after), "LoRA weight did NOT change after optimizer step"
        return "frozen backbone params bit-identical after optimizer.step(); decoder and LoRA params changed as expected"
    check("optimizer updates only intended trainable params; frozen backbone unchanged", _optimizer_isolation)
    del model8

    # ---- 10. checkpoint save/load reproduces predictions ----
    def _checkpoint_roundtrip():
        layers = [19, 23]
        m1, lora1 = build_model(layers, device=device)
        m1.eval()
        fixed_x = torch.randn(1, 6, 1, 224, 224, device=device)
        with torch.no_grad():
            logits_before = m1(fixed_x).clone()
        ckpt_path = CKPT_DIR / "roundtrip_test.pt"
        save_checkpoint(ckpt_path, m1, lora1, layers, step=1)

        m2, lora2 = build_model(layers, device=device)
        load_checkpoint(ckpt_path, m2, lora2, layers)
        m2.eval()
        with torch.no_grad():
            logits_after = m2(fixed_x).clone()
        assert torch.allclose(logits_before, logits_after, atol=1e-6), "checkpoint round-trip predictions differ!"
        return f"max abs diff = {(logits_before - logits_after).abs().max().item():.2e}"
    check("checkpoint save/load reproduces predictions exactly", _checkpoint_roundtrip)

    # ---- 11/12/13/14. validation inference / tiling / confusion matrix / metrics, via a tiny real run ----
    def _target_test_untouched_check():
        train_files = train_mod.load_split("target_train")
        val_files = train_mod.load_split("target_validation")
        test_files = train_mod.load_split("target_test")
        assert not (set(train_files) & set(test_files))
        assert not (set(val_files) & set(test_files))
        return f"train={len(train_files)} val={len(val_files)} test={len(test_files)} (test filenames only diffed, never loaded)"
    check("target-train/validation partitions disjoint from target-test (test not loaded)", _target_test_untouched_check)

    def _tiny_training_run_k0():
        run_spec = {"run_id": "preflight_K0", "K": 0, "layer_indices": [], "condition_labels": ["K0_decoder_only"],
                    "training_seed": 1000}
        val_files = train_mod.load_split("target_validation")[:1]
        result, model, lora_modules = train_mod.run_training(
            run_spec, device=device, out_dir=CKPT_DIR,
            total_steps=2, checkpoint_every=2, warmup_steps=1,
            val_files_override=val_files, eval_max_size=448, preflight=True, log=lambda m: None,
        )
        assert result["parameter_counts"]["lora_params"] == 0
        assert len(result["validation_history"]) == 1
        return result
    r_k0 = check("tiny end-to-end training run (K=0, decoder-only path)", _tiny_training_run_k0)

    def _tiny_training_run_k8():
        run_spec = {"run_id": "preflight_K8", "K": 8, "layer_indices": K8_LAYERS,
                    "condition_labels": ["DSSA@K8", "Late@K8"], "training_seed": 1000}
        val_files = train_mod.load_split("target_validation")[:1]
        result, model, lora_modules = train_mod.run_training(
            run_spec, device=device, out_dir=CKPT_DIR,
            total_steps=4, checkpoint_every=2, warmup_steps=1,
            val_files_override=val_files, eval_max_size=448, preflight=True, log=lambda m: None,
        )
        assert result["parameter_counts"]["lora_params"] == 262144
        assert len(result["validation_history"]) == 2
        return result
    r_k8 = check("tiny end-to-end training run (K=8, LoRA path, includes checkpointing)", _tiny_training_run_k8)

    def _validation_outputs_valid():
        for name, r in [("K0", r_k0), ("K8", r_k8)]:
            for entry in r["validation_history"]:
                for v in (entry["val_mean_iou"], entry["val_macro_f1"], entry["val_pixel_accuracy"]):
                    assert torch.isfinite(torch.tensor(float(v))), f"{name}: non-finite metric {v}"
                for c in entry["val_per_class_iou"]:
                    assert c is None or 0.0 <= c <= 1.0, f"{name}: per-class IoU out of range: {c}"
        return "all validation metrics finite and in-range across both tiny runs"
    check("validation metrics finite and valid across tiny runs", _validation_outputs_valid)

    # ---- explicit confusion-matrix validity check (independent of the tiny runs above) ----
    def _confusion_matrix_validity():
        import numpy as np
        cm = ConfusionMatrixAccumulator()
        pred = np.random.randint(0, 6, size=(50, 50))
        target = np.random.randint(0, 6, size=(50, 50))
        cm.update(pred, target)
        out = cm.compute()
        mat = np.array(out["confusion_matrix"])
        assert mat.shape == (6, 6)
        assert (mat >= 0).all()
        assert mat.sum() == 2500
        assert np.isfinite(out["mean_iou"])
        assert np.isfinite(out["macro_f1"])
        assert np.isfinite(out["pixel_accuracy"])
        return f"confusion matrix shape=(6,6), sum={int(mat.sum())}, all metrics finite"
    check("confusion matrix is valid (6x6, non-negative, correct pixel count)", _confusion_matrix_validity)

    # ---- summary ----
    n_pass = sum(1 for r in results if r["status"] == "PASS")
    n_fail = sum(1 for r in results if r["status"] == "FAIL")
    report = {
        "label": "IMPLEMENTATION PREFLIGHT - NOT EXPERIMENTAL RESULT",
        "device": device,
        "n_checks": len(results),
        "n_pass": n_pass,
        "n_fail": n_fail,
        "checks": results,
        "tiny_run_k0": r_k0,
        "tiny_run_k8": r_k8,
    }
    with open(OUT_DIR / "phase2c_preflight_report.json", "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\n{n_pass}/{len(results)} checks passed. Report written to {OUT_DIR / 'phase2c_preflight_report.json'}")


if __name__ == "__main__":
    main()
