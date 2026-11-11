"""Potsdam test analysis, frozen (hashed into the test manifest) before any test tile is opened.

Protocol v3 section 6, scenario S2: the single primary confirmatory contrast is
  C3: Prior-3 {13,14,15} non-inferior to Uniform-r1 (all 24 blocks, rank 1), margin delta = 0.010,
paired by training seed (1000-10000), n = 10, effect = mean of (Prior-3 - Uniform-r1) in pooled
test mIoU, with a two-sided 95% t-interval (df 9). C3 holds if and only if the lower bound of
that interval is above -delta (equivalently a one-sided alpha = 0.025 test of H0: mean <= -delta).
Robustness (protocol v2 section 7): a tile bootstrap conditional on the trained models (10,000
resamples of the 10 test tiles, the same resample for every model, seed 20261111).
Everything else is descriptive: every arm's mean, SD and 95% t-interval, its gain over K0, and
per-class IoU. Pooled mIoU = mean IoU of the confusion matrix summed over the 10 test tiles, as
for validation. Writes artifacts/phase3/test_potsdam/test_analysis.json; never overwrites."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import p3common as C  # noqa: E402

C.install_guards()
C.setup_paths()
import numpy as np  # noqa: E402
from metrics import ConfusionMatrixAccumulator  # noqa: E402

DELTA = 0.010
T975 = {4: 2.776445, 9: 2.262157}   # Student t 0.975 quantiles
N_BOOT, BOOT_SEED = 10_000, 20261111
TDIR = C.ART / "test_potsdam"


def miou(cm: np.ndarray) -> float:
    a = ConfusionMatrixAccumulator()
    a.matrix += cm.astype(np.int64)
    return float(a.compute()["mean_iou"])


def t_cdf(x: float, df: int) -> float:
    """Student t CDF by Simpson integration of the density (no scipy in this environment)."""
    c = math.exp(math.lgamma((df + 1) / 2) - math.lgamma(df / 2)) / math.sqrt(df * math.pi)
    f = lambda u: c * (1 + u * u / df) ** (-(df + 1) / 2)  # noqa: E731
    a, b, n = 0.0, abs(x), 20000
    h = (b - a) / n
    s = f(a) + f(b) + sum((4 if i % 2 else 2) * f(a + i * h) for i in range(1, n))
    half = s * h / 3
    return 0.5 + half if x >= 0 else 0.5 - half


def interval(v):
    v = np.asarray(v, float)
    n = len(v)
    m, sd = float(v.mean()), float(v.std(ddof=1)) if n > 1 else float("nan")
    hw = T975.get(n - 1, float("nan")) * sd / math.sqrt(n) if n > 1 else float("nan")
    return {"n": n, "mean": m, "sd": sd, "ci95": [m - hw, m + hw]}


def main():
    out = TDIR / "test_analysis.json"
    if out.exists():
        raise FileExistsError(out)
    tm = json.load(open(TDIR / "test_manifest.json"))
    tiles = tm["tiles"]
    cms, info = {}, {}
    for m in tm["models"]:
        rid = m["run_id"]
        per = []
        for t in tiles:
            j = json.load(open(TDIR / rid / f"{C.potsdam_tile_id(t)}.json"))
            if j["checkpoint_sha256"] != m["checkpoint_sha256"] or j["tile"] != t:
                raise RuntimeError(f"{rid} {t}: checkpoint or tile mismatch")
            per.append(np.array(j["confusion_matrix"], dtype=np.int64))
        cms[rid] = np.stack(per)
        info[rid] = m
    test_miou = {rid: miou(c.sum(0)) for rid, c in cms.items()}

    arms = {}
    for rid, m in info.items():
        arms.setdefault(m["arm"], []).append(rid)
    k0_mean = float(np.mean([test_miou[r] for r in arms["K0"]]))
    arm_table = {}
    for arm, rids in arms.items():
        v = [test_miou[r] for r in rids]
        pcs = []
        for r in rids:
            a = ConfusionMatrixAccumulator()
            a.matrix += cms[r].sum(0)
            pcs.append(a.compute()["per_class_iou"])
        arm_table[arm] = {**interval(v), "gain_over_k0": float(np.mean(v)) - k0_mean,
                          "val_mean": float(np.mean([info[r]["val_miou"] for r in rids])),
                          "per_class_iou_mean": (np.mean([list(p.values()) if isinstance(p, dict) else p for p in pcs], axis=0).tolist()),
                          "per_class_names": list(pcs[0].keys()) if isinstance(pcs[0], dict) else None,
                          "models": {r: {"seed": info[r]["seed"], "blocks": info[r]["blocks"], "test_miou": test_miou[r], "val_miou": info[r]["val_miou"]} for r in rids}}

    by_seed = lambda arm: {info[r]["seed"]: r for r in arms[arm]}  # noqa: E731
    pr, un = by_seed("PRIOR3"), by_seed("UNIF1")
    seeds = sorted(pr)
    if seeds != sorted(un) or len(seeds) != 10:
        raise RuntimeError("Prior-3 and Uniform-r1 seeds do not pair as 10")
    d = np.array([test_miou[pr[s]] - test_miou[un[s]] for s in seeds])
    iv = interval(d)
    t_stat = (iv["mean"] + DELTA) / (iv["sd"] / math.sqrt(10))
    p_one = 1.0 - t_cdf(t_stat, 9)
    rng = np.random.default_rng(BOOT_SEED)
    boots = []
    for _ in range(N_BOOT):
        idx = rng.integers(0, len(tiles), len(tiles))
        boots.append(np.mean([miou(cms[pr[s]][idx].sum(0)) - miou(cms[un[s]][idx].sum(0)) for s in seeds]))
    boots = np.array(boots)
    c3 = {"contrast": "Prior-3 minus Uniform-r1, paired by seed", "delta": DELTA, "seeds": seeds,
          "differences": dict(zip(map(str, seeds), d.tolist())), **iv,
          "t_statistic_vs_minus_delta": t_stat, "p_one_sided": p_one,
          "non_inferior": bool(iv["ci95"][0] > -DELTA),
          "tile_bootstrap": {"n": N_BOOT, "seed": BOOT_SEED, "mean": float(boots.mean()),
                             "ci95_percentile": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))],
                             "share_above_minus_delta": float((boots > -DELTA).mean())}}

    descriptive_vs_unif1 = {}
    for arm in arms:
        if arm in ("UNIF1",):
            continue
        a = by_seed(arm)
        common = sorted(set(a) & set(un))
        if len(common) >= 2:
            descriptive_vs_unif1[arm] = {"seeds": common, **interval([test_miou[a[s]] - test_miou[un[s]] for s in common])}
    res = {"test_manifest_sha256": C.sha256_file(TDIR / "test_manifest.json"), "tiles": tiles, "k0_mean": k0_mean,
           "primary_C3": c3, "arms": arm_table, "descriptive_paired_vs_unif1": descriptive_vs_unif1,
           "note": "Confirmatory claim follows C3 only (protocol v3 section 6, S2). All other numbers are descriptive."}
    C.write_json_atomic(out, res)
    print(f"C3 Prior3-Unif1 mean {iv['mean']:+.4f} CI [{iv['ci95'][0]:+.4f}, {iv['ci95'][1]:+.4f}] non-inferior={c3['non_inferior']} p={p_one:.4g}")
    for arm, r in sorted(arm_table.items(), key=lambda x: -x[1]["mean"]):
        print(f"{arm:7s} n={r['n']:2d} test={r['mean']:.4f} [{r['ci95'][0]:.4f},{r['ci95'][1]:.4f}] gain={r['gain_over_k0']:+.4f} val={r['val_mean']:.4f}")


if __name__ == "__main__":
    main()
