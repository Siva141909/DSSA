"""Frozen before training, NOT run in the pilot. Gate 3 selector comparison,
for use only if a separate Gate 2 authorization is given. --selftest uses
synthetic utilities. All conclusions are restricted to the L23-only decoder."""
from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
import numpy as np  # noqa: E402

KS = (1, 3, 5)
PRIMARY, SECONDARY = "R2", ["F", "R1", "S20", "RAW_R2", "MMD_R2"]


def rk(a):
    o = np.argsort(a, kind="mergesort")
    r = np.empty(len(a))
    r[o] = np.arange(len(a))
    return r


def spearman(a, b):
    return float(np.corrcoef(rk(np.asarray(a)), rk(np.asarray(b)))[0, 1])


def kendall_b(a, b):
    c = t_a = t_b = 0
    for i, j in itertools.combinations(range(len(a)), 2):
        x, y = np.sign(a[i] - a[j]), np.sign(b[i] - b[j])
        c += x * y
        t_a += x != 0
        t_b += y != 0
    return float(c / np.sqrt(t_a * t_b))


def partial_spearman(a, b, d):
    ab, ad, bd = spearman(a, b), spearman(a, d), spearman(b, d)
    return (ab - ad * bd) / np.sqrt((1 - ad ** 2) * (1 - bd ** 2))


def score_from_rank(rank):
    s = np.empty(24)
    s[np.array(rank)] = np.arange(24, 0, -1)
    return s


def rules(sel):
    r = {k: v["rank"] for k, v in sel.items()}
    r["Lowest_R2"] = list(reversed(sel[PRIMARY]["rank"]))
    r["Early"] = list(range(24))
    r["Late"] = list(range(23, -1, -1))
    r["Middle"] = sorted(range(24), key=lambda l: (abs(l - 11.5), l))
    return r


def metrics(rank, U):
    o = np.argsort(-U, kind="mergesort")
    s = score_from_rank(rank)
    out = {"spearman": spearman(s, U), "kendall_b": kendall_b(s, U), "partial_given_depth": partial_spearman(s, U, np.arange(24))}
    for k in KS:
        a, b = list(rank[:k]), list(o[:k])
        out[f"overlap@{k}"] = len(set(a) & set(b)) / k
        out[f"regret_best@{k}"] = float(U.max() - U[a].max())
        out[f"regret_sum@{k}"] = float(U[b].sum() - U[a].sum())
    return out


def analyze(U, sel, n_random=100000, seed=20261102):
    """U: (resamples, 24); U[0] is the point estimate."""
    rs = rules(sel)
    table = {k: metrics(v, U[0]) for k, v in rs.items()}
    r = np.random.default_rng(seed)
    point = U[0]
    rnd = {k: [] for k in KS}
    for _ in range(min(n_random, 100000)):
        p = r.permutation(24)
        for k in KS:
            rnd[k].append(np.sort(point)[::-1][:k].sum() - point[p[:k]].sum())
    pct = {f"regret_sum@{k}": {n: float((np.array(rnd[k]) <= table[n][f"regret_sum@{k}"]).mean()) for n in rs} for k in KS}
    iv = {}
    for n, v in rs.items():
        m = [metrics(v, u) for u in U[1:]] if len(U) > 1 else []
        iv[n] = {c: np.percentile([x[c] for x in m], [2.5, 97.5]).tolist() for c in table[n]} if m else {}
    return {"point": table, "random_percentile": pct, "intervals": iv, "oracle_rank": np.argsort(-point, kind="mergesort").tolist()}


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        fake = {k: {"rank": list(range(23, -1, -1))} for k in ["R2", "F", "R1", "S20", "RAW_R2", "MMD_R2"]}
        U = np.vstack([np.linspace(0, .03, 24)] + [np.linspace(0, .03, 24) + np.random.default_rng(i).normal(0, .001, 24) for i in range(5)])
        o = analyze(U, fake, n_random=2000)
        assert o["point"]["Late"]["regret_sum@3"] == 0 and o["point"]["Late"]["overlap@5"] == 1 and abs(o["point"]["Early"]["spearman"] + 1) < 1e-9
        assert kendall_b([1, 2, 3], [1, 2, 3]) == 1.0
        print("selftest ok")
    else:
        raise SystemExit("Gate 3 is not authorized.")
