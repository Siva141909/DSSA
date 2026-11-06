"""DSSA Phase 2D shared safety layer: paths, guards, hashes, monitors.

Permitted write locations (PHASE2D_ADDENDUM.md, correction 7):
  dssa/phase2d/            code and addendum
  dssa/artifacts/phase2d/  all generated evidence
  .gitignore               the single appended ignore rule, done once at Gate 0
Everything else under the project is read-only to this code.
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
import random
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT.parent
CODE = ROOT / "phase2d"
ART = ROOT / "artifacts" / "phase2d"
GATE0 = ART / "gate0"
RUNS = ART / "runs"
MANIFEST = ART / "manifest_pilot.json"
BASELINE = GATE0 / "baseline_hashes.json"
ALLOWED_WRITE = (ART, CODE)

SPLIT = json.load(open(ROOT / "artifacts" / "splits" / "vaihingen_target_split_manifest.json"))["partitions"]
TRAIN, VAL, PROBE, FORBIDDEN = SPLIT["target_train"], SPLIT["target_validation"], SPLIT["target_probe"], frozenset(SPLIT["target_test"])
ALLOWED_TILES = frozenset(TRAIN) | frozenset(VAL)
assert not (ALLOWED_TILES & FORBIDDEN)

MEM_LIMIT_MB = 11.5 * 1024
SWAP_GROWTH_LIMIT_MB = 512
BACKBONE_FP = None  # filled from the baseline file
PILOT_SEEDS = (1000, 2000, 3000)
LORA_SEED_OFFSET = 7_000_000

P2C = ROOT / "artifacts" / "phase2c" / "runs"
P2C_RUNS = ["run000_K0_K0_decoder_only", "run001_K2_DSSA", "run002_K2_Early", "run003_K2_Late", "run004_K2_LowestDSS"]


def frozen_files() -> list[Path]:
    fs = []
    for r in P2C_RUNS:
        fs += [P2C / r / f"{r}_best.pt", P2C / r / "result.json"]
    fs += [ROOT / "config" / "phase2b_training_protocol.json",
           ROOT / "artifacts" / "splits" / "vaihingen_target_split_manifest.json",
           ROOT / "artifacts" / "dss" / "phase2b_final_dss_results.json",
           ROOT / "artifacts" / "radiometric_transform.json",
           ROOT / "artifacts" / "phase2c" / "phase2c_batch1_checkpoint_report.json"]
    return fs


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def frozen_hashes() -> dict:
    return {str(p.relative_to(PROJECT)): sha256_file(p) for p in frozen_files()}


def assert_frozen_unchanged() -> None:
    base = json.load(open(BASELINE))["frozen"]
    now = frozen_hashes()
    bad = [k for k in base if base[k] != now.get(k)]
    if bad:
        raise RuntimeError(f"FROZEN ARTIFACT CHANGED: {bad}")


def code_hash() -> dict:
    return {p.name: sha256_file(p) for p in sorted(CODE.glob("*")) if p.is_file() and p.suffix in (".py", ".md")}


def canon_hash(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()


def config_hash(entry: dict) -> str:
    return canon_hash({k: v for k, v in entry.items() if k not in ("config_hash", "est_seconds")})


def write_json_atomic(path: Path, obj) -> None:
    check_write_path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=1, default=str)
    os.replace(tmp, path)


def check_write_path(path) -> None:
    p = Path(path).resolve()
    if not any(p == a or a in p.parents for a in ALLOWED_WRITE):
        raise PermissionError(f"write outside approved Phase 2D paths: {p}")


def install_guards() -> None:
    """Hard stops for target-test access and for writes outside approved paths."""
    proj = str(PROJECT)
    allowed = tuple(str(a) for a in ALLOWED_WRITE)

    def hook(event, args):
        if event != "open":
            return
        path, mode, flags = args
        if not isinstance(path, (str, bytes, os.PathLike)):
            return
        s = os.fsdecode(path)
        if os.path.basename(s) in FORBIDDEN:
            raise PermissionError(f"TARGET-TEST ACCESS ATTEMPTED: {s}")
        writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT))
        if writing and s.startswith(proj) and not s.startswith(allowed):
            raise PermissionError(f"write outside approved Phase 2D paths: {s}")

    sys.addaudithook(hook)


def install_tile_allowlist(dataset_module, opened: set) -> None:
    """The label zip is a single file, so member reads are checked here too."""
    img, lab = dataset_module.load_irrg_image, dataset_module.load_label_array

    def check(fn):
        if fn in FORBIDDEN or fn not in ALLOWED_TILES:
            raise PermissionError(f"TARGET-TEST OR UNAPPROVED TILE ACCESS ATTEMPTED: {fn}")
        opened.add(fn)

    def g_img(fn):
        check(fn)
        return img(fn)

    def g_lab(fn):
        check(fn)
        return lab(fn)

    dataset_module.load_irrg_image, dataset_module.load_label_array = g_img, g_lab


def rusage() -> dict:
    buf = (ctypes.c_uint64 * 48)()
    if ctypes.CDLL("libproc.dylib").proc_pid_rusage(os.getpid(), 4, ctypes.byref(buf)) != 0:
        raise OSError("proc_pid_rusage failed")
    v = list(buf)[2:]
    return {"resident_mb": v[6] / 2**20, "phys_footprint_mb": v[7] / 2**20, "lifetime_max_phys_footprint_mb": v[28] / 2**20}


_libc = ctypes.CDLL("libc.dylib")


def pressure_level() -> int:
    """1 normal, 2 warning, 4 critical."""
    v, n = ctypes.c_int(0), ctypes.c_size_t(4)
    _libc.sysctlbyname(b"kern.memorystatus_vm_pressure_level", ctypes.byref(v), ctypes.byref(n), None, 0)
    return v.value


class XswUsage(ctypes.Structure):
    _fields_ = [("total", ctypes.c_uint64), ("avail", ctypes.c_uint64), ("used", ctypes.c_uint64), ("pagesize", ctypes.c_uint32), ("encrypted", ctypes.c_uint32)]


def swap_used_mb() -> float:
    x, n = XswUsage(), ctypes.c_size_t(ctypes.sizeof(XswUsage))
    _libc.sysctlbyname(b"vm.swapusage", ctypes.byref(x), ctypes.byref(n), None, 0)
    return x.used / 2**20


class Monitor(threading.Thread):
    """Background sampler. Sets .fault; the training thread raises at its next tick."""

    def __init__(self, dt: float = 0.5, use_mps: bool = True):
        super().__init__(daemon=True)
        self.dt, self.use_mps, self.halt, self.fault = dt, use_mps, False, None
        self.swap0 = swap_used_mb()
        self.max = {"driver_mb": 0.0, "current_mb": 0.0, "phys_mb": 0.0, "swap_growth_mb": 0.0, "pressure": 1}
        self.pressure_warn_samples, self.samples, self.series = 0, 0, []

    def run(self):
        import torch
        last = 0.0
        while not self.halt:
            r = rusage()
            d, c = (torch.mps.driver_allocated_memory() / 2**20, torch.mps.current_allocated_memory() / 2**20) if self.use_mps else (0.0, 0.0)
            lv, sw = pressure_level(), swap_used_mb() - self.swap0
            m = self.max
            m["driver_mb"], m["current_mb"] = max(m["driver_mb"], d), max(m["current_mb"], c)
            m["phys_mb"], m["swap_growth_mb"], m["pressure"] = max(m["phys_mb"], r["phys_footprint_mb"]), max(m["swap_growth_mb"], sw), max(m["pressure"], lv)
            self.samples += 1
            self.pressure_warn_samples += lv >= 2
            now = time.time()
            if now - last > 30:
                self.series.append([round(now), round(r["phys_footprint_mb"]), round(d), round(sw), lv])
                last = now
            if r["lifetime_max_phys_footprint_mb"] > MEM_LIMIT_MB:
                self.fault = f"process footprint {r['lifetime_max_phys_footprint_mb']:.0f} MB above limit"
            elif sw > SWAP_GROWTH_LIMIT_MB:
                self.fault = f"swap growth {sw:.0f} MB above limit"
            elif lv >= 4:
                self.fault = "macOS memory pressure critical"
            time.sleep(self.dt)


def simulate_data_stream(seed: int, steps: int = 2000, batch: int = 8) -> str:
    """Pure replay of TargetSegDataset's random-number use, for tile sizes only;
    no pixels are read. Returns the hash of the generator state after training."""
    sizes = {e["file"]: e["shape"][:2] for e in json.load(open(ROOT / "artifacts" / "dataset_integrity_raw.json"))["vaihingen"]}
    r = random.Random(seed)
    for _ in range(steps * batch):
        fn = r.choice(TRAIN)
        h, w = sizes[fn]
        r.randrange(0, h - 223)
        r.randrange(0, w - 223)
        r.random()
        r.random()
        r.randrange(4)
    return hashlib.sha256(repr(r.getstate()).encode()).hexdigest()


def rng_state_hash(r) -> str:
    return hashlib.sha256(repr(r.getstate()).encode()).hexdigest()
