"""Phase 3 Stage C screening analysis (protocol v2 section 5, v3 section 5, D10, D11), written
before any single-block run, and the measured Stage D budget (compute audit section 5
formulas with measured Stage C inputs). Reads only dssa/artifacts/phase3; writes
artifacts/phase3/stage_c_analysis.json. Opens no tile and no label.

Definitions:
  U[s, l] = pooled 6-class mIoU at step 2000 (8 Potsdam validation tiles) of L_l seed s
            minus that of K0 seed s;  Ubar = mean over the 3 seeds.
  p(l)    = -1.8386e-4 l^2 + 4.9992e-3 l - 4.1343e-4 (frozen Phase 2D prior).
  z(v)    = (v - mean) / sd over the 24 blocks (population sd).
  r_res   = Spearman(score, z(Ubar) - z(p)).
  Gate (non-inferential), per label-free signal: r_res >= 0.30; each leave-one-seed-out
  r_res >= 0.15; 2.5th percentile of the tile-bootstrap r_res >= 0 (10,000 resamples of
  the 8 tiles, the same resample for every run); regret_sum@3 <= the prior's {14,13,15}.
  regret_sum@k = sum of the k largest Ubar - sum of Ubar over the k selected blocks
  (phase2d/oracle_analysis.py). Scenario: S1 if a label-free signal passes (the best r_res
  among passers advances); else S2 if Spearman(p, Ubar) >= 0.3; else S3."""
from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
ART = ROOT / "artifacts" / "phase3"
SEEDS = (1000, 2000, 3000)
PRIOR_TOP3 = [14, 13, 15]
LABEL_FREE = ["DSS_R2", "GSD", "IO_SIM", "ACT_NORM"]
B_TILES, B_RANDOM = 10000, 20000


def rk(a):
    o = np.argsort(a, kind="mergesort")
    r = np.empty(len(a))
    r[o] = np.arange(len(a))
    return r


def spear(a, b):
    return float(np.corrcoef(rk(np.asarray(a, float)), rk(np.asarray(b, float)))[0, 1])


def kendall(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    s = 0
    for i, j in itertools.combinations(range(len(a)), 2):
        s += np.sign(a[i] - a[j]) * np.sign(b[i] - b[j])
    return float(s / (len(a) * (len(a) - 1) / 2))


def z(v):
    v = np.asarray(v, float)
    return (v - v.mean()) / v.std()


def prior():
    l = np.arange(24)
    return -1.8386e-4 * l ** 2 + 4.9992e-3 * l - 4.1343e-4


def top(v, k):
    return [int(i) for i in np.lexsort((np.arange(24), -np.asarray(v, float)))[:k]]


def regret(U, sel):
    k = len(sel)
    return float(np.sort(U)[::-1][:k].sum() - U[sel].sum())


def miou(cm):
    cm = cm.astype(np.float64)
    tp = np.diag(cm)
    d = cm.sum(0) + cm.sum(1) - tp
    return float(np.nanmean(np.where(d > 0, tp / np.maximum(d, 1e-12), np.nan)))


def main():
    frozen = json.load(open(ART / "stage_b" / "stage_b_scores_frozen.json"))
    import hashlib
    h = hashlib.sha256(open(ART / "stage_b" / "stage_b_scores_frozen.json", "rb").read()).hexdigest()
    if h != (ART / "stage_b" / "stage_b_scores_frozen.sha256").read_text().split()[0]:
        raise RuntimeError("frozen score hash mismatch")
    scores = {k: np.asarray(v, float) for k, v in frozen["scores"].items()}
    runs = {}
    for s in SEEDS:
        for name in [f"p3_K0_s{s}"] + [f"p3_L{l:02d}_s{s}" for l in range(24)]:
            runs[name] = json.load(open(ART / "runs" / name / "summary.json"))
    tiles = sorted(runs["p3_K0_s1000"]["tiles"])
    cms = {n: np.stack([np.asarray(r["tiles"][t]["confusion_matrix"], np.int64) for t in tiles]) for n, r in runs.items()}

    def util(sel_tiles=None):
        idx = np.arange(len(tiles)) if sel_tiles is None else sel_tiles
        m = {n: miou(c[idx].sum(0)) for n, c in cms.items()}
        return np.array([[m[f"p3_L{l:02d}_s{s}"] - m[f"p3_K0_s{s}"] for l in range(24)] for s in SEEDS]), m

    U, m = util()
    Ub = U.mean(0)
    p = prior()
    target = z(Ub) - z(p)
    rng = np.random.default_rng(2026)
    boots = [rng.integers(0, len(tiles), len(tiles)) for _ in range(B_TILES)]
    boot_targets = []
    for b in boots:
        Uu, _ = util(b)
        boot_targets.append(z(Uu.mean(0)) - z(p))
    prior_reg3 = regret(Ub, PRIOR_TOP3)
    res = {}
    for k, v in scores.items():
        loso = [spear(v, z(U[[i for i in range(3) if i != j]].mean(0)) - z(p)) for j in range(3)]
        bt = np.array([spear(v, t) for t in boot_targets])
        r = spear(v, target)
        reg = {f"regret_sum@{kk}": regret(Ub, top(v, kk)) for kk in (1, 3, 5)}
        gate = {"r_res>=0.30": r >= 0.30, "loso>=0.15": min(loso) >= 0.15, "boot2.5>=0": float(np.percentile(bt, 2.5)) >= 0,
                "regret3<=prior": reg["regret_sum@3"] <= prior_reg3 + 1e-12}
        res[k] = {"r_res": r, "loso_r_res": loso, "tile_boot_r_res_2.5_97.5": np.percentile(bt, [2.5, 97.5]).tolist(),
                  "spearman_U": spear(v, Ub), "kendall_U": kendall(v, Ub), "top3": top(v, 3), **reg,
                  "gate": gate, "passes": bool(all(gate.values())) if k in LABEL_FREE else None}
    rnd = {kk: np.array([regret(Ub, list(rng.choice(24, kk, replace=False))) for _ in range(B_RANDOM)]) for kk in (1, 3, 5)}
    for k in res:
        res[k]["random_percentile_regret"] = {kk: float((rnd[kk] <= res[k][f"regret_sum@{kk}"]).mean()) for kk in (1, 3, 5)}
    prior_tr = spear(p, Ub)
    passers = [k for k in LABEL_FREE if res[k]["passes"]]
    cand = max(passers, key=lambda k: res[k]["r_res"]) if passers else None
    scen = "S1" if cand else ("S2" if prior_tr >= 0.3 else "S3")
    seed_sd = float(U.std(0, ddof=1).mean())
    out = {"utility": {"U": U.tolist(), "Ubar": Ub.tolist(), "K0_miou": {s: m[f"p3_K0_s{s}"] for s in SEEDS},
                       "oracle_top3": top(Ub, 3), "mean_seed_sd_per_block": seed_sd},
           "prior": {"spearman_p_Ubar": prior_tr, "kendall_p_Ubar": kendall(p, Ub), "top3": PRIOR_TOP3,
                     "regret_sum@1": regret(Ub, [14]), "regret_sum@3": prior_reg3, "regret_sum@5": regret(Ub, top(p, 5))},
           "late_rule": {"spearman": spear(np.arange(24), Ub), "regret_sum@3": regret(Ub, [21, 22, 23])},
           "signals": res, "label_free_passers": passers, "candidate": cand, "scenario": scen,
           "candidate_top3": res[cand]["top3"] if cand else None,
           "frozen_scores_sha256": h, "tiles": tiles, "n_boot_tiles": B_TILES}
    out["budget"] = budget(runs, frozen, cand, scen)
    tmp = ART / "stage_c_analysis.json.tmp"
    tmp.write_text(json.dumps(out, indent=1, default=float))
    tmp.replace(ART / "stage_c_analysis.json")
    print(json.dumps({"scenario": scen, "candidate": cand, "prior_transfer": prior_tr, "oracle_top3": top(Ub, 3),
                      "r_res": {k: round(v["r_res"], 3) for k, v in res.items()}, "passes": {k: res[k]["passes"] for k in LABEL_FREE},
                      "stage_d": out["budget"]["selected"]}, indent=1))


def budget(runs, frozen, cand, scen):
    """Compute-audit section 5 formulas with measured Stage C inputs."""
    tr = {l: float(np.mean([runs[f"p3_L{l:02d}_s{s}"]["timing"]["training_seconds"] for s in SEEDS])) for l in range(24)}
    t_k0 = float(np.mean([runs[f"p3_K0_s{s}"]["timing"]["training_seconds"] for s in SEEDS]))
    fixed = [r["timing"]["run_wall"] - r["timing"]["training_seconds"] for r in runs.values()]
    FIXED = float(np.mean(fixed))
    evals = [w for r in runs.values() for w in r["timing"]["eval_walls"]]
    E_tile = float(np.mean(evals))
    eps = 0.0044
    t_unif = 1677 * tr[0] / 1521  # Measurement B scaled by the measured Potsdam/Vaihingen L0 ratio
    tk3 = lambda sel: tr[min(sel)] * (1 + 2 * eps)  # noqa: E731
    t_rand = float(np.mean([tk3(c) for c in itertools.combinations(range(24), 3)]))
    top3 = frozen["top3"]
    arms = [("K0 (7 new)", t_k0, 7, 7, 7), ("Prior-3 {13,14,15}", tk3([13, 14, 15]), 10, 10, 10),
            ("Candidate-3", tk3(top3[cand]) if cand else None, 10, 0, 0), ("Uniform r1", t_unif, 10, 10, 10),
            ("Middle-3 {10,11,12}", tk3([10, 11, 12]), 5, 5, 5), ("Late-3 {21,22,23}", tk3([21, 22, 23]), 5, 5, 0),
            ("DSS-R2-3 " + str(top3["DSS_R2"]), tk3(top3["DSS_R2"]), 5, 5, 0), ("Fisher-3 " + str(top3["FISHER"]), tk3(top3["FISHER"]), 5, 5, 0),
            ("LogME-3 " + str(top3["LOGME"]), tk3(top3["LOGME"]), 5, 5, 0), ("Random-3 (10 draws)", t_rand, 10, 10, 10), ("Uniform r8", t_unif, 5, 5, 0)]
    sc = {}
    for i, name in enumerate(("S1", "S2", "S3")):
        n = sum(a[2 + i] for a in arms)
        secs = sum(a[2 + i] * ((a[1] or 0) + FIXED) for a in arms)
        models = n + 3
        sc[name] = {"new_runs": n, "stage_d_hours": secs / 3600, "test_models": models, "potsdam_test_hours": models * 10 * E_tile / 3600}
    if not cand:
        sc["S1"] = {"note": "not applicable: no label-free candidate passed"}
    return {"measured": {"T_K0": t_k0, "T_l": tr, "FIXED_per_run_s": FIXED, "FIXED_range_s": [min(fixed), max(fixed)], "E_tile_s": E_tile,
                         "T_uniform_est": t_unif, "T_random3": t_rand,
                         "stage_c_hours_actual_compute": sum(r["timing"]["run_wall"] for r in runs.values()) / 3600},
            "arms": [{"arm": a[0], "T_arm_s": a[1], "seeds_S1_S2_S3": a[2:]} for a in arms], "scenarios": sc, "selected": {scen: sc[scen]}}


if __name__ == "__main__":
    sys.exit(main())
