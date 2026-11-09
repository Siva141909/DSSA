"""Phase 3 Stage B selector scores (protocol v2 section 4, v3 section 4; D5, D6, D14).
Modes (one fresh process each, run under run_sequence.py scores):
  labelfree  frozen backbone, no labels: DSS-R2, GSD perturbation (V->P, 124 px -> 224
             bilinear, align_corners=False, no antialias), input-output similarity,
             activation norm; RAW_R2 and MMD descriptively.
             Pools: source = 20 Vaihingen training tiles (centroid = first 16 sorted;
             null = matched 16-vs-5 draws from the 20); target = 5 Potsdam probe tiles.
             Representation: Gate 0's (block output, patch tokens mean-pooled, 9 Gate 0
             crops per tile). Phase 3 transform (Vaihingen-train refit) for every image.
  logme      Potsdam TRAINING labels only: frozen-backbone patch tokens of every block on
             2,000 random 224 crops of the training tiles (fixed seed); 16x16 patch majority
             labels with purity >= 0.8; <= 20,000 patches, class-stratified, cap 4,000 per
             class; one-vs-rest mean LogME (You et al. 2021, fixed-point evidence).
  fisher     Potsdam TRAINING labels only: frozen backbone + final (step-2000) decoder of
             Potsdam K0 seed s + LoRA in all 24 blocks (A from seed s's LoRA seed, B = 0);
             64 batches x 8 crops from seed s's training stream; training loss (CE + Dice);
             F_l = mean over batches of sum (dL/dB_q,l)^2 + (dL/dB_v,l)^2; mean over seeds.
  freeze     combine, fix score directions, write the frozen file and its SHA-256.
Score direction (frozen here, before any single-block run): for every signal a HIGHER
score means the block is MORE preferred for adaptation; top-3 = the three highest."""
from __future__ import annotations

import hashlib
import json
import random
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import p3common as C  # noqa: E402

C.install_guards()
C.setup_paths()
import sigsafe  # noqa: E402

sigsafe.restore()
import numpy as np  # noqa: E402
import tifffile  # noqa: E402
import torch  # noqa: E402
import torch.nn.functional as F  # noqa: E402
import model as dm  # noqa: E402
import preprocessing as pp  # noqa: E402
import p3run as R  # noqa: E402

OUT = C.ART / "stage_b"
N_CROPS, B_NULL = 9, 10000
GSD_N = 124


def crops_for(name, h, w):
    seed = int(hashlib.sha256(f"phase2d-crops-v1:{name}".encode()).hexdigest()[:16], 16)
    r = random.Random(seed)
    return [(0, 0)] + [(r.randrange(h - 223), r.randrange(w - 223)) for _ in range(N_CROPS - 1)]


def rk(a):
    o = np.argsort(a, kind="mergesort")
    r = np.empty(len(a))
    r[o] = np.arange(len(a))
    return r


def spear(a, b):
    return float(np.corrcoef(rk(np.asarray(a, float)), rk(np.asarray(b, float)))[0, 1])


def unit(x):
    return x / (np.linalg.norm(x, axis=-1, keepdims=True) + 1e-8)


def D(S, T):
    c = unit(S.mean(0))
    return (1 - (unit(T) * c[None]).sum(-1)).mean(0)


def null_matched(P, ns, nt, B, seed):
    r = np.random.default_rng(seed)
    out = np.zeros((B, 24))
    for b in range(B):
        p = r.permutation(len(P))
        out[b] = D(P[p[:ns]], P[p[ns:ns + nt]])
    return out


def mmd_obs_null(X, src, tgt, pool, B, seed):
    """Biased RBF MMD^2 with median bandwidth per comparison (gate0_dss.mmd_all), with the
    Phase 3 pools: observed = 16 source vs 5 target; null = 16-vs-5 draws from the pool."""
    d2 = np.stack([((X[:, None, l] - X[None, :, l]) ** 2).sum(-1) for l in range(24)])

    def one(l, a, b):
        i = np.concatenate([a, b])
        sub = d2[l][np.ix_(i, i)]
        bw2 = np.median(np.sqrt(sub[~np.eye(len(i), dtype=bool)])) ** 2
        k = np.exp(-sub / (2 * bw2))
        na = len(a)
        return k[:na, :na].mean() + k[na:, na:].mean() - 2 * k[:na, na:].mean()
    obs = np.array([one(l, src, tgt) for l in range(24)])
    r = np.random.default_rng(seed)
    null = np.zeros((B, 24))
    for k in range(B):
        p = pool[r.permutation(len(pool))]
        for l in range(24):
            null[k, l] = one(l, p[:16], p[16:21])
    return obs, null


def zstats(obs, null):
    mu, sd = null.mean(0), null.std(0)
    return {"raw": obs.tolist(), "z": ((obs - mu) / (sd + 1e-8)).tolist(), "null_mean": mu.tolist(), "null_sd": sd.tolist()}


def start(name):
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / f"{name}.json"
    if p.exists():
        raise FileExistsError(p)
    state = {"stage": name}
    mon = C.Telemetry(None, state, OUT)
    mon.start()
    return p, mon


def finish(p, mon, obj, t0):
    if mon.fault:
        raise RuntimeError(f"STOP: {mon.fault}")
    mon.halt = True
    obj["seconds"] = time.time() - t0
    obj["peak_mb"] = C.rusage()["lifetime_max_phys_footprint_mb"]
    obj["memory"] = C.memory_record(mon)
    obj["opened"] = {"potsdam_images": sorted(C.OPENED["images"]), "potsdam_labels": sorted(C.OPENED["labels"])}
    obj["code_hash"] = C.code_hash()
    C.write_json_atomic(p, obj)
    print(f"[{p.stem}] {obj['seconds']:.0f}s peak {obj['peak_mb']:.0f} MB", flush=True)


def labelfree():
    t0 = time.time()
    p, mon = start("labelfree")
    s = C.split()
    co = R.transform()
    enc = dm.load_frozen_encoder(1, "mps")
    enc.eval()
    cap_in, cap_out = [None] * 24, [None] * 24

    def hk(k):
        def f(m, i, o):
            cap_in[k], cap_out[k] = i[0].detach(), o.detach()
        return f
    for k, b in enumerate(enc.blocks):
        b.register_forward_hook(hk(k))

    def run(batch):
        with torch.no_grad():
            enc.forward_features(torch.cat(batch).to("mps"), temporal_coords=None, location_coords=None)

    src = sorted(C.V_TRAIN)
    files = [("V", n) for n in src] + [("P", n) for n in s["probe"]]
    X = np.zeros((len(files), N_CROPS, 24, 1024), np.float32)
    gsd_num = np.zeros(24)
    gsd_cnt = 0
    io_cos, act_norm, tok = np.zeros(24), np.zeros(24), 0
    crops_used = {}
    for fi, (dom, n) in enumerate(files):
        a = tifffile.imread(str(C.VAIHINGEN_IMG_DIR / n)) if dom == "V" else C.potsdam_image(n)
        cl = crops_for(n, *a.shape[:2])
        crops_used[n] = cl
        xs = [pp.build_prithvi_input(co.apply(a[y:y + 224, x:x + 224, :])) for y, x in cl]
        feats = np.zeros((N_CROPS, 24, 1024), np.float32)
        for st in range(0, N_CROPS, 8):
            run(xs[st:st + 8])
            for l in range(24):
                feats[st:st + 8, l] = cap_out[l][:, 1:].mean(1).cpu().numpy()
                if dom == "P":
                    hi, ho = cap_in[l][:, 1:], cap_out[l][:, 1:]
                    io_cos[l] += F.cosine_similarity(hi, ho, dim=-1).sum().item()
                    act_norm[l] += ho.norm(dim=-1).sum().item()
            if dom == "P":
                tok += cap_out[0][:, 1:].shape[0] * cap_out[0][:, 1:].shape[1]
        X[fi] = feats
        if dom == "V":  # GSD perturbation on source images only
            gx = []
            for y, x in cl:
                cy, cx = y + 112, x + 112
                y0, x0 = cy - GSD_N // 2, cx - GSD_N // 2
                assert 0 <= y0 and 0 <= x0 and y0 + GSD_N <= a.shape[0] and x0 + GSD_N <= a.shape[1]
                w = torch.from_numpy(co.apply(a[y0:y0 + GSD_N, x0:x0 + GSD_N, :])).permute(2, 0, 1)[None]
                up = F.interpolate(w, size=(224, 224), mode="bilinear", align_corners=False, antialias=False)[0].permute(1, 2, 0).numpy()
                gx.append(pp.build_prithvi_input(up))
            gf = np.zeros((N_CROPS, 24, 1024), np.float32)
            for st in range(0, N_CROPS, 8):
                run(gx[st:st + 8])
                for l in range(24):
                    gf[st:st + 8, l] = cap_out[l][:, 1:].mean(1).cpu().numpy()
            gsd_num += (np.linalg.norm(gf - feats, axis=-1) / np.linalg.norm(feats, axis=-1)).sum(0)
            gsd_cnt += N_CROPS
        print("  features", n, flush=True)
    X9 = X.mean(1)
    S, T, pool = X9[:16], X9[20:25], X9[:20]
    r2 = zstats(D(S, T), null_matched(pool, 16, 5, B_NULL, 12))
    mobs, mnull = mmd_obs_null(X9, np.arange(16), np.arange(20, 25), np.arange(20), B_NULL, 14)
    mm = zstats(mobs, mnull)
    out = {"pools": {"source_centroid": src[:16], "null_pool": src, "target_probe": s["probe"]},
           "crops": crops_used, "n_null": B_NULL,
           "scores": {"DSS_R2": r2["z"], "GSD": (gsd_num / gsd_cnt).tolist(), "IO_SIM": (1 - io_cos / tok).tolist(), "ACT_NORM": (act_norm / tok).tolist(),
                      "RAW_R2": r2["raw"], "MMD_R2": mm["z"]},
           "dss_r2_detail": r2, "mmd_detail": mm, "probe_tokens": tok, "gsd_crops": gsd_cnt}
    np.savez(OUT / "labelfree_features.npz", X9=X9, names=np.array([n for _, n in files]))
    finish(p, mon, out, t0)


def logme_binary(f, y, u, sigma):
    """LogME evidence per sample for one binary target (official fixed-point algorithm)."""
    N, Dd = f.shape
    x = u.T @ y
    x2 = x ** 2
    res_x2 = (y ** 2).sum() - x2.sum()
    alpha, beta = 1.0, 1.0
    for _ in range(11):
        t = alpha / beta
        gamma = (sigma / (sigma + t)).sum()
        m2 = (sigma * x2 / ((t + sigma) ** 2)).sum()
        res2 = (x2 / ((1 + sigma / t) ** 2)).sum() + res_x2
        alpha = gamma / (m2 + 1e-5)
        beta = (N - gamma) / (res2 + 1e-5)
        if abs(alpha / beta - t) / t <= 1e-3:
            break
    ev = Dd / 2 * np.log(alpha) + N / 2 * np.log(beta) - 0.5 * np.sum(np.log(alpha + beta * sigma)) - beta / 2 * res2 - alpha / 2 * m2 - N / 2 * np.log(2 * np.pi)
    return ev / N


def logme():
    t0 = time.time()
    p, mon = start("logme")
    s = C.split()
    train = s["train"]
    C.LABEL_ALLOW.update(C.potsdam_tile_id(n) for n in train)
    co = R.transform()
    rng = np.random.default_rng(31)
    crops = [(int(rng.integers(len(train))), int(rng.integers(0, 6000 - 224 + 1)), int(rng.integers(0, 6000 - 224 + 1))) for _ in range(2000)]
    labs = {}
    for n in train:
        labs[n] = C.potsdam_label(n)
    pl = np.zeros((2000, 196), np.int64)
    pur = np.zeros((2000, 196))
    for ci, (fi, y, x) in enumerate(crops):
        L = labs[train[fi]][y:y + 224, x:x + 224].reshape(14, 16, 14, 16).transpose(0, 2, 1, 3).reshape(196, 256)
        cnt = np.stack([(L == c).sum(1) for c in range(6)], 1)
        pl[ci], pur[ci] = cnt.argmax(1), cnt.max(1) / 256
    del labs
    ok = pur >= 0.8
    avail = np.bincount(pl[ok], minlength=6)
    cap = 4000
    while np.minimum(avail, cap).sum() > 20000:
        cap -= 1
    quota = np.minimum(avail, cap)
    idx = np.argwhere(ok)
    sel = []
    for c in range(6):
        cand = idx[pl[ok] == c]
        sel += cand[rng.choice(len(cand), quota[c], replace=False)].tolist() if quota[c] else []
    sel = sorted(map(tuple, sel))
    y_all = np.array([pl[a, b] for a, b in sel])
    by_crop = {}
    for j, (a, b) in enumerate(sel):
        by_crop.setdefault(a, []).append((j, b))
    enc = dm.load_frozen_encoder(1, "mps")
    enc.eval()
    cap_out = [None] * 24
    for k, b in enumerate(enc.blocks):
        b.register_forward_hook(lambda m, i, o, k=k: cap_out.__setitem__(k, o.detach()))
    feats = np.zeros((24, len(sel), 1024), np.float32)
    crop_ids = sorted(by_crop)
    imgs = {}
    for st in range(0, len(crop_ids), 8):
        if mon.fault:
            raise RuntimeError(f"STOP: {mon.fault}")
        chunk = crop_ids[st:st + 8]
        xs = []
        for ci in chunk:
            fi, y, x = crops[ci]
            if fi not in imgs:
                imgs[fi] = C.potsdam_image(train[fi])
            xs.append(pp.build_prithvi_input(co.apply(imgs[fi][y:y + 224, x:x + 224, :])))
        with torch.no_grad():
            enc.forward_features(torch.cat(xs).to("mps"), temporal_coords=None, location_coords=None)
        for bi, ci in enumerate(chunk):
            js = [j for j, _ in by_crop[ci]]
            ps = [pp_ for _, pp_ in by_crop[ci]]
            for l in range(24):
                feats[l, js] = cap_out[l][bi, 1:][ps].cpu().numpy()
    del imgs
    scores, per_class = [], []
    for l in range(24):
        f = feats[l].astype(np.float64)
        u, sv, _ = np.linalg.svd(f, full_matrices=False)
        sigma = sv ** 2
        ev = [logme_binary(f, (y_all == c).astype(np.float64), u, sigma) for c in range(6) if quota[c] > 0]
        per_class.append(ev)
        scores.append(float(np.mean(ev)))
        print("  logme block", l, round(scores[-1], 4), flush=True)
    out = {"scores": {"LOGME": scores}, "per_class_evidence": per_class, "n_patches": len(sel), "per_class_patches": quota.tolist(),
           "available_pure_patches": avail.tolist(), "class_cap_applied": int(cap), "n_crops": 2000, "crop_seed": 31,
           "crops_sha256": hashlib.sha256(json.dumps(crops).encode()).hexdigest(), "snapped_labels": C.SNAPPED}
    finish(p, mon, out, t0)


def fisher_batches(train, seeds, co, n_items):
    """The first n_items draws of each seed's training stream, exactly as
    PotsdamSegDatasetU8 produces them (same RNG calls in the same order, same crop,
    per-crop calibration and augmentation), without holding the 20-tile cache: each tile
    is decoded once and only the needed crops are kept (memory guard, 16 GB machine)."""
    plans = {}
    for seed in seeds:
        r = random.Random(seed)
        plan = []
        for _ in range(n_items):
            fn = r.choice(train)
            y0, x0 = r.randrange(0, 6000 - 223), r.randrange(0, 6000 - 223)
            plan.append((fn, y0, x0, r.random() < 0.5, r.random() < 0.5, r.randrange(4)))
        plans[seed] = (plan, R.rng_hash(r))
    crops = {}
    for fn in train:
        need = [(seed, i, it) for seed in seeds for i, it in enumerate(plans[seed][0]) if it[0] == fn]
        if not need:
            continue
        img, lab = C.potsdam_image(fn), C.potsdam_label(fn)
        for seed, i, (_, y0, x0, *_r) in need:
            crops[(seed, i)] = (img[y0:y0 + 224, x0:x0 + 224].copy(), lab[y0:y0 + 224, x0:x0 + 224].copy())
        del img, lab
    out = {}
    for seed in seeds:
        xs, ys = [], []
        for i, (_, _, _, hf, vf, k) in enumerate(plans[seed][0]):
            im, lb = crops[(seed, i)]
            im = co.apply(im.astype(np.float64))
            lb = lb.astype(np.int64)
            if hf:
                im, lb = np.ascontiguousarray(im[:, ::-1, :]), np.ascontiguousarray(lb[:, ::-1])
            if vf:
                im, lb = np.ascontiguousarray(im[::-1, :, :]), np.ascontiguousarray(lb[::-1, :])
            if k:
                im, lb = np.ascontiguousarray(np.rot90(im, k, axes=(0, 1))), np.ascontiguousarray(np.rot90(lb, k, axes=(0, 1)))
            xs.append(pp.build_prithvi_input(im).squeeze(0))
            ys.append(torch.from_numpy(lb.copy()).long())
        out[seed] = (xs, ys, plans[seed][1])
    return out


def fisher():
    t0 = time.time()
    p, mon = start("fisher")
    s = C.split()
    from losses import CEDiceLoss
    import models as M
    C.LABEL_ALLOW.update(C.potsdam_tile_id(n) for n in s["train"])
    per_seed, ck = {}, {}
    loss_fn = CEDiceLoss()
    data = fisher_batches(s["train"], C.SEEDS, R.transform(), 64 * 8)
    for seed in C.SEEDS:
        rid = f"p3_K0_s{seed}"
        d = C.RUNS / rid
        summ = json.load(open(d / "summary.json"))
        ckp = d / f"{rid}_final.pt"
        if C.sha256_file(ckp) != summ["checkpoint_sha256"]:
            raise RuntimeError(f"{rid}: checkpoint hash")
        ck[rid] = summ["checkpoint_sha256"]
        model, mods = M.build(list(range(24)), "mps", seed + C.LORA_SEED_OFFSET)
        payload = torch.load(ckp, map_location="cpu", weights_only=False)
        if payload["step"] != 2000 or payload["layer_indices"] != []:
            raise RuntimeError(f"{rid}: not a step-2000 K0 checkpoint")
        model.decoder.load_state_dict(payload["decoder_state_dict"])
        for prm in model.decoder.parameters():
            prm.requires_grad_(False)
        for m in mods:
            m.lora_A_q.requires_grad_(False)
            m.lora_A_v.requires_grad_(False)
            assert torch.count_nonzero(m.lora_B_q) == 0 and torch.count_nonzero(m.lora_B_v) == 0
        model.train()  # the training forward (eval mode takes a no-grad path); GroupNorm only, no dropout, so nothing is stochastic
        xs, ys, _ = data[seed]
        acc = np.zeros(24)
        for b in range(64):
            if mon.fault:
                raise RuntimeError(f"STOP: {mon.fault}")
            x = torch.stack(xs[b * 8:(b + 1) * 8]).to("mps")
            y = torch.stack(ys[b * 8:(b + 1) * 8]).to("mps")
            model.zero_grad(set_to_none=True)
            loss_fn(model(x), y).backward()
            for l, m in enumerate(mods):
                acc[l] += (m.lora_B_q.grad.cpu().double() ** 2).sum().item() + (m.lora_B_v.grad.cpu().double() ** 2).sum().item()
        per_seed[str(seed)] = (acc / 64).tolist()
        print("  fisher seed", seed, flush=True)
        del model, mods, payload
        torch.mps.empty_cache()
    out = {"scores": {"FISHER": np.mean([per_seed[k] for k in per_seed], 0).tolist()}, "per_seed": per_seed, "k0_checkpoints": ck,
           "batches": 64, "batch_size": 8, "loss": "CEDiceLoss (the training loss)", "stream_state_after_512_draws": {str(k): v[2] for k, v in data.items()},
           "snapped_labels": C.SNAPPED}
    finish(p, mon, out, t0)


def freeze():
    if C.SCORES_FILE.exists():
        raise FileExistsError(C.SCORES_FILE)
    parts = {k: json.load(open(OUT / f"{k}.json")) for k in ("labelfree", "logme", "fisher")}
    sc = {**parts["labelfree"]["scores"], **parts["logme"]["scores"], **parts["fisher"]["scores"]}
    top3 = {k: [int(i) for i in np.lexsort((np.arange(24), -np.asarray(v, dtype=np.float64)))[:3]] for k, v in sc.items()}
    out = {"status": "FROZEN before any Stage C single-block run",
           "frozen_at": time.time(),
           "direction": "higher score = more preferred for adaptation, for every signal; top-3 = three highest (ties: lower block index)",
           "roles": {"label_free_candidates": ["DSS_R2", "GSD"], "literature_baselines": ["IO_SIM", "ACT_NORM"],
                     "label_using_references": ["FISHER", "LOGME"], "descriptive_only": ["RAW_R2", "MMD_R2"]},
           "prior": {"formula": "p(l) = -1.8386e-4 l^2 + 4.9992e-3 l - 4.1343e-4", "top3": [14, 13, 15]},
           "gate": {"r_res": ">= 0.30", "leave_one_seed_out_r_res": ">= 0.15 each", "tile_bootstrap_2.5pct": ">= 0 (8 tiles, 10,000 resamples)",
                    "top3_regret": "<= prior top-3 {14,13,15} regret", "non_inferential": True},
           "scores": sc, "top3": top3,
           "depth_spearman": {k: spear(v, range(24)) for k, v in sc.items()},
           "source_files_sha256": {k: C.sha256_file(OUT / f"{k}.json") for k in parts},
           "split_sha256": C.sha256_file(C.SPLIT_FILE), "transform_sha256": C.sha256_file(C.TRANSFORM_FILE),
           "single_block_runs_existing": sorted(p.name for p in C.RUNS.glob("p3_L*")) if C.RUNS.exists() else []}
    if out["single_block_runs_existing"]:
        raise RuntimeError("single-block runs exist; scores cannot be frozen as prospective")
    C.write_json_atomic(C.SCORES_FILE, out)
    h = C.sha256_file(C.SCORES_FILE)
    C.SCORES_HASH_FILE.write_text(f"{h}  {C.SCORES_FILE.name}\n")
    C.write_json_atomic(OUT / "freeze.json", {"sha256": h, "peak_mb": C.rusage()["lifetime_max_phys_footprint_mb"]})
    print("[frozen]", h, json.dumps(top3), flush=True)


if __name__ == "__main__":
    {"labelfree": labelfree, "logme": logme, "fisher": fisher, "freeze": freeze}[sys.argv[1]]()
