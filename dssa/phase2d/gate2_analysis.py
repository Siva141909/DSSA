"""Frozen before any Gate 2 training. Reads the 12 pilot runs and the 63 Gate 2
runs, recomputes mIoU from raw validation confusion matrices, and compares the
frozen rankings with observed utility through oracle_analysis.analyze (frozen
before the pilot, used unchanged). Seed and tile uncertainty stay separate:
  seed: t intervals across the 3 seeds (per layer df 2; pooled two-way df 48)
        and the 27 ordered seed resamples for ranking metrics (only 10 distinct)
  tile: 3,125 ordered resamples of the 5 validation tiles, applied jointly to
        every arm and seed, conditional on the trained models
The oracle ranking uses validation labels and is a research benchmark only.
Conclusions are restricted to the L23-only decoder and this split."""
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
import oracle_analysis as O  # noqa: E402
from tstat import t_ppf  # noqa: E402

DELTA = 0.010
SEEDS = C.PILOT_SEEDS
ARMS = ["K0"] + list(range(24))
OUT = C.ART / "gate2"
KS = O.KS


def rid(a, s):
    if a == "K0":
        return f"p2d_ctrl_K0_s{s}"
    return "p2d_oracle_L00_s1000_a3" if (a, s) == (0, 1000) else f"p2d_oracle_L{a:02d}_s{s}"


def miou_batch(cm, k=6):
    """cm (..., 6, 6) -> mIoU over the first k classes (nan-mean, frozen definition)."""
    cm = cm.astype(np.float64)
    tp = np.diagonal(cm, axis1=-2, axis2=-1)
    d = cm.sum(-2) + cm.sum(-1) - tp
    v = np.where(d > 0, tp / np.where(d > 0, d, 1), np.nan)[..., :k]
    return np.nanmean(v, -1)


def class_iou(cm):
    cm = cm.astype(np.float64)
    tp = np.diag(cm)
    d = cm.sum(0) + cm.sum(1) - tp
    return np.where(d > 0, tp / np.where(d > 0, d, 1), np.nan)


def tint(v, sd, df):
    m, h = float(np.mean(v)), t_ppf(0.975, df) * sd / math.sqrt(len(v))
    return {"mean": m, "sd": sd, "df": df, "halfwidth": h, "ci95": [m - h, m + h]}


def twoway(Y):
    a, s = Y.shape
    res = Y - Y.mean(1, keepdims=True) - Y.mean(0, keepdims=True) + Y.mean()
    df = (a - 1) * (s - 1)
    return math.sqrt((res ** 2).sum() / df), df, res


def kendall_w(R):
    """R: (raters, items) utility values; Kendall's coefficient of concordance."""
    m, n = R.shape
    ranks = np.array([O.rk(r) for r in R]) + 1
    S = ((ranks.sum(0) - m * (n + 1) / 2) ** 2).sum()
    return float(12 * S / (m ** 2 * (n ** 3 - n)))


def load():
    runs, problems = {}, []
    for a in ARMS:
        for s in SEEDS:
            d = C.RUNS / rid(a, s)
            r = json.load(open(d / "result.json"))
            h = json.load(open(d / "hashes.json"))
            e = json.load(open(C.BASELINE))["expected"][str(s)]
            chk = {"status": r["status"] == "completed", "steps": r["post_run_checks"]["steps"] == 2000, "last_eval_2000": r["evals"][-1]["step"] == 2000,
                   "layers": r["entry"]["layer_indices"] == ([] if a == "K0" else [a]), "seed": r["entry"]["training_seed"] == s,
                   "decoder_hash": r["pre_run_checks"]["decoder_hash"] == e["decoder_hash"], "rng_hash": r["pre_run_checks"]["torch_rng_hash"] == e["torch_rng_hash"],
                   "backbone_fp_after": r["post_run_checks"]["backbone_fp"] == json.load(open(C.BASELINE))["expected_common"]["backbone_fp"], "data_stream": r["post_run_checks"]["data_stream_ok"],
                   "tiles_allowed": not (set(r["post_run_checks"]["tiles_opened"]) - C.ALLOWED_TILES), "result_hash": C.sha256_file(d / "result.json") == h["result_sha256"],
                   "ckpt_hashes": all(C.sha256_file(d / f"{rid(a, s)}_{t}.pt") == h["checkpoints"][t]["sha256"] for t in ("best", "final")),
                   "reload_cm_diff_0": all(h["checkpoints"][t]["cm_diff"] == 0 for t in ("best", "final"))}
            if not all(chk.values()):
                problems.append({"run": rid(a, s), "failed": [k for k, v in chk.items() if not v]})
            runs[(a, s)] = r
    return runs, problems


def main():
    OUT.mkdir(exist_ok=True)
    runs, problems = load()
    T = {k: np.array([v["evals"][-1]["tiles"][f] for f in C.VAL]) for k, v in runs.items()}  # (5, 6, 6)
    M6 = np.array([[miou_batch(T[(a, s)].sum(0)) for s in SEEDS] for a in ARMS])
    M5 = np.array([[miou_batch(T[(a, s)].sum(0), 5) for s in SEEDS] for a in ARMS])
    stored_diff = max(abs(M6[i, j] - runs[(a, s)]["evals"][-1]["mean_iou"]) for i, a in enumerate(ARMS) for j, s in enumerate(SEEDS))
    U = M6[1:] - M6[0]          # (24, 3)
    U5 = M5[1:] - M5[0]
    Ubar = U.mean(1)

    # seed uncertainty
    sig_e, df_pool, res = twoway(M6)
    sig_c = math.sqrt(2) * sig_e
    per_layer = {l: {"U": U[l].tolist(), "U5": U5[l].tolist(), "mean": float(Ubar[l]), "mean_5class": float(U5[l].mean()),
                     "seed_t_df2": tint(U[l], float(np.std(U[l], ddof=1)), 2), "pooled_t": tint(U[l], sig_c, df_pool),
                     "all_seeds_positive": bool((U[l] > 0).all()), "all_seeds_negative": bool((U[l] < 0).all())} for l in range(24)}
    arm_resid_sd = {str(a): float(np.sqrt((res[i] ** 2).sum() / 2)) for i, a in enumerate(ARMS)}
    seed_rank_corr = {f"{SEEDS[i]}-{SEEDS[j]}": O.spearman(U[:, i], U[:, j]) for i, j in itertools.combinations(range(3), 2)}
    seed_block = {"sigma_e": sig_e, "sigma_c": sig_c, "df": df_pool, "seed_main_effect_sd": float(M6.mean(0).std(ddof=1)), "arm_residual_sd": arm_resid_sd,
                  "spearman_between_seed_utility_vectors": seed_rank_corr, "kendall_W_three_seeds": kendall_w(U.T),
                  "pooled_halfwidth": t_ppf(0.975, df_pool) * sig_c / math.sqrt(3), "per_layer_df2_halfwidth_median": float(np.median([per_layer[l]["seed_t_df2"]["halfwidth"] for l in range(24)]))}

    # tile uncertainty (conditional on trained models; never pooled with seed)
    idx = np.array(list(itertools.product(range(5), repeat=5)))
    Mt = np.stack([np.stack([miou_batch(T[(a, s)][idx].sum(1)) for s in SEEDS], -1) for a in ARMS])  # (25, 3125, 3)
    Ut = Mt[1:] - Mt[0]  # (24, 3125, 3)
    tile_block = {"per_layer_seed_pct95": {l: [np.percentile(Ut[l, :, j], [2.5, 97.5]).tolist() for j in range(3)] for l in range(24)},
                  "per_layer_mean_over_seeds_pct95": {l: np.percentile(Ut[l].mean(-1), [2.5, 97.5]).tolist() for l in range(24)}}
    tile_block["halfwidth_median_single_seed"] = float(np.median([(v[1] - v[0]) / 2 for l in range(24) for v in tile_block["per_layer_seed_pct95"][l]]))
    tile_block["halfwidth_median_seed_mean"] = float(np.median([(v[1] - v[0]) / 2 for v in tile_block["per_layer_mean_over_seeds_pct95"].values()]))
    U_tile = np.vstack([Ubar, Ut.mean(-1).T])                    # (1 + 3125, 24)
    seed_sets = list(itertools.product(range(3), repeat=3))
    U_seed = np.vstack([Ubar] + [U[:, list(ss)].mean(1) for ss in seed_sets])  # (1 + 27, 24)

    # rankings
    frz = json.load(open(C.GATE0 / "frozen_rankings.json"))
    sel = {k: {"rank": v["rank"]} for k, v in frz["selectors"].items()}
    oracle_rank = np.argsort(-Ubar, kind="mergesort").tolist()
    by_tile = O.analyze(U_tile, sel)
    by_seed = O.analyze(U_seed, sel)
    rules = O.rules(sel)
    rules["Oracle_benchmark"] = oracle_rank
    point = {n: O.metrics(r, Ubar) for n, r in rules.items()}
    per_seed = {str(s): {n: O.metrics(r, U[:, j]) for n, r in rules.items()} for j, s in enumerate(SEEDS)}
    rng = np.random.default_rng(20261103)
    rnd = [O.metrics(list(rng.permutation(24)), Ubar) for _ in range(20000)]
    random_rule = {c: {"mean": float(np.mean([m[c] for m in rnd])), "pct": np.percentile([m[c] for m in rnd], [2.5, 50, 97.5]).tolist()} for c in rnd[0]}
    loso = {str(s): {n: O.metrics(r, U[:, [k for k in range(3) if k != j]].mean(1)) for n, r in rules.items() if n != "Oracle_benchmark"} for j, s in enumerate(SEEDS)}

    # depth confound
    depth = np.arange(24, dtype=float)
    fits = {}
    for deg in (1, 2):
        coef = np.polyfit(depth, Ubar, deg)
        resid = Ubar - np.polyval(coef, depth)
        fits[f"poly{deg}"] = {"coef": coef.tolist(), "r2": float(1 - resid.var() / Ubar.var()),
                              "selector_spearman_with_residual": {n: O.spearman(O.score_from_rank(r), resid) for n, r in rules.items() if n != "Oracle_benchmark"}}
    depth_block = {"spearman_U_depth": O.spearman(depth, Ubar), "kendall_U_depth": O.kendall_b(depth, Ubar), "selector_depth_spearman": frz["depth_spearman"], "fits": fits,
                   "R2_minus_Late_spearman": point["R2"]["spearman"] - point["Late"]["spearman"],
                   "tile_resampled_R2_minus_Late_spearman_pct95": np.percentile([O.spearman(O.score_from_rank(rules["R2"]), u) - O.spearman(depth, u) for u in U_tile[1:]], [2.5, 97.5]).tolist()}

    # layer 12
    l12 = {"observed_rank_of_24": oracle_rank.index(12) + 1, "mean_U": float(Ubar[12]), "rank_in_selector": {n: list(r).index(12) + 1 for n, r in rules.items()},
           "tile_rank_pct95": np.percentile([list(np.argsort(-u, kind="mergesort")).index(12) + 1 for u in U_tile[1:]], [2.5, 97.5]).tolist(),
           "per_seed_rank": [list(np.argsort(-U[:, j], kind="mergesort")).index(12) + 1 for j in range(3)]}

    # per class, best checkpoint, runtime
    per_class = {l: np.mean([class_iou(T[(l, s)].sum(0)) - class_iou(T[("K0", s)].sum(0)) for s in SEEDS], 0).tolist() for l in range(24)}
    best = {str(a): {"best_miou": [runs[(a, s)]["train_result"]["best_val_mean_iou"] for s in SEEDS], "best_step": [runs[(a, s)]["train_result"]["best_step"] for s in SEEDS],
                     "val_ce_2000": [runs[(a, s)]["evals"][-1]["val_ce"] for s in SEEDS]} for a in ARMS}
    ops = {rid(a, s): {"steps": runs[(a, s)]["post_run_checks"]["steps"], **{k: round(v, 1) for k, v in runs[(a, s)]["timing"].items()}, "est": runs[(a, s)]["entry"]["est_seconds"],
                       "peak_mb": round(runs[(a, s)]["memory"]["kernel_lifetime_max_footprint_mb"], 1), "driver_mb": round(runs[(a, s)]["memory"]["sampled_max"]["driver_mb"], 1),
                       "current_mb": round(runs[(a, s)]["memory"]["sampled_max"]["current_mb"], 1), "swap_growth_mb": round(runs[(a, s)]["memory"]["sampled_max"]["swap_growth_mb"], 1),
                       "pressure_max": runs[(a, s)]["memory"]["sampled_max"]["pressure"], "warn_samples": runs[(a, s)]["memory"]["pressure_warn_samples"],
                       "best_sha": runs[(a, s)]["reload_verification"]["best"]["sha256"], "final_sha": runs[(a, s)]["reload_verification"]["final"]["sha256"]} for a in ARMS for s in SEEDS}

    out = {"note": __doc__, "integrity_problems": problems, "stored_vs_recomputed_max_diff": stored_diff, "M6": M6.tolist(), "M5": M5.tolist(), "per_layer": per_layer,
           "oracle_rank": oracle_rank, "seed": seed_block, "tile": tile_block, "selectors_point": point, "selectors_per_seed": per_seed, "leave_one_seed_out": loso,
           "tile_resampled": {"random_percentile": by_tile["random_percentile"], "intervals": by_tile["intervals"]},
           "seed_resampled": {"intervals": by_seed["intervals"], "distinct_seed_sets": 10}, "random_rule": random_rule, "depth": depth_block, "layer12": l12,
           "per_class_mean_diff": per_class, "best_checkpoint": best, "operations": ops, "delta": DELTA}
    C.write_json_atomic(OUT / "gate2_analysis.json", out)
    print("integrity problems:", problems, "stored diff", stored_diff)
    print("oracle rank:", oracle_rank)
    print("mean U:", np.round(Ubar, 4).tolist())
    for n, v in point.items():
        print(f"{n:16s}", {k: round(x, 3) for k, x in v.items()})


if __name__ == "__main__":
    main()
