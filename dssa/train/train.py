"""
DSSA Phase 2C - single-run training loop.

Executes exactly the frozen protocol (dssa/config/phase2b_training_protocol.json):
AdamW, lr=1e-3, cosine decay w/ 100-step warmup, 2000 total steps, batch=8,
fp32, grad-clip 1.0, checkpoint/validate every 200 steps, best-by-validation-
mIoU checkpoint retained (deterministic tie-break: strictly greater only, so
an exact tie keeps the earlier checkpoint), training seed=1000 for every
condition.

`total_steps`/`checkpoint_every`/`val_files_override` are exposed ONLY so
preflight.py can run a tiny, clearly-labeled implementation dry run (a
handful of steps, optionally on a single validation file to bound runtime) -
the real Phase 2C matrix always calls this with the frozen 2000/200/all-5
values. No scientific-protocol logic differs between the two call sites.
"""
from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dataset import TargetSegDataset  # noqa: E402
from model_wrapper import build_model, count_total, count_trainable  # noqa: E402
from losses import CEDiceLoss  # noqa: E402
from metrics import ConfusionMatrixAccumulator  # noqa: E402
from tiling import sliding_window_predict  # noqa: E402
from checkpoint import save_checkpoint  # noqa: E402
from efficiency import WallClockTimer, reset_peak_memory, peak_memory_mb, hardware_info  # noqa: E402
import lora as lora_mod  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SPLIT_MANIFEST = ROOT / "artifacts" / "splits" / "vaihingen_target_split_manifest.json"

TRAINING_SEED = 1000
LR = 1e-3
BETAS = (0.9, 0.999)
WEIGHT_DECAY = 0.01
WARMUP_STEPS = 100
TOTAL_STEPS = 2000
BATCH_SIZE = 8
GRAD_CLIP_NORM = 1.0
CHECKPOINT_EVERY = 200


def set_all_seeds(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def load_split(name: str) -> list[str]:
    with open(SPLIT_MANIFEST) as f:
        manifest = json.load(f)
    return manifest["partitions"][name]


def cosine_lr(step: int, total_steps: int, warmup_steps: int, base_lr: float) -> float:
    if step < warmup_steps:
        return base_lr * (step + 1) / warmup_steps
    progress = (step - warmup_steps) / max(1, total_steps - warmup_steps)
    progress = min(max(progress, 0.0), 1.0)
    return base_lr * 0.5 * (1 + math.cos(math.pi * progress))


def make_batch(dataset: TargetSegDataset, batch_size: int, device: str):
    xs, ys = [], []
    for _ in range(batch_size):
        x, y, _ = dataset[0]
        xs.append(x)
        ys.append(y)
    x_batch = torch.stack(xs).to(device)
    y_batch = torch.stack(ys).to(device)
    return x_batch, y_batch


def evaluate(model, filenames: list[str], device: str, eval_max_size: int | None = None) -> dict:
    ds = TargetSegDataset(filenames, mode="eval", eval_max_size=eval_max_size)
    cm = ConfusionMatrixAccumulator()
    model.eval()
    for i in range(len(ds)):
        calibrated, label_idx, filename = ds[i]
        pred = sliding_window_predict(model, calibrated, device)
        assert pred.shape == label_idx.shape, f"{filename}: pred shape {pred.shape} != label shape {label_idx.shape}"
        cm.update(pred, label_idx)
    return cm.compute()


def run_training(run_spec: dict, device: str, out_dir: Path,
                  total_steps: int = TOTAL_STEPS, checkpoint_every: int = CHECKPOINT_EVERY,
                  warmup_steps: int = WARMUP_STEPS, val_files_override: list[str] | None = None,
                  eval_max_size: int | None = None,
                  preflight: bool = False, log=print) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    seed = run_spec.get("training_seed", TRAINING_SEED)
    set_all_seeds(seed)

    layer_indices = sorted(run_spec["layer_indices"])
    model, lora_modules = build_model(layer_indices, device=device)

    lora_mod.assert_only_intended_trainable(model.encoder, set(layer_indices))

    total_params = count_total(model)
    trainable_params = count_trainable(model)
    decoder_params = sum(p.numel() for p in model.decoder.parameters())
    lora_params = sum(lm.lora_param_count() for lm in lora_modules)
    assert trainable_params == decoder_params + lora_params, \
        f"trainable={trainable_params} != decoder={decoder_params}+lora={lora_params}"

    train_files = load_split("target_train")
    val_files = val_files_override if val_files_override is not None else load_split("target_validation")
    test_files = load_split("target_test")
    assert not (set(val_files) & set(test_files)), "target-test file leaked into validation set"
    train_ds = TargetSegDataset(train_files, mode="train", seed=seed)

    trainable = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(trainable, lr=LR, betas=BETAS, weight_decay=WEIGHT_DECAY)
    loss_fn = CEDiceLoss()

    reset_peak_memory(device)
    history = []
    best_val_miou = -1.0
    best_step = None
    best_ckpt_path = out_dir / f"{run_spec['run_id']}_best.pt"

    log(f"[{run_spec['run_id']}] layers={layer_indices} trainable={trainable_params} "
        f"(decoder={decoder_params}, lora={lora_params}) device={device} "
        f"total_steps={total_steps} checkpoint_every={checkpoint_every} val_files={len(val_files)}")

    with WallClockTimer() as timer:
        for step in range(total_steps):
            model.train()
            lr = cosine_lr(step, total_steps, warmup_steps, LR)
            for g in optimizer.param_groups:
                g["lr"] = lr

            x_batch, y_batch = make_batch(train_ds, BATCH_SIZE, device)
            optimizer.zero_grad(set_to_none=True)
            logits = model(x_batch)
            assert logits.shape == (BATCH_SIZE, 6, 224, 224), f"unexpected logits shape {logits.shape}"
            loss = loss_fn(logits, y_batch)
            if not torch.isfinite(loss):
                raise RuntimeError(f"non-finite loss at step {step}: {loss.item()}")
            loss.backward()
            grad_norm = torch.nn.utils.clip_grad_norm_(trainable, GRAD_CLIP_NORM)
            if not torch.isfinite(grad_norm):
                raise RuntimeError(f"non-finite grad norm at step {step}: {grad_norm}")
            optimizer.step()

            is_checkpoint_step = ((step + 1) % checkpoint_every == 0) or (step + 1 == total_steps)
            if is_checkpoint_step:
                val_metrics = evaluate(model, val_files, device, eval_max_size=eval_max_size)
                entry = {
                    "step": step + 1,
                    "train_loss": float(loss.item()),
                    "lr": lr,
                    "val_mean_iou": val_metrics["mean_iou"],
                    "val_macro_f1": val_metrics["macro_f1"],
                    "val_pixel_accuracy": val_metrics["pixel_accuracy"],
                    "val_per_class_iou": val_metrics["per_class_iou"],
                }
                history.append(entry)
                log(f"[{run_spec['run_id']}] step={step+1} loss={loss.item():.4f} "
                    f"val_mIoU={val_metrics['mean_iou']:.4f}")
                if val_metrics["mean_iou"] > best_val_miou:
                    best_val_miou = val_metrics["mean_iou"]
                    best_step = step + 1
                    save_checkpoint(best_ckpt_path, model, lora_modules, layer_indices, step + 1,
                                     extra={"val_metrics": val_metrics})

    peak_mem = peak_memory_mb(device)

    result = {
        "run_id": run_spec["run_id"],
        "condition_labels": run_spec["condition_labels"],
        "K": run_spec["K"],
        "layer_indices": layer_indices,
        "training_seed": seed,
        "preflight": preflight,
        "total_steps_executed": total_steps,
        "checkpoint_every": checkpoint_every,
        "parameter_counts": {
            "total_params": total_params,
            "trainable_params": trainable_params,
            "decoder_params": decoder_params,
            "lora_params": lora_params,
            "trainable_percentage": 100.0 * trainable_params / total_params,
        },
        "validation_history": history,
        "best_val_mean_iou": best_val_miou,
        "best_step": best_step,
        "best_checkpoint_path": str(best_ckpt_path) if best_step is not None else None,
        "training_wall_clock_seconds": timer.elapsed_seconds,
        "peak_memory_mb": peak_mem,
        "hardware": hardware_info(),
    }
    return result, model, lora_modules
