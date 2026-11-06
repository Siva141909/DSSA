"""Gate 2 pre-training audit of the pilot statistics. Independent of
pilot_analysis.py: mIoU is recomputed here from the raw per-tile validation
confusion matrices and checked against the values the frozen evaluator stored.
Writes gate2/pilot_statistical_audit.json. The pilot report and
pilot_analysis.json are not modified."""
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
from tstat import power_two_sided, t_ppf  # noqa: E402

DELTA = 0.010
SEEDS, ARMS = (1000, 2000, 3000), ("K0", "L00", "L12", "L23")
OUT = C.ART / "gate2"


def rid(a, s):
    if a == "K0":
        return f"p2d_ctrl_K0_s{s}"
    return "p2d_oracle_L00_s1000_a3" if (a, s) == ("L00", 1000) else f"p2d_oracle_{a}_s{s}"


def iou(cm):
    cm = np.asarray(cm, dtype=np.float64)
    tp = np.diag(cm)
    d = cm.sum(0) + cm.sum(1) - tp
    return np.where(d > 0, tp / np.where(d > 0, d, 1), np.nan), d


def miou(cm, k):
    v, _ = iou(cm)
    return float(np.nanmean(v[:k]))


def interval(vals, sd, df):
    m, n = float(np.mean(vals)), len(vals)
    h = t_ppf(0.975, df) * sd / math.sqrt(n)
    return {"mean": m, "sd": sd, "se": sd / math.sqrt(n), "df": df, "t975": t_ppf(0.975, df), "halfwidth": h, "ci95": [m - h, m + h], "excludes_zero": bool(m - h > 0 or m + h < 0)}


def seeds_needed(sigma, df_of_r, target, power=None):
    for r in range(2, 200):
        df = df_of_r(r)
        if power is None:
            if t_ppf(0.975, df) * sigma / math.sqrt(r) <= target:
                return r
        elif power_two_sided(target * math.sqrt(r) / sigma, df) >= power:
            return r
    return None


def main():
    OUT.mkdir(exist_ok=True)
    runs = {(a, s): json.load(open(C.RUNS / rid(a, s) / "result.json")) for a in ARMS for s in SEEDS}
    stored = json.load(open(C.ART / "pilot_analysis.json"))

    # 1-2. mIoU definitions, recomputed from raw tile matrices
    checks, M6, M5 = [], np.zeros((4, 3)), np.zeros((4, 3))
    zero_denominator = []
    for i, a in enumerate(ARMS):
        for j, s in enumerate(SEEDS):
            r = runs[(a, s)]
            ev = r["evals"][-1]
            if ev["step"] != 2000 or r["post_run_checks"]["steps"] != 2000:
                raise RuntimeError(f"{a} {s}: last evaluation is not step 2000")
            if sorted(ev["tiles"]) != sorted(C.VAL):
                raise RuntimeError("validation tiles differ from the split")
            cm = np.sum([ev["tiles"][f] for f in C.VAL], axis=0)
            _, d = iou(cm)
            zero_denominator += [(a, s, int(k)) for k in np.where(d == 0)[0]]
            M6[i, j], M5[i, j] = miou(cm, 6), miou(cm, 5)
            vh = r["validation_history"][-1]
            checks.append({"arm": a, "seed": s, "recomputed_6": M6[i, j], "stored_eval_mean_iou": ev["mean_iou"], "stored_history_val_mean_iou": vh["val_mean_iou"],
                           "pilot_analysis_M6": stored["M6"][i][j], "pilot_analysis_M5": stored["M5"][i][j], "recomputed_5": M5[i, j],
                           "max_abs_diff": max(abs(M6[i, j] - ev["mean_iou"]), abs(M6[i, j] - vh["val_mean_iou"]), abs(M6[i, j] - stored["M6"][i][j]), abs(M5[i, j] - stored["M5"][i][j]))})
    max_diff = max(c["max_abs_diff"] for c in checks)

    # 3-4. seed level, per contrast (df = n_seeds - 1) and pooled two-way (df = 6)
    res = M6 - M6.mean(1, keepdims=True) - M6.mean(0, keepdims=True) + M6.mean()
    sigma_e = math.sqrt((res ** 2).sum() / 6)
    sigma_c = math.sqrt(2) * sigma_e
    U = {a: M6[i] - M6[0] for i, a in enumerate(ARMS) if i}
    U5 = {a: M5[i] - M5[0] for i, a in enumerate(ARMS) if i}
    per_arm = {}
    for a, v in U.items():
        per_arm[a] = {"values": v.tolist(), "values_5class": U5[a].tolist(), "mean_5class": float(U5[a].mean()),
                      "per_contrast_t_df2": interval(v, float(np.std(v, ddof=1)), 2),
                      "pooled_t_df6": interval(v, sigma_c, 6),
                      "reported_z_halfwidth": 1.95996 * sigma_c / math.sqrt(3)}
    contrasts = {}
    for a, b in itertools.combinations(ARMS[1:], 2):
        v = M6[ARMS.index(a)] - M6[ARMS.index(b)]
        contrasts[f"{a}-{b}"] = {"values": v.tolist(), "per_contrast_t_df2": interval(v, float(np.std(v, ddof=1)), 2), "pooled_t_df6": interval(v, sigma_c, 6)}
    chi = {"lo": 1.2373, "hi": 14.4494}
    sig_ci = [sigma_c * math.sqrt(6 / chi["hi"]), sigma_c * math.sqrt(6 / chi["lo"])]

    # 5. the reported 0.0085 and the resolution claim
    z_hw3 = 1.95996 * sigma_c / math.sqrt(3)
    t6_hw3 = t_ppf(0.975, 6) * sigma_c / math.sqrt(3)
    t2_hw = {a: per_arm[a]["per_contrast_t_df2"]["halfwidth"] for a in per_arm}
    gate2_df = lambda r: 24 * (r - 1)  # 25 arms (24 layers + K0), two-way layout
    contrast_df = lambda r: r - 1
    fixed6 = lambda r: 6
    need = {}
    for name, s in (("point", sigma_c), ("upper95", sig_ci[1])):
        need[name] = {"sigma_c": s,
                      "precision_z_reported_method": max(1, math.ceil((1.95996 * s / DELTA) ** 2)),
                      "precision_t_per_contrast_df_r_minus_1": seeds_needed(s, contrast_df, DELTA),
                      "precision_t_sigma_from_pilot_df6": seeds_needed(s, fixed6, DELTA),
                      "precision_t_gate2_pooled_df_24(r-1)": seeds_needed(s, gate2_df, DELTA),
                      "power80_z_reported_method": max(1, math.ceil(((1.95996 + 0.84162) * s / DELTA) ** 2)),
                      "power80_t_per_contrast": seeds_needed(s, contrast_df, DELTA, power=0.8),
                      "power80_t_gate2_pooled": seeds_needed(s, gate2_df, DELTA, power=0.8)}
    power_at_3 = {"per_contrast_df2": power_two_sided(DELTA * math.sqrt(3) / sigma_c, 2), "pooled_df6": power_two_sided(DELTA * math.sqrt(3) / sigma_c, 6),
                  "gate2_pooled_df48": power_two_sided(DELTA * math.sqrt(3) / sigma_c, 48)}
    resolution = {"reported_halfwidth_r3": stored["replication"]["halfwidth_r3"], "recomputed_z_halfwidth_r3": z_hw3, "reported_value_reproduces": abs(z_hw3 - stored["replication"]["halfwidth_r3"]) < 1e-12,
                  "t_df6_halfwidth_r3": t6_hw3, "t_df2_halfwidth_by_arm": t2_hw, "gate2_pooled_df48_halfwidth_r3": t_ppf(0.975, 48) * sigma_c / math.sqrt(3),
                  "t_df6_halfwidth_r3_at_sigma_upper": t_ppf(0.975, 6) * sig_ci[1] / math.sqrt(3),
                  "claim_three_seeds_resolve_delta": "not supported", "seeds_needed": need, "power_at_delta_with_3_seeds": power_at_3}

    # 6. tile resampling, conditional on each trained model; never combined with seed
    idx = np.array(list(itertools.product(range(5), repeat=5)))
    last = {k: np.array([v["evals"][-1]["tiles"][f] for f in C.VAL]) for k, v in runs.items()}
    tile = {}
    for a in ARMS[1:]:
        for s in SEEDS:
            A, B = last[(a, s)], last[("K0", s)]
            d = np.array([miou(A[i].sum(0), 6) - miou(B[i].sum(0), 6) for i in idx])
            tile[f"{a}-K0_s{s}"] = {"point": float(U[a][SEEDS.index(s)]), "pct95": np.percentile(d, [2.5, 97.5]).tolist(), "sd": float(d.std())}
    tile_reproduces = all(np.allclose(tile[k]["pct95"], stored["tile_intervals"][k], atol=1e-12) for k in tile)

    out = {"miou_checks": checks, "max_abs_diff_all_sources": max_diff, "zero_denominator_classes": zero_denominator, "M6": M6.tolist(), "M5": M5.tolist(),
           "sigma_e": sigma_e, "sigma_c": sigma_c, "sigma_c_ci95_df6": sig_ci, "seed_main_effect_sd": float(M6.mean(0).std(ddof=1)), "per_arm": per_arm, "contrasts": contrasts,
           "resolution": resolution, "tile": tile, "tile_reproduces_pilot": tile_reproduces, "tile_halfwidth_median": float(np.median([(t["pct95"][1] - t["pct95"][0]) / 2 for t in tile.values()]))}
    C.write_json_atomic(OUT / "pilot_statistical_audit.json", out)
    print(json.dumps({k: out[k] for k in ("max_abs_diff_all_sources", "zero_denominator_classes", "sigma_e", "sigma_c", "sigma_c_ci95_df6", "resolution", "tile_reproduces_pilot", "tile_halfwidth_median")}, indent=1))
    for a, v in per_arm.items():
        print(a, {k: (round(v[k]["mean"], 4), round(v[k]["halfwidth"], 4), [round(x, 4) for x in v[k]["ci95"]]) for k in ("per_contrast_t_df2", "pooled_t_df6")})
    for a, v in contrasts.items():
        print(a, {k: (round(v[k]["mean"], 4), round(v[k]["halfwidth"], 4), [round(x, 4) for x in v[k]["ci95"]]) for k in ("per_contrast_t_df2", "pooled_t_df6")})


if __name__ == "__main__":
    main()
