"""DSSA Phase 3 shared safety layer (decision D20: a new code directory; dssa/phase2d is
read-only and is only imported, never modified).

Permitted write locations:
  dssa/phase3/            code
  dssa/artifacts/phase3/  all generated evidence
Everything else under the project is read-only to Phase 3 code.

Access rules enforced here (approved Stage C conditions, 2026-11-06):
  - Vaihingen test tiles: never opened (Phase 2D rule, unchanged).
  - Vaihingen validation tiles and the Vaihingen label archive: never opened in Phase 3
    (protocol v2 section 2.4: Vaihingen validation and test tiles are never used).
  - Potsdam test tiles (last 10 in sorted order): never opened, images or labels.
  - Potsdam label archives: no open at all until the split manifest is frozen and hashed.
  - Potsdam labels: decoded only through potsdam_label(), which checks a per-process
    allow-list (training tiles, or validation tiles in evaluation processes only).
"""
from __future__ import annotations

import ctypes
import hashlib
import io
import json
import os
import sys
import threading
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT.parent
CODE = ROOT / "phase3"
ART = ROOT / "artifacts" / "phase3"
RUNS = ART / "runs"
LOGS = ART / "logs"
SPLIT_FILE = ART / "split" / "potsdam_split_manifest.json"
SPLIT_HASH_FILE = ART / "split" / "potsdam_split_manifest.sha256"
TRANSFORM_FILE = ART / "stage_a" / "radiometric_transform_vaihingen_train.json"
MANIFEST_V1 = ART / "manifest_stage_c.json"   # K0 x 3 ran under v1 (original evaluator)
MANIFEST_V2 = ART / "manifest_stage_c_v2.json"  # v2: lower-memory evaluator (p3eval), verified identical
MANIFEST_V3 = ART / "manifest_stage_c_v3.json"  # v3: canary p3_L00_s1000 interrupted by the swap guard; restart as p3_L00_s1000_r1
MANIFEST_V4 = ART / "manifest_stage_c_v4.json"  # v4: p3_L06_s2000 interrupted by the charger guard; restart as p3_L06_s2000_r1, resume
MANIFEST = ART / "manifest_stage_c_v5.json"  # v5: p3_L10_s3000 interrupted by the charger guard; restart as p3_L10_s3000_r1, resume
CANARY = "p3_L00_s1000_r1"
MANIFEST_D_V1 = ART / "manifest_stage_d_v1.json"   # Stage D (scenario S2), approved by the user 2026-11-09
MANIFEST_D_V2 = ART / "manifest_stage_d_v2.json"   # v2: p3d_PRIOR3_s1000 interrupted by the sleep guard (lid closed on battery); restart as p3d_PRIOR3_s1000_r1, resume
MANIFEST_D_V3 = ART / "manifest_stage_d_v3.json"   # v3: p3d_UNIF1_s7000 interrupted by the swap guard (other apps in use); restart as p3d_UNIF1_s7000_r1, resume
MANIFEST_D = ART / "manifest_stage_d_v4.json"   # v4: p3d_RAND3d09_s9000 stopped by the 1.5x runtime guard (GPU contention); restart as p3d_RAND3d09_s9000_r1, runtime limit raised to 2.5x, resume
STAGE_D_BASELINE = ART / "stage_d" / "stage_d_baseline.json"
STAGE_D_BASELINE_HASH = ART / "stage_d" / "stage_d_baseline.sha256"


def manifest_for(run_id: str) -> Path:
    """Stage D run IDs start with p3d_; everything else is a Stage C run."""
    return MANIFEST_D if run_id.startswith("p3d_") else MANIFEST
SCORES_FILE = ART / "stage_b" / "stage_b_scores_frozen.json"
SCORES_HASH_FILE = ART / "stage_b" / "stage_b_scores_frozen.sha256"
ALLOWED_WRITE = (ART, CODE)

POTSDAM_IMG_DIR = ROOT / "data" / "potsdam_irrg"
POTSDAM_LABEL_ZIP = ROOT / "data" / "Potsdam" / "5_Labels_all.zip"
VAIHINGEN_IMG_DIR = ROOT / "data" / "vaihingen_irrg"
P2D_BASELINE = ROOT / "artifacts" / "phase2d" / "gate0" / "baseline_hashes.json"

_VSPLIT = json.load(open(ROOT / "artifacts" / "splits" / "vaihingen_target_split_manifest.json"))["partitions"]
V_TRAIN = list(_VSPLIT["target_train"])
V_FORBIDDEN = frozenset(_VSPLIT["target_test"]) | frozenset(_VSPLIT["target_validation"])

SEEDS = (1000, 2000, 3000)          # Stage C seeds 1-3 (the Phase 2D seeds)
LORA_SEED_OFFSET = 7_000_000        # as Phase 2D: lora_init_seed = seed + offset
MEM_LIMIT_MB = 11.5 * 1024          # existing hard guard (fault, incident.json)
ABORT_MB = 11.0 * 1024              # Phase 3 early-abort sampler (immediate exit)
STOP_RULE_MB = 10.5 * 1024          # sequence stops if any process peak exceeds this
SWAP_GROWTH_LIMIT_MB = 512


def potsdam_tile_id(name: str) -> str:
    """'top_potsdam_2_10_IRRG.tif' -> '2_10'."""
    parts = name.split("_")
    return f"{parts[2]}_{parts[3]}"


def potsdam_image_names() -> list[str]:
    """Directory listing only (no file is opened)."""
    return sorted(p.name for p in POTSDAM_IMG_DIR.glob("top_potsdam_*_IRRG.tif"))


def _split_rule(names: list[str]) -> dict:
    assert len(names) == 38 and names == sorted(names)
    return {"train": names[:20], "probe": names[:5], "validation": names[20:28], "test": names[28:]}


# The test keys are derived from the directory listing by the frozen positional rule, so the
# guard is active before the manifest exists.
_TEST_KEYS = tuple(f"top_potsdam_{potsdam_tile_id(n)}_" for n in _split_rule(potsdam_image_names())["test"])


def split() -> dict:
    """The frozen split; refuses if the manifest is missing or its hash changed."""
    if not SPLIT_FILE.exists():
        raise RuntimeError("Potsdam split manifest not frozen yet")
    if sha256_file(SPLIT_FILE) != SPLIT_HASH_FILE.read_text().split()[0]:
        raise RuntimeError("Potsdam split manifest hash mismatch")
    s = json.load(open(SPLIT_FILE))["partitions"]
    if s != _split_rule(potsdam_image_names()):
        raise RuntimeError("Potsdam split manifest differs from the positional rule")
    return s


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def canon_hash(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()


def config_hash(entry: dict) -> str:
    return canon_hash({k: v for k, v in entry.items() if k not in ("config_hash", "est_seconds")})


def code_hash() -> dict:
    return {p.name: sha256_file(p) for p in sorted(CODE.glob("*")) if p.is_file() and p.suffix in (".py", ".md")}


def check_write_path(path) -> None:
    p = Path(path).resolve()
    if not any(p == a or a in p.parents for a in ALLOWED_WRITE):
        raise PermissionError(f"write outside approved Phase 3 paths: {p}")


def write_json_atomic(path: Path, obj) -> None:
    check_write_path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=1, default=str)
    os.replace(tmp, path)


def install_guards() -> None:
    """Audit hook: hard stops for test access, early label access and stray writes."""
    proj = str(PROJECT)
    allowed = tuple(str(a) for a in ALLOWED_WRITE)
    vlabel = (str(ROOT / "data" / "Vaihingen") + os.sep).lower()
    plabel = (str(ROOT / "data" / "Potsdam") + os.sep).lower()
    zip_real = os.path.realpath(POTSDAM_LABEL_ZIP).lower()

    def hook(event, args):
        if event != "open":
            return
        path, mode, flags = args
        if not isinstance(path, (str, bytes, os.PathLike)):
            return
        s = os.fsdecode(path)
        base = os.path.basename(s)
        if base in V_FORBIDDEN:
            raise PermissionError(f"VAIHINGEN TEST/VALIDATION ACCESS ATTEMPTED: {s}")
        if base.startswith(_TEST_KEYS):
            raise PermissionError(f"POTSDAM TEST ACCESS ATTEMPTED: {s}")
        low = s.lower()
        if low.startswith(vlabel):
            raise PermissionError(f"VAIHINGEN LABEL ARCHIVE ACCESS ATTEMPTED IN PHASE 3: {s}")
        if low.startswith(plabel):
            if os.path.realpath(s).lower() != zip_real:
                raise PermissionError(f"UNAPPROVED POTSDAM ARCHIVE ACCESS: {s}")
            if not (SPLIT_FILE.exists() and SPLIT_HASH_FILE.exists()):
                raise PermissionError(f"POTSDAM LABEL ACCESS BEFORE THE SPLIT IS FROZEN: {s}")
        writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT))
        if writing and s.startswith(proj) and not s.startswith(allowed):
            raise PermissionError(f"write outside approved Phase 3 paths: {s}")

    sys.addaudithook(hook)


# ---------------- Potsdam data access ----------------
LABEL_ALLOW: set = set()       # set per process: tile ids whose labels may be decoded
OPENED: dict = {"images": set(), "labels": set()}


def label_member(tile_id: str) -> str:
    return f"top_potsdam_{tile_id}_label.tif"


def potsdam_image(name: str):
    import tifffile
    tid = potsdam_tile_id(name)
    s = split()
    if name not in s["train"] + s["validation"]:
        raise PermissionError(f"Potsdam image not in train or validation: {name}")
    OPENED["images"].add(tid)
    return tifffile.imread(str(POTSDAM_IMG_DIR / name))


def potsdam_label(name: str):
    """(H, W) uint8 class indices, decoded with the frozen ISPRS colour table (no fallback)."""
    import numpy as np
    import tifffile
    import dataset as ds
    tid = potsdam_tile_id(name)
    s = split()
    if name in s["test"] or tid not in LABEL_ALLOW:
        raise PermissionError(f"Potsdam label not allowed in this process: {name}")
    OPENED["labels"].add(tid)
    with zipfile.ZipFile(POTSDAM_LABEL_ZIP) as z:
        data = z.read(label_member(tid))
    arr = tifffile.imread(io.BytesIO(data))
    if arr.ndim != 3 or arr.shape[-1] != 3 or arr.dtype != np.uint8:
        raise ValueError(f"{name}: unexpected label array {arr.shape} {arr.dtype}")
    try:
        return ds.rgb_to_class_index(arr).astype(np.uint8)
    except ValueError:
        return _snap_label(tid, arr)


SNAP_MAX_DIST, SNAP_MIN_MARGIN = 100.0, 100.0
SNAPPED: dict = {}


def _snap_label(tid: str, arr):
    """Label-decoding amendment approved 2026-11-06 (Potsdam 4_12 is a lossy copy): a tile with
    non-exact colours is snapped by a per-channel threshold at 128, only if every pixel is
    unambiguous: the snapped colour is one of the 6, the nearest ISPRS colour is <= 100 away and
    the second nearest >= 100 further. Otherwise a hard stop. Every snapped tile is recorded."""
    import numpy as np
    import dataset as ds
    cols = np.array([ds.CLASS_COLORS_RGB[n] for n in ds.CLASS_NAMES], np.float32)
    flat = arr.reshape(-1, 3)
    out = np.full(len(flat), 255, np.uint8)
    worst_d, worst_m, n_exact = 0.0, 1e9, 0
    for a in range(0, len(flat), 1_000_000):
        x = flat[a:a + 1_000_000]
        d = np.sqrt(((x[:, None, :].astype(np.float32) - cols[None]) ** 2).sum(-1))
        o = np.sort(d, 1)
        near = d.argmin(1)
        thr = (x >= 128).astype(np.uint8) * 255
        thr_cls = np.full(len(x), 255, np.uint8)
        for i, c in enumerate(cols.astype(np.uint8)):
            thr_cls[np.all(thr == c, -1)] = i
        if (thr_cls == 255).any() or (thr_cls != near).any():
            raise ValueError(f"{tid}: threshold snap invalid or disagrees with nearest colour")
        worst_d, worst_m = max(worst_d, float(o[:, 0].max())), min(worst_m, float((o[:, 1] - o[:, 0]).min()))
        n_exact += int((o[:, 0] == 0).sum())
        out[a:a + len(x)] = thr_cls
    if worst_d > SNAP_MAX_DIST or worst_m < SNAP_MIN_MARGIN:
        raise ValueError(f"{tid}: ambiguous colours (max nearest distance {worst_d:.1f}, min margin {worst_m:.1f})")
    SNAPPED[tid] = {"pixels": len(flat), "exact_pixels": n_exact, "max_nearest_distance": round(worst_d, 2), "min_margin": round(worst_m, 2),
                    "class_counts": np.bincount(out, minlength=6).tolist()}
    return out.reshape(arr.shape[:2])


# ---------------- process monitoring (same quantities as Phase 2D) ----------------
def rusage() -> dict:
    buf = (ctypes.c_uint64 * 48)()
    if ctypes.CDLL("libproc.dylib").proc_pid_rusage(os.getpid(), 4, ctypes.byref(buf)) != 0:
        raise OSError("proc_pid_rusage failed")
    v = list(buf)[2:]
    return {"resident_mb": v[6] / 2**20, "phys_footprint_mb": v[7] / 2**20, "lifetime_max_phys_footprint_mb": v[28] / 2**20}


_libc = ctypes.CDLL("libc.dylib")


def pressure_level() -> int:
    v, n = ctypes.c_int(0), ctypes.c_size_t(4)
    _libc.sysctlbyname(b"kern.memorystatus_vm_pressure_level", ctypes.byref(v), ctypes.byref(n), None, 0)
    return v.value


class XswUsage(ctypes.Structure):
    _fields_ = [("total", ctypes.c_uint64), ("avail", ctypes.c_uint64), ("used", ctypes.c_uint64), ("pagesize", ctypes.c_uint32), ("encrypted", ctypes.c_uint32)]


def swap_used_mb() -> float:
    x, n = XswUsage(), ctypes.c_size_t(ctypes.sizeof(XswUsage))
    _libc.sysctlbyname(b"vm.swapusage", ctypes.byref(x), ctypes.byref(n), None, 0)
    return x.used / 2**20


class Telemetry(threading.Thread):
    """Samples every dt seconds and appends one JSON line per sample (if path is given).
    .fault is set for the existing guards (11.5 GB lifetime footprint, swap growth, critical
    pressure); the owner raises at its next tick and writes incident.json. Above ABORT_MB the
    process writes abort.json and exits immediately (Phase 3 early-abort sampler)."""

    def __init__(self, path: Path | None, state: dict, out_dir: Path, dt: float = 0.25, use_mps: bool = True):
        super().__init__(daemon=True)
        self.dt, self.state, self.out_dir, self.use_mps = dt, state, out_dir, use_mps
        self.f = open(path, "a", buffering=1) if path else None
        self.halt, self.fault, self.tail = False, None, []
        self.swap0 = swap_used_mb()
        self.max = {"driver_mb": 0.0, "current_mb": 0.0, "phys_mb": 0.0, "swap_growth_mb": 0.0, "pressure": 1}
        self.samples, self.pressure_warn_samples = 0, 0

    def run(self):
        import torch
        while not self.halt:
            r = rusage()
            d, c = (torch.mps.driver_allocated_memory() / 2**20, torch.mps.current_allocated_memory() / 2**20) if self.use_mps else (0.0, 0.0)
            lv, used = pressure_level(), swap_used_mb()
            sw = used - self.swap0
            m = self.max
            m["driver_mb"], m["current_mb"] = max(m["driver_mb"], d), max(m["current_mb"], c)
            m["phys_mb"], m["swap_growth_mb"], m["pressure"] = max(m["phys_mb"], r["phys_footprint_mb"]), max(m["swap_growth_mb"], sw), max(m["pressure"], lv)
            self.samples += 1
            self.pressure_warn_samples += lv >= 2
            rec = {"t": round(time.time(), 3), "opt_step": self.state.get("opt_steps", 0), "stage": self.state.get("stage"), "phys_mb": round(r["phys_footprint_mb"], 1),
                   "life_max_mb": round(r["lifetime_max_phys_footprint_mb"], 1), "driver_mb": round(d, 1), "current_mb": round(c, 1),
                   "pressure": lv, "swap_used_mb": round(used, 1), "swap_growth_mb": round(sw, 1)}
            if self.f:
                self.f.write(json.dumps(rec) + "\n")
            self.tail = (self.tail + [rec])[-200:]
            if r["phys_footprint_mb"] > ABORT_MB or r["lifetime_max_phys_footprint_mb"] > ABORT_MB:
                try:
                    write_json_atomic(self.out_dir / "abort.json", {"cause": f"footprint above {ABORT_MB:.0f} MB early-abort limit", "rusage": r, "stage": self.state.get("stage"),
                                                                     "opt_steps": self.state.get("opt_steps"), "time": time.time(), "telemetry_tail": self.tail[-40:]})
                finally:
                    print(f"[ABORT] footprint {r['phys_footprint_mb']:.0f} MB (lifetime max {r['lifetime_max_phys_footprint_mb']:.0f} MB) above {ABORT_MB:.0f} MB", flush=True)
                    os._exit(3)
            if r["lifetime_max_phys_footprint_mb"] > MEM_LIMIT_MB:
                self.fault = f"process footprint {r['lifetime_max_phys_footprint_mb']:.0f} MB above limit"
            elif sw > SWAP_GROWTH_LIMIT_MB:
                self.fault = f"swap growth {sw:.0f} MB above limit"
            elif lv >= 4:
                self.fault = "macOS memory pressure critical"
            time.sleep(self.dt)


def memory_record(mon: Telemetry) -> dict:
    r = rusage()
    return {"kernel_lifetime_max_footprint_mb": r["lifetime_max_phys_footprint_mb"], "sampled_max": mon.max, "samples": mon.samples,
            "pressure_warn_samples": mon.pressure_warn_samples, "swap_at_start_mb": mon.swap0,
            "above_stop_rule": r["lifetime_max_phys_footprint_mb"] > STOP_RULE_MB}


def setup_paths() -> None:
    """Phase 2D and Phase 2C modules are imported read-only; bytecode is never written."""
    sys.dont_write_bytecode = True
    for p in (ROOT / "sanity", ROOT / "train", ROOT / "phase2d"):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
