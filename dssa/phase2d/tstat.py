"""Student t quantiles and power without scipy. Exact integer-df t CDF
(closed-form series in theta = atan(t / sqrt(df))), inverted by bisection.
Power uses the noncentral t by fixed-seed simulation."""
from __future__ import annotations

import math

import numpy as np


def t_cdf(t: float, df: int) -> float:
    th = math.atan(t / math.sqrt(df))
    c2, s = math.cos(th) ** 2, math.sin(th)
    if df % 2:
        if df == 1:
            a = 2 * th / math.pi
        else:
            term, tot = 1.0, 1.0
            for k in range(1, (df - 3) // 2 + 1):
                term *= c2 * (2 * k) / (2 * k + 1)
                tot += term
            a = 2 / math.pi * (th + s * math.cos(th) * tot)
    else:
        term, tot = 1.0, 1.0
        for k in range(1, (df - 2) // 2 + 1):
            term *= c2 * (2 * k - 1) / (2 * k)
            tot += term
        a = s * tot
    return 0.5 * (1 + a)


def t_ppf(p: float, df: int) -> float:
    lo, hi = -1e3, 1e3
    for _ in range(200):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if t_cdf(mid, df) < p else (lo, mid)
    return (lo + hi) / 2


def power_two_sided(ncp: float, df: int, alpha: float = 0.05, n: int = 400_000, seed: int = 20261103) -> float:
    r = np.random.default_rng(seed)
    t = (r.standard_normal(n) + ncp) / np.sqrt(r.chisquare(df, n) / df)
    return float((np.abs(t) > t_ppf(1 - alpha / 2, df)).mean())


if __name__ == "__main__":
    for df, want in ((2, 4.302653), (4, 2.776445), (6, 2.446912), (48, 2.010635), (1, 12.706205), (5, 2.570582)):
        got = t_ppf(0.975, df)
        assert abs(got - want) < 1e-5, (df, got)
    print("tstat selftest ok")
