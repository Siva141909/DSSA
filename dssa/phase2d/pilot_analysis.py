"""Frozen before training. Reads the 12 pilot results; computes the report tables.
Variance sources stay separate: seed (paired across runs), tile (resampled within
a fixed model), crop (DSS only, in frozen_rankings.json). No selector is scored
here: three layers cannot rank 24."""
from __future__ import annotations

import itertools
import json
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
import numpy as np  # noqa: E402

DELTA = 0.010
SEEDS, ARMS = (1000, 2000, 3000), ("K0", "L00", "L12", "L23")
CHI2_6 = (1.2373, 14.4494)  # 2.5% and 97.5% quantiles, df=6
Z975, Z80 = 1.95996, 0.84162


def rid(a, s):
    return f"p2d_ctrl_K0_s{s}" if a == "K0" else f"p2d_oracle_{a}_s{s}"


def miou(cm, classes=6):
    tp = np.diag(cm)
    d = cm.sum(0) + cm.sum(1) - tp
    v = np.where(d > 0, tp / np.maximum(d, 1), np.nan)
    return float(np.nanmean(v[:classes]))


def tile_present_miou(cm):
    tp, gt = np.diag(cm), cm.sum(1)
    d = cm.sum(0) + gt - tp
    return float((tp[gt > 0] / d[gt > 0]).mean())


def stack(ev):
    return np.array([ev["tiles"][f] for f in C.VAL])


def r_required(sigma, multiplier):
    return max(1, math.ceil((multiplier * sigma / DELTA) ** 2))


def main():
    runs = {(a, s): json.load(open(C.RUNS / rid(a, s) / "result.json")) for a in ARMS for s in SEEDS}
    last = {k: stack(v["evals"][-1]) for k, v in runs.items()}
    M6 = np.array([[miou(last[(a, s)].sum(0)) for s in SEEDS] for a in ARMS])
    M5 = np.array([[miou(last[(a, s)].sum(0), 5) for s in SEEDS] for a in ARMS])

    # reproducibility of run000
    r0 = json.load(open(C.P2C / C.P2C_RUNS[0] / "result.json"))
    h0, h1 = [e["val_mean_iou"] for e in r0["train_result"]["validation_history"]], [e["val_mean_iou"] for e in runs[("K0", 1000)]["validation_history"]]
    loss0, loss1 = [e["train_loss"] for e in r0["train_result"]["validation_history"]], [e["train_loss"] for e in runs[("K0", 1000)]["validation_history"]]
    repro = {"val_miou_identical_all_10": h0 == h1, "train_loss_identical_all_10": loss0 == loss1, "max_abs_val_diff": max(abs(a - b) for a, b in zip(h0, h1)),
             "max_abs_loss_diff": max(abs(a - b) for a, b in zip(loss0, loss1)), "best_step": (r0["train_result"]["best_step"], runs[("K0", 1000)]["train_result"]["best_step"]),
             "run000": h0, "repeat": h1}

    # two-way layout: mIoU = arm + seed + residual. df = (4-1)(3-1) = 6
    def anova(Y):
        res = Y - Y.mean(1, keepdims=True) - Y.mean(0, keepdims=True) + Y.mean()
        s2 = (res ** 2).sum() / 6
        return float(np.sqrt(s2)), float(Y.mean(0).std(ddof=1))
    sigma_e, sd_seed_means = anova(M6)
    sigma_contrast = math.sqrt(2) * sigma_e  # SD of a same-seed arm-minus-arm difference
    lo, hi = sigma_contrast * math.sqrt(6 / CHI2_6[1]), sigma_contrast * math.sqrt(6 / CHI2_6[0])
    sigma5, _ = anova(M5)
    U6 = {a: (M6[i] - M6[0]).tolist() for i, a in enumerate(ARMS) if i}
    U5 = {a: (M5[i] - M5[0]).tolist() for i, a in enumerate(ARMS) if i}
    arms = {a: {"mean": float(np.mean(v)), "sd_seed_df2": float(np.std(v, ddof=1)), "values": v, "t95_halfwidth": float(4.303 * np.std(v, ddof=1) / math.sqrt(3)),
                "mean_5class": float(np.mean(U5[a])), "values_5class": U5[a]} for a, v in U6.items()}
    pairs = {f"{a}-{b}": (M6[ARMS.index(a)] - M6[ARMS.index(b)]).tolist() for a, b in itertools.combinations(ARMS[1:], 2)}

    # tile uncertainty within each seed, all 3,125 ordered resamples
    idx = np.array(list(itertools.product(range(5), repeat=5)))

    def tile_boot(a, b, s):
        A, B = last[(a, s)], last[(b, s)]
        d = [miou(A[i].sum(0)) - miou(B[i].sum(0)) for i in idx]
        return float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))
    tile = {f"{a}-K0_s{s}": tile_boot(a, "K0", s) for a in ARMS[1:] for s in SEEDS}
    tile.update({f"L23-L00_s{s}": tile_boot("L23", "L00", s) for s in SEEDS})
    widths = [(h - l) / 2 for l, h in tile.values()]
    per_tile = {f"{a}_s{s}": [tile_present_miou(last[(a, s)][i]) - tile_present_miou(last[("K0", s)][i]) for i in range(5)] for a in ARMS[1:] for s in SEEDS}

    # replication needed for a 95% half-width of delta, and 80% power at delta
    req = {"delta": DELTA, "sigma_contrast_point": sigma_contrast, "sigma_contrast_95ci": [lo, hi],
           "r_precision_point": r_required(sigma_contrast, Z975), "r_precision_upper": r_required(hi, Z975),
           "r_power80_point": r_required(sigma_contrast, Z975 + Z80), "r_power80_upper": r_required(hi, Z975 + Z80),
           "halfwidth_r1": Z975 * sigma_contrast, "halfwidth_r3": Z975 * sigma_contrast / math.sqrt(3), "df": 6}

    best = {a: [runs[(a, s)]["train_result"]["best_val_mean_iou"] for s in SEEDS] for a in ARMS}
    best_step = {a: [runs[(a, s)]["train_result"]["best_step"] for s in SEEDS] for a in ARMS}
    t = {k[0] + f"_s{k[1]}": v["timing"] for k, v in runs.items()}
    mem = {k[0] + f"_s{k[1]}": {"kernel_peak_mb": v["memory"]["kernel_lifetime_max_footprint_mb"], **v["memory"]["sampled_max"], "warn_samples": v["memory"]["pressure_warn_samples"], "samples": v["memory"]["samples"]} for k, v in runs.items()}
    step_rate = {a: float(np.mean([runs[(a, s)]["timing"]["training_seconds"] for s in SEEDS]) / 2000) for a in ARMS}
    val_each = float(np.mean([e["seconds"] for v in runs.values() for e in v["evals"]]))
    d = [(0, step_rate["L00"]), (12, step_rate["L12"]), (23, step_rate["L23"])]
    b, a0 = np.polyfit([24 - x for x, _ in d], [y for _, y in d], 1)
    rem = [2000 * (a0 + b * (24 - l)) + 10 * val_each + 60 for l in range(24) if l not in (0, 12, 23)]
    feas = {"sec_per_step_by_arm": step_rate, "seconds_per_validation": val_each, "remaining_21_hours": sum(rem) / 3600, "remaining_21_hours_plus10pct": 1.1 * sum(rem) / 3600}
    u_vals = [arms[a]["mean"] for a in arms]
    info = {"observed_range_of_mean_U_three_layers": max(u_vals) - min(u_vals), "max_abs_mean_U": max(abs(x) for x in u_vals), "two_delta": 2 * DELTA, "se_contrast_three_seeds": sigma_contrast / math.sqrt(3)}
    out = {"M6": M6.tolist(), "M5": M5.tolist(), "arms": ARMS, "seeds": SEEDS, "reproducibility": repro, "sigma_residual": sigma_e, "sigma_residual_5class": sigma5, "seed_main_effect_sd": sd_seed_means,
           "layer_utility": arms, "layer_contrasts": pairs, "tile_intervals": tile, "tile_halfwidth_median": float(np.median(widths)), "tile_present_delta": per_tile, "replication": req,
           "best_checkpoint_miou": best, "best_step": best_step, "timing": t, "memory": mem, "feasibility": feas, "informativeness": info}
    C.write_json_atomic(C.ART / "pilot_analysis.json", out)
    print(json.dumps({k: out[k] for k in ("M6", "M5", "sigma_residual", "seed_main_effect_sd", "layer_utility", "layer_contrasts", "tile_halfwidth_median", "replication", "best_step", "feasibility", "informativeness")}, indent=1))
    print(json.dumps({k: {a: b for a, b in repro.items() if a not in ("run000", "repeat")} for k in ["repro"]}))


if __name__ == "__main__":
    main()
