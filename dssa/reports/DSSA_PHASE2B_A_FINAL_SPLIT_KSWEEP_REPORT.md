# DSSA Phase 2B-A — Final Split + DSS K-Sweep Report

**No LoRA trained. No segmentation trained. No optimizer instantiated. No gradients computed beyond the frozen, `torch.no_grad()` forward pass. No frozen DSS methodology modified. No final K selected. No method ranked. No segmentation result predicted.**

This is the final, consolidated version of this report — it supersedes the two earlier in-progress versions produced during this phase (a first attempt that stopped at two missing specifications, and a second that stopped at a third). Those stop conditions and their resolutions are recorded below (§2–3) as the actual history of how this phase's inputs were determined, not smoothed over.

Status vocabulary used throughout: **VERIFIED** / **UNSPECIFIED — REQUIRES DECISION** / **BLOCKER** / **NOT APPLICABLE**.

---

## 1. Scope

Lock a formal, file-level Vaihingen split; compute the real (not exploratory) DSS using only the locked target-probe; execute the authorized Top-K sweep {2,4,6,8,12}; determine, without interpretation, whether DSSA-selected layers match the fixed Early/Middle/Late controls at each K; audit and report. All of this was completed in this final pass. No training of any kind occurred.

## 2. Explicit New Experimental Decisions

None of the following existed in any frozen document before this phase. Each was supplied explicitly, by the team, during this phase:

1. **K-sweep grid: `{2, 4, 6, 8, 12}`.** The original freeze required a Top-K sweep but specified no values.
2. **Outer Vaihingen split: lexicographic filename order, partitioned 20/5/8** (target-train/target-validation/target-test). The original freeze fixed the 60/15/25 *ratios* and the probe-from-train relationship, but no ordering rule, seed, or exact integer counts.
3. **Target-probe count: 5 files**, taken as the first 5 (lexicographic order) of the 20-file target-train partition. The original freeze specified only "roughly 10–20% of the total target pool" (33 files) — 10% of 33 = 3.3, 20% of 33 = 6.6, a range, not a unique integer. Five files ≈ 15.15% of the 33-file total pool, near the midpoint of the stated range — this specific number was chosen by the team, not derived uniquely from the freeze.

**None of these three numbers should be read back into the original frozen specification.** They are recorded here as this phase's own decisions.

## 3. Original Freeze vs. New Decisions

| Item | Original freeze | This phase's new decision |
|---|---|---|
| Split ratios (60/15/25) | VERIFIED, frozen (§O-I) | Reused unchanged |
| Probe-carved-from-train relationship | VERIFIED, frozen (§O-I) | Reused unchanged |
| Probe sizing "roughly 10–20% of total pool" | VERIFIED, frozen (§O-I) | Interpreted (not uniquely resolved by the freeze) as the integer 5 |
| Split ordering rule | Not specified | New: lexicographic filename order |
| Split seed | Not specified | New: none used (positional after lexicographic sort, no shuffle) |
| Exact train/val/test counts | Not specified | New: 20/5/8 |
| Top-K grid | Not specified (only "a sweep" required) | New: {2,4,6,8,12} |
| DSS definition itself (pooling, centroid, cosine, bootstrap null, tie-break) | VERIFIED, frozen | **Unchanged in every respect** |

## 4. Final Outer Split

All 33 staged Vaihingen files, sorted lexicographically (Python default string sort on filename — e.g. `area1 < area10 < area11 < ... < area17 < area2 < area20 < ...`, confirmed not to be numeric order). Partitioned positionally, no shuffle, no seed:

- **target-train** = first 20 (indices 0–19)
- **target-validation** = next 5 (indices 20–24)
- **target-test** = final 8 (indices 25–32)

## 5. Target-Probe Decision

**target-probe = first 5 files of target-train** (lexicographic order), per the team's explicit instruction. Rationale recorded verbatim, as required: *"The target-probe count of 5 is a new Phase 2B experimental-design decision. The original freeze specified only roughly 10–20% of the total target pool and did not uniquely determine an integer."*

## 6. Complete File-Level Split Manifest

Written to `dssa/artifacts/splits/vaihingen_target_split_manifest.json` (immutable once created, per instruction — not modified after this phase).

**target-train (20):** `area1, area10, area11, area12, area13, area14, area15, area16, area17, area2, area20, area21, area22, area23, area24, area26, area27, area28, area29, area3` *(all `top_mosaic_09cm_<name>.tif`)*

**target-probe (5, ⊆ target-train):** `area1, area10, area11, area12, area13`

**target-validation (5):** `area30, area31, area32, area33, area34`

**target-test (8):** `area35, area37, area38, area4, area5, area6, area7, area8`

## 7. Split Integrity

Verified programmatically (`dssa/artifacts/splits/vaihingen_target_split_manifest.json` cross-checked against the 33 files actually staged in `dssa/data/vaihingen_irrg/`):

| Check | Result |
|---|---|
| Total staged files | 33 |
| target-train ∪ target-validation ∪ target-test = all 33 staged files | **True** |
| No duplicate across train/val/test | **True** |
| target-probe ⊆ target-train | **True** |
| target-probe ∩ target-validation = ∅ | **True** |
| target-probe ∩ target-test = ∅ | **True** |
| target-validation ∩ target-test = ∅ | **True** |
| target-train ∩ target-validation = ∅ | **True** |
| target-train ∩ target-test = ∅ | **True** |
| Counts | train=20, probe=5, validation=5, test=8 |
| Labels accessed during split creation | **No** — split built from filenames only, no `.tif` pixel data or label files opened |

## 8. Final DSS Methodology

Reused, unmodified, from `dssa/sanity/run_phase2a_dss.py` (imported, not reimplemented, in the new `run_phase2b_final_dss.py`):

- **Source:** Potsdam files[0:16] — the same 16 files used as "source" in Phase 2A Probe A.
- **Null pool:** Potsdam files[16:32] — the same 16 files used as Probe A's null pool.
- **Target:** the 5 **locked target-probe** files, and *only* those — target-validation and target-test are never opened by this script (confirmed by code inspection, §17).
- Checkpoint, revision, Strategy C coefficients, band mapping, T=1, crop mechanism, mean-pooled patch tokens (cls excluded), source centroid, cosine primary metric, 40-resample bootstrap (seed 1234), normalized-DSS formula, deterministic tie-break: **all identical to Phase 1B/2A, none modified.**

37 real forward passes (16 source + 16 null + 5 target-probe).

## 9. Complete 24-Layer DSS Table

| Layer | Raw DSS | Null mean | Null std | Normalized DSS |
|---|---|---|---|---|
| 0 | 0.15189 | 0.20237 | 0.04067 | −1.2414 |
| 1 | 0.12223 | 0.14436 | 0.03001 | −0.7372 |
| 2 | 0.11332 | 0.14116 | 0.02865 | −0.9717 |
| 3 | 0.10430 | 0.13754 | 0.02800 | −1.1873 |
| 4 | 0.10434 | 0.13582 | 0.02696 | −1.1679 |
| 5 | 0.09864 | 0.12451 | 0.02438 | −1.0611 |
| 6 | 0.10243 | 0.11916 | 0.02296 | −0.7286 |
| 7 | 0.10925 | 0.12230 | 0.02237 | −0.5833 |
| 8 | 0.11829 | 0.12944 | 0.02393 | −0.4661 |
| 9 | 0.12904 | 0.13800 | 0.02544 | −0.3521 |
| 10 | 0.13356 | 0.13447 | 0.02463 | −0.0370 |
| 11 | 0.13183 | 0.13417 | 0.02453 | −0.0956 |
| 12 | 0.13814 | 0.14775 | 0.02692 | −0.3568 |
| 13 | 0.14044 | 0.14600 | 0.02626 | −0.2117 |
| 14 | 0.14350 | 0.14813 | 0.02671 | −0.1732 |
| 15 | 0.13679 | 0.13881 | 0.02540 | −0.0796 |
| 16 | 0.13254 | 0.12947 | 0.02371 | +0.1295 |
| 17 | 0.13211 | 0.12527 | 0.02302 | +0.2974 |
| 18 | 0.12589 | 0.11787 | 0.02156 | +0.3719 |
| 19 | 0.12584 | 0.11657 | 0.02094 | +0.4429 |
| 20 | 0.12255 | 0.11516 | 0.02046 | +0.3609 |
| 21 | 0.11326 | 0.10766 | 0.01916 | +0.2920 |
| 22 | 0.09953 | 0.09236 | 0.01664 | +0.4309 |
| 23 | 0.09183 | 0.08477 | 0.01590 | +0.4437 |

**Ranking (most-to-least sensitive):** `[23, 19, 22, 18, 20, 17, 21, 16, 10, 15, 11, 14, 13, 9, 12, 8, 7, 6, 1, 2, 5, 4, 3, 0]`

**Observation, not interpreted:** normalized DSS is negative for layers 0–15 and positive only for layers 16–23, with magnitudes (max ≈ +0.44) substantially smaller than Phase 2A's Probe A (max ≈ +3.76, on 16 target files vs. this run's 5). This is consistent with a smaller target-probe sample producing a noisier, lower-magnitude raw-DSS-vs-null gap — a plausible sample-size effect, not evidence about DSSA's validity, and not investigated further here (no methodology change was made in response to it).

## 10. Source-vs-Source Null

Null mean/std per layer shown in §9 — computed via the same 40-resample bootstrap (seed 1234) over the same 16-file Potsdam null pool as Phase 2A, unchanged. The same depth-dependent shrinkage pattern observed in Phase 2A recurs here (null_std falls from 0.041 at L0 to 0.016 at L23) — expected, since the null computation uses the identical null pool and is independent of which target files are used.

## 11. K={2,4,6,8,12} Sweep

| K | DSSA layers | Early | Middle | Late | Jaccard(DSSA,Early) | Jaccard(DSSA,Middle) | Jaccard(DSSA,Late) | DSSA==Early | DSSA==Middle | DSSA==Late |
|---|---|---|---|---|---|---|---|---|---|---|
| 2 | [19, 23] | [0,1] | [11,12] | [22,23] | 0.000 | 0.000 | 0.333 | False | False | False |
| 4 | [18,19,22,23] | [0,1,2,3] | [10,11,12,13] | [20,21,22,23] | 0.000 | 0.000 | 0.333 | False | False | False |
| 6 | [17,18,19,20,22,23] | [0,1,2,3,4,5] | [9,10,11,12,13,14] | [18,19,20,21,22,23] | 0.000 | 0.000 | 0.714 | False | False | **False** |
| 8 | [16,17,18,19,20,21,22,23] | [0..7] | [8..15] | [16..23] | 0.000 | 0.000 | 1.000 | False | False | **True** |
| 12 | [10,11,14,15,16,17,18,19,20,21,22,23] | [0..11] | [6..17] | [12..23] | 0.091 | 0.333 | 0.714 | False | False | False |

**No condition is interpreted as better than another here. This is a selection-identifiability table only.**

## 12. DSSA vs Early/Middle/Late Overlap

At **every** K tested, DSSA shares **zero** layers with Early, and zero-to-modest overlap with Middle (rising to Jaccard 0.333 only at K=12). DSSA's overlap with Late is substantial at every K (0.333–1.000) and is exact identity at K=8. This pattern — essentially no early-layer overlap, growing late-layer overlap — is consistent, qualitatively, with what Phase 2A observed on its exploratory probes, though the *exact* K at which DSSA becomes identical to Late has changed (Phase 2A: exact identity at K=6; this run: exact identity at K=8, not K=6).

## 13. K=6 DSSA-vs-Late Result — Stated Plainly

```
DSSA@K=6:  [17, 18, 19, 20, 22, 23]
Late@K=6:  [18, 19, 20, 21, 22, 23]

DSSA@K=6 == Late@K=6 ?  FALSE
```

**This differs from Phase 2A's finding, where the two were exactly identical at K=6.** On the real, formally locked target-probe (5 files), the two sets share 5 of 6 layers (Jaccard = 0.714) but are **not** identical — DSSA includes layer 17 and excludes layer 21; Late does the reverse. **This was not assumed in either direction before running, and the actual, changed result is reported exactly as computed.** No claim is made about which of Phase 2A's or this run's result is "more correct" — they used different target samples (Phase 2A: 16 ad hoc files; this run: the formally locked 5-file probe) under the same unmodified methodology, and produced a genuinely different fine-grained answer at this specific K. The exact identity recurs, unprompted, at **K=8** in this run.

## 14. Random-K / Lowest-DSS Status

**No new values were introduced.** Both remain exactly what they were in Phase 2A and the Phase 2B pre-flight audit: **frozen baselines reserved for a future training run** (`DSSA_PROJECT_FREEZE.md` §Q), not something this phase computes fresh. No governing document requires their recomputation at this stage, and none was performed.

## 15. MMD Status

**No new MMD computation was performed in this phase.** No governing document requires MMD to be recomputed against the final-split target-probe. The Phase 2A MMD result (Top-6 = `[5,4,11,6,19,3]` on Probe A, rank correlation with cosine ≈ −0.146) is retained as historical comparison only, unmodified, and was not re-invoked anywhere in this phase's code.

## 16. Repeatability

The Phase 2A Probe-A pipeline's bit-exact repeatability (raw DSS max diff = 0.0, normalized DSS max diff = 0.0, ranking identical) was already established in the prior continuation of this phase and is unchanged — not rerun here, per instruction, since it does not test the new final-split computation. **A separate final-split repeatability check was not performed in this pass** (not requested as mandatory — the instruction made it conditional: "If you perform a final-split repeatability check, report it separately"). This is recorded as **NOT APPLICABLE / not performed**, not as a gap — running the exact same 37-forward-pass computation twice was judged not necessary to answer this phase's questions, given the underlying pipeline's determinism was already established on the same hardware/code path in §16 of the prior pass.

## 17. Leakage Audit

Code-searched directly in `dssa/sanity/run_phase2b_final_dss.py` (new this phase) and its imported dependency `run_phase2a_dss.py` (unchanged):

- The only appearances of `target_validation` / `target_test` in the new script are **log lines that print those filenames explicitly to confirm they are *not* used** (`LOG(f"[split] target-validation NOT referenced: ...")`) — neither list is ever passed into any forward pass, pooling, or DSS computation.
- No label file path (`*_label.tif`, `gts_for_participants`, `ground_truth`) appears anywhere.
- No `optim`, no `.backward()`, no learning-rate scheduler.
- Every forward pass runs under `torch.no_grad()` (inherited from `forward_pooled()` in `run_phase2a_dss.py`, unchanged).
- No LoRA code, no segmentation-training code, exists anywhere in `dssa/sanity/`.

**Leakage audit: clean.** No violation found.

## 18. Artifacts

| Artifact | Status |
|---|---|
| `dssa/artifacts/splits/vaihingen_target_split_manifest.json` | **Created**, immutable |
| `dssa/artifacts/dss/phase2b_final_dss_results.json` | **Created** — full 24-layer table, K-sweep, K=6 result |
| `dssa/artifacts/dss/phase2b_final_dss_run.log` | **Created** — full execution log |
| `dssa/sanity/run_phase2b_final_dss.py` | **Created** |
| `dssa/artifacts/dss/phase2a_dss_results.json`, `phase2a_run.log` | **Unmodified** (Phase 2A artifacts, not overwritten) |
| `dssa/artifacts/dss/phase2b_a_repeatability_check.json` | **Unmodified** (prior pass of this phase) |

## 19. Deviations from Frozen Methodology

**None.** The DSS definition, Strategy C coefficients, band mapping, checkpoint/revision, T value, pooling, centroid construction, bootstrap procedure, and tie-break rule are byte-for-byte the same code path used in Phase 1B/2A. The only things that changed between Phase 2A and this run were **inputs** the frozen methodology always treated as configurable (which target files constitute the "target" role) — not the methodology itself.

## 20. Remaining Decisions Before Training

Unchanged from `DSSA_PHASE2B_PREFLIGHT_REPORT.md` §13 — this phase resolved the split/K-grid/probe-count gaps specifically but did not touch: training protocol (optimizer, LR, epochs, batch size, loss, etc.), decoder architecture, LoRA A/B initialization convention, whether MMD becomes a full training condition, and the design decision on how to handle a DSSA-vs-Late collision when one occurs (now confirmed to occur at K=8 in this run, though not at K=6). All remain **UNSPECIFIED — REQUIRES DECISION**.

## 21. Final Status

**UNSPECIFIED — REQUIRES DECISION**, overall — the specific blockers this phase was scoped to resolve (K grid, split methodology, target-probe count) are now resolved, and the requested final DSS + K-sweep computation is complete. **No BLOCKER** was found anywhere — nothing conflicts with the frozen methodology. What remains unspecified is unchanged from the Phase 2B pre-flight audit's list (§20 above) and was out of scope for this phase.

**Stopping here, per instruction. No LoRA, no decoder implementation, no optimizer, no segmentation training, no evaluation, and no target-test label access occurred or is authorized by this result. Waiting for separate authorization for the next phase.**
