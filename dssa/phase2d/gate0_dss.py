"""Gate 0: extract and freeze all selector rankings. No labels, no training.
R2 is an exploratory signal choice; freezing it here makes the later oracle
evaluation prospective. Inputs: 38 Potsdam tiles, 20 target-train tiles only."""
from __future__ import annotations

import hashlib
import itertools
import json
import random
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

C.install_guards()
sys.path.insert(0, str(C.ROOT / "sanity"))
import numpy as np  # noqa: E402
import tifffile  # noqa: E402
import torch  # noqa: E402
import model as dm  # noqa: E402
import preprocessing as pp  # noqa: E402

N_CROPS, B_NULL = 9, 10000
OUT = C.GATE0


def crops_for(name: str, h: int, w: int) -> list[tuple[int, int]]:
    seed = int(hashlib.sha256(f"phase2d-crops-v1:{name}".encode()).hexdigest()[:16], 16)
    r = random.Random(seed)
    return [(0, 0)] + [(r.randrange(h - 223), r.randrange(w - 223)) for _ in range(N_CROPS - 1)]


def extract():
    enc = dm.load_frozen_encoder(1, "mps")
    s = json.load(open(C.ROOT / "artifacts" / "radiometric_transform.json"))
    co = pp.SourceFitAffine(tuple(s["offset_IR_R_G"]), tuple(s["scale_IR_R_G"]))
    cap = [None] * 24
    for k, b in enumerate(enc.blocks):
        b.register_forward_hook(lambda m, i, o, k=k: cap.__setitem__(k, o.detach()))
    pots = sorted((C.ROOT / "data" / "potsdam_irrg").glob("*.tif"))
    files = pots + [C.ROOT / "data" / "vaihingen_irrg" / n for n in C.TRAIN]
    assert len(pots) == 38 and not (C.FORBIDDEN & {f.name for f in files})
    pre = np.zeros((len(files), N_CROPS, 24, 1024), np.float32)
    l23post = np.zeros((len(files), N_CROPS, 1024), np.float32)
    crops = {}
    for fi, f in enumerate(files):
        a = tifffile.imread(str(f))
        cl = crops_for(f.name, *a.shape[:2])
        crops[f.name] = cl
        xs = [pp.build_prithvi_input(co.apply(a[y:y + 224, x:x + 224, :])) for y, x in cl]
        with torch.no_grad():
            for st in range(0, N_CROPS, 8):
                o = enc.forward_features(torch.cat(xs[st:st + 8]).to("mps"), temporal_coords=None, location_coords=None)
                for li in range(24):
                    pre[fi, st:st + 8, li] = cap[li][:, 1:].mean(1).cpu().numpy()
                l23post[fi, st:st + 8] = o[-1][:, 1:].mean(1).cpu().numpy()
    return pre, l23post, [f.name for f in files], crops


def rank_desc(v):
    return np.lexsort((np.arange(24), -np.round(np.asarray(v) / 1e-6))).tolist()


def rk(a):
    o = np.argsort(a, kind="mergesort")
    r = np.empty(len(a))
    r[o] = np.arange(len(a))
    return r


def spear(a, b):
    return float(np.corrcoef(rk(np.asarray(a)), rk(np.asarray(b)))[0, 1])


def unit(x):
    return x / (np.linalg.norm(x, axis=-1, keepdims=True) + 1e-8)


def D(S, T):
    c = S.mean(0)
    c = c / (np.linalg.norm(c, axis=-1, keepdims=True) + 1e-8)
    return (1 - (unit(T) * c[None]).sum(-1)).mean(0)


def null_matched(P, ns, nt, B, seed):
    r = np.random.default_rng(seed)
    out = np.zeros((B, 24))
    for b in range(B):
        p = r.permutation(len(P))
        out[b] = D(P[p[:ns]], P[p[ns:ns + nt]])
    return out


def stats(obs, null):
    mu, sd = null.mean(0), null.std(0)
    z = (obs - mu) / (sd + 1e-8)
    p = ((null >= obs).sum(0) + 1) / (len(null) + 1)
    mx = ((null - mu) / (sd + 1e-8)).max(1)
    pfw = np.array([((mx >= v).sum() + 1) / (len(null) + 1) for v in z])
    return dict(raw=obs.tolist(), z=z.tolist(), null_mean=mu.tolist(), null_sd=sd.tolist(), p=p.tolist(), p_fw=pfw.tolist(), rank=rank_desc(z), depth_spearman=spear(z, range(24)))


def boot_files(P, S, T, mu, sd, B, seed):
    r = np.random.default_rng(seed)
    ranks, sp = np.zeros((B, 24), int), np.zeros(B)
    for b in range(B):
        z = (D(S[r.integers(0, len(S), len(S))], T[r.integers(0, len(T), len(T))]) - mu) / (sd + 1e-8)
        o = rank_desc(z)
        ranks[b, o] = np.arange(24)
        sp[b] = spear(z, range(24))
    return summarize(ranks, sp, rank_ref=None)


def summarize(ranks, sp, rank_ref):
    ci = np.percentile(ranks, [2.5, 97.5], axis=0).tolist()
    inc = {str(k): (ranks < k).mean(0).tolist() for k in (1, 3, 5, 8)}
    return dict(n=len(ranks), rank_lo=ci[0], rank_hi=ci[1], top_k_inclusion=inc, depth_spearman_median=float(np.median(sp)), depth_spearman_ci=np.percentile(sp, [2.5, 97.5]).tolist())


def boot_crops(pre, B, seed):
    """R2 with crops redrawn within file; null recomputed. Crop uncertainty only."""
    r = np.random.default_rng(seed)
    ranks, sp = np.zeros((B, 24), int), np.zeros(B)
    for b in range(B):
        idx = r.integers(0, N_CROPS, (pre.shape[0], N_CROPS))
        X = pre[np.arange(pre.shape[0])[:, None], idx].mean(1)
        n = null_matched(X[:38], 16, 5, 500, seed + b)
        z = (D(X[:16], X[38:43]) - n.mean(0)) / (n.std(0) + 1e-8)
        o = rank_desc(z)
        ranks[b, o] = np.arange(24)
        sp[b] = spear(z, range(24))
    return summarize(ranks, sp, None)


def mmd_all(X, ns, nt, B, seed):
    """Biased RBF MMD^2, median bandwidth per comparison, same files and same
    representation as R2. Vectorized replica of sanity/mmd.py."""
    n = len(X)
    d2 = np.stack([((X[:, None, l] - X[None, :, l]) ** 2).sum(-1) for l in range(24)])

    def one(l, a, b):
        i = np.concatenate([a, b])
        sub = d2[l][np.ix_(i, i)]
        bw2 = np.median(np.sqrt(sub[~np.eye(len(i), dtype=bool)])) ** 2
        k = np.exp(-sub / (2 * bw2))
        na = len(a)
        return k[:na, :na].mean() + k[na:, na:].mean() - 2 * k[:na, na:].mean()
    a, b = np.arange(16), np.arange(38, 43)
    obs = np.array([one(l, a, b) for l in range(24)])
    r = np.random.default_rng(seed)
    null = np.zeros((B, 24))
    for k in range(B):
        p = r.permutation(38)
        for l in range(24):
            null[k, l] = one(l, p[:ns], p[ns:ns + nt])
    return obs, null


def main():
    t0 = time.time()
    pre, l23post, names, crops = extract()
    assert names[38:43] == C.PROBE
    print("extraction", time.time() - t0, flush=True)
    np.savez(OUT / "features_pre.npz", pre=pre, l23post=l23post, names=np.array(names))
    frozen = json.load(open(C.ROOT / "artifacts" / "dss" / "phase2b_final_dss_results.json"))

    # F: frozen pipeline, recomputed on the top-left crop, as a reproducibility check
    Xf = pre[:, 0].copy()
    Xf[:, 23] = l23post[:, 0]
    raw_f = D(Xf[:16], Xf[38:43])
    rr, idx, leg = random.Random(1234), list(range(16)), []
    for _ in range(40):
        rr.shuffle(idx)
        leg.append(D(Xf[16:32][idx[:8]], Xf[16:32][idx[8:16]]))
    leg = np.array(leg)
    z_f = (raw_f - leg.mean(0)) / (leg.std(0) + 1e-8)
    repro = {"raw_max_abs_diff": float(np.abs(raw_f - np.array(frozen["raw_dss"])).max()),
             "z_max_abs_diff": float(np.abs(z_f - np.array(frozen["normalized_dss"])).max()),
             "rank_identical": rank_desc(z_f) == frozen["ranking_desc"]}
    if not (repro["raw_max_abs_diff"] < 1e-5 and repro["z_max_abs_diff"] < 1e-3 and repro["rank_identical"]):
        raise RuntimeError(f"frozen DSS not reproduced: {repro}")
    print(repro, flush=True)

    X1, X9 = pre[:, 0], pre.mean(1)
    sel = {"F": {"score": z_f.tolist(), "rank": frozen["ranking_desc"], "desc": "frozen Phase 2B-A ranking"}}
    r1 = stats(D(X1[:16], X1[38:43]), null_matched(X1[:38], 16, 5, B_NULL, 11))
    r2n = null_matched(X9[:38], 16, 5, B_NULL, 12)
    r2 = stats(D(X9[:16], X9[38:43]), r2n)
    s20 = stats(D(X9[:16], X9[38:58]), null_matched(X9[:38], 16, 20, B_NULL, 13))
    print("rankings done", time.time() - t0, flush=True)
    mobs, mnull = mmd_all(X9, 16, 5, B_NULL, 14)
    mm = stats(mobs, mnull)
    print("mmd done", time.time() - t0, flush=True)
    sel["R1"], sel["R2"], sel["S20"], sel["MMD_R2"] = r1, r2, s20, mm
    sel["RAW_R2"] = {"score": r2["raw"], "rank": rank_desc(r2["raw"]), "desc": "unnormalized R2 distance"}
    for k in ("R1", "R2", "S20", "MMD_R2"):
        sel[k]["score"] = sel[k]["z"]
    unc = {
        "file_bootstrap_R1": boot_files(X1, X1[:16], X1[38:43], np.array(r1["null_mean"]), np.array(r1["null_sd"]), 5000, 21),
        "file_bootstrap_R2": boot_files(X9, X9[:16], X9[38:43], np.array(r2["null_mean"]), np.array(r2["null_sd"]), 5000, 22),
        "crop_resample_R2": boot_crops(pre, 200, 1000),
    }
    loo = []
    for i in range(5):
        keep = [38 + j for j in range(5) if j != i]
        n = null_matched(X9[:38], 16, 4, 2000, 30 + i)
        loo.append(rank_desc((D(X9[:16], X9[keep]) - n.mean(0)) / (n.std(0) + 1e-8))[:8])
    unc["leave_one_target_out_R2_top8"] = [sorted(x) for x in loo]
    agree = {f"{a}|{b}": spear(sel[a]["score"], sel[b]["score"]) for a, b in itertools.combinations(["F", "R1", "R2", "S20", "RAW_R2", "MMD_R2"], 2)}
    out = {
        "status": "FROZEN before any Phase 2D training",
        "note": "R2 is an exploratory signal choice. The oracle evaluation of it is prospective. Crops, scores and rankings below are not changed after this file is hashed.",
        "reproduction_of_frozen_dss": repro, "n_null": B_NULL, "crops": crops, "selectors": sel, "uncertainty": unc,
        "selector_agreement_spearman": agree,
        "depth_spearman": {k: spear(v["score"], range(24)) for k, v in sel.items()},
    }
    C.write_json_atomic(OUT / "frozen_rankings.json", out)
    print(json.dumps({k: {"rank": v["rank"][:8], "depth": out["depth_spearman"][k], "z": [round(min(v["score"]), 3), round(max(v["score"]), 3)]} for k, v in sel.items()}, indent=0))
    print("min p / max-T:", {k: (min(sel[k]["p"]), min(sel[k]["p_fw"])) for k in ("R1", "R2", "S20", "MMD_R2")})
    print(json.dumps({k: {a: b for a, b in v.items() if a.startswith("depth")} for k, v in unc.items() if isinstance(v, dict)}))
    print("LOTO", unc["leave_one_target_out_R2_top8"], "agree", {k: round(v, 3) for k, v in agree.items()}, "total_s", time.time() - t0)


if __name__ == "__main__":
    main()
