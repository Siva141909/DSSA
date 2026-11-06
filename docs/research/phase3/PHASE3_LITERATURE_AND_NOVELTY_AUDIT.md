# Phase 3: literature and novelty audit

Date: 2026-11-06. Sources were reached by web search; the arXiv abstract and HTML pages were read where
stated. Labels:
- **[P]** a primary source was read (arXiv abstract or HTML, publisher or proceedings page);
- **[S]** only search or aggregator snippets were available, so verify before citing;
- **[U]** unverified.

No bibliographic detail was invented. Where a field is unknown, it says so.

## 1. Literature matrix

| # | Paper (verification) | Problem / setting | Backbone, data | Supervision for selection | Signal; when | What is selected | Overlap with DSSA | What DSSA can still add |
|---|---|---|---|---|---|---|---|---|
| 1 | **CrossEarth-Gate**: Cao, Gong, Lin, … Fu (13 authors). arXiv 2511.20302 (v1 25 Nov 2025, v3 17 Jun 2026). **[P]**. CVPR 2026 status **[U]**: there is no venue comment on arXiv | Efficient cross-domain RS segmentation (DG and DA) | DINOv2-L + Mask2Former (ablations: SAM, SatMAE, Scale-MAE). 18 benchmarks: CASID (12 DG), RescueNet (2), **P2V and V2P (Potsdam ↔ Vaihingen, incl. IR-R-G)**, R2U and U2R | **Labelled source** (DG); for DA, also target pseudo-labels | Diagonal empirical **Fisher** (squared gradients of the task loss); recomputed **during training** every N iterations, keeping the top-k modules | Module *type* per block (spatial = LoRA on Q/V; semantic = adapter; frequency = Earth-Adapter) | **Same dataset pair**; module/layer selection for PEFT under RS domain shift | A **label-free, pre-training** signal (CrossEarth-Gate uses task gradients during training). A **controlled single-layer oracle** to test whether any signal predicts utility (CrossEarth-Gate does not test selector validity against depth baselines). A GFM (Prithvi) rather than DINOv2 |
| 2 | **SPECTRA**: Li, Caraballo-Vega, Gong, Carroll, Wang. arXiv 2608.01751; "Accepted at ACM SIGSPATIAL 2026 Research track". **[P]** | Cross-sensor fine-tuning of GFMs: band mismatch + PEFT | **Prithvi-EO-2.0 600M**, ScaleMAE, SatMAE; Sen1Floods11, FireScars, Landslide4Sense, SA Crop Type | **Target labels** ("profiling labels" Y) | **LogME** on frozen stage features, **before** fine-tuning; softmax rank allocation; "transfer" or "repair" mode chosen by validation | LoRA **rank per stage** (4 stages) | Pre-training selection on Prithvi. Its "repair" mode gives more capacity to *less* transferable stages, conceptually close to the DSSA premise | Block-level (24) rather than stage-level (4); **label-free** target signal; explicit **depth-baseline** testing (SPECTRA compares to uniform LoRA, Surgical/auto-RGN, LP and full FT, but per the HTML read **not** to depth-only rules) |
| 3 | **GeoSA + BaSA**: Luo, Zan, Ji, Khoshelham. "Domain generalization for semantic segmentation of remote sensing images via vision foundation model fine-tuning", ISPRS J. Photogramm. Remote Sens. 230 (2025) 126–146, DOI 10.1016/j.isprsjprs.2025.09.004. **[S]** | RS domain generalisation | DINOv2; 4 RS datasets, 4 DG scenarios | Labelled source | Architectural adapter (no layer selection) | — | RS cross-domain PEFT context only | Not a selection method; weak overlap |
| 4 | **"Learning From Vision Foundation Models for Cross-Domain Remote Sensing Image Segmentation"**, IEEE TIP 2025, DOI 10.1109/TIP.2025.3588041. **[S]**, metadata only. The "LFMDA" acronym is **[U]** | Cross-domain RS segmentation using VFMs | **[U]** | **[U]** | **[U]** | **[U]** | Context | Must be read in full before citing any detail |
| 5 | **Activation-Guided Layer Selection for LoRA (Act-LoRA)**: Dawadikar, Shyamsundar, Bhat, Saxena. *Information* (MDPI) 17(3):283, 2026, DOI 10.3390/info17030283. **[S]** | Where to insert LoRA (NLP) | Encoder and decoder LMs; GLUE | Label-free (activations) | **Activation magnitude**; before training | Layers for LoRA | Same question (which layers get LoRA), with a label-free signal | DSSA's is **cross-domain discrepancy**, not activation norm. **Caveat:** arXiv 2604.17573 **[S]** reports random selection statistically indistinguishable from activation-guided selection in its setting |
| 6 | **Training-free layer selection for PEFT of LMs**: LREC 2026, ACL Anthology 2026.lrec-1.810. Authors listed on the Anthology include A. K. Biswas and A. K. M. M. Rahman. **[S]**; a journal version reported in *Information Sciences* (DOI 10.1016/j.ins.2026.123204) **[U]** | Partial fine-tuning (NLP) | LMs; 15 NLP datasets | Label-free | **Inter-layer cosine similarity** of aggregate token representations; a single forward pass | Layers to fine-tune | Training-free representation signal | Domain-shift setting; vision/RS; depth control |
| 7 | **Where to Adapt Matters: Layer-Selective Fine-Tuning for Capability Retention**: Pang, Sun, Xie, Shu, Meng, Xu. arXiv 2610.11620 (8 Oct 2026). **[S]** | Which layers to LoRA-tune, balancing gain and forgetting (LLMs) | LLMs; math, code, commonsense | Label-free | **Low input-output similarity** of a layer (LS-LoRA) | Layers for LoRA | Directly covers "input-output cosine" as a selector | So candidate signal 5 (input-output similarity) is **not novel** |
| 8 | **Deep Domain Confusion**: Tzeng, Hoffman, Zhang, Saenko, Darrell. arXiv 1412.3474 (2014). **[P]** (abstract) | UDA (classification) | AlexNet; Office | Labelled source, unlabelled target | **MMD** source-target discrepancy used to choose the adaptation layer's **position and width** | Where to place the adaptation layer | **Layer-wise source-target discrepancy for placement already exists** | Rules out any "first to use layer-wise discrepancy" claim |
| 9 | **Surgical Fine-Tuning Improves Adaptation to Distribution Shifts**: Lee et al. ICLR 2023, arXiv 2210.11466. **[P]** (abstract) | Which contiguous block to fine-tune under shift | ResNets/ViTs; 7 shifts | Target labels | Shift-type analysis plus automatic criteria (Auto-RGN, a relative gradient norm, is named by SPECTRA as the surgical baseline) | Contiguous layer subset | **Best layers depend on shift type**: input-level shifts favour early layers, feature-level shifts later layers | DSSA can test this in RS with a GFM; Auto-RGN is a necessary label-using baseline |
| 10 | **GALA (Gradient-Aligned Layer Adaptation)**: Sahoo, ElAraby, Ngnawe, Pequignot, Precioso, Gagné. "A Layer Selection Approach to Test Time Adaptation", arXiv 2404.03784; AAAI-25. **[S]** (venue year inconsistent across sources) | Test-time adaptation | DomainBed; various backbones | Unlabelled test stream (TTA loss) | Gradient alignment; online | Layers to update per sample | Layer selection under shift | Different regime (TTA, online) |
| 11 | **LogME**: You, Liu, Wang, Long. ICML 2021, PMLR 139:12133–12143, arXiv 2102.11005. **[P]** | Transferability estimation | Many | Target labels | Evidence of labels given frozen features | Models (used per stage by SPECTRA) | Basis for a label-using per-block baseline | — |
| 12 | **AdaLoRA**: Zhang et al. ICLR 2023, arXiv 2303.10512. **[P]** (abstract) | Rank allocation | NLP | Task gradients during training | Sensitivity-based importance; SVD pruning | Rank per matrix | Adaptive allocation baseline | — |
| 13 | **Prithvi-EO-2.0**: Szwarcman et al. arXiv 2412.02732 (v3 Mar 2026). **[P]** (abstract) | GFM | 4.2M HLS 30 m time series; evaluated at 0.1–15 m | — | — | — | Our backbone | Confirms the pretraining-scale mismatch (D6) |
| 14 | **Fine-tune Smarter, Not Harder (PEFT for GFMs)**: Marti-Escofet et al., arXiv 2504.17397. **[S]** | PEFT benchmark on GFMs | Prithvi-EO-2.0, Clay | Target labels | — | Uniform PEFT (LoRA r16, VPT, adapters) | LoRA ≈ full FT on GFMs; **the decoder choice (UNet) mattered most** | Supports D5: decoder design can dominate; DSSA must control it |
| 15 | **PANGAEA benchmark**: Marsocci et al. arXiv 2412.04204. **[P]** (abstract) | GFM evaluation | Many datasets | — | — | — | GFMs do not consistently beat supervised UNets | Context for claims about GFM benefit |
| 16 | **LoveDA**: Wang, Zheng, Ma, Lu, Zhong. NeurIPS 2021 Datasets & Benchmarks, arXiv 2110.08733; licence **CC BY-NC-SA 4.0**, academic use only (Zenodo record). **[P]** | Urban ↔ rural domain-adaptive segmentation | 5,987 HSR images (0.3 m, RGB), 7 classes, three cities | — | — | — | Candidate independent setting; also used by CrossEarth-Gate (R2U/U2R) | — |

**Searched without a direct hit:** "source-target representation shift predicts which ViT/GFM layers to
fine-tune". No paper found does exactly this with a depth-controlled oracle. This is weak evidence of a
gap, not proof. A related 2026 NeurIPS submission ("Does the Deep-Layer Alignment Collapse Predict
Anything?") **[S]** reports that CKA representation gaps barely predicted fine-tuning behaviour
(ρ ≈ −0.20), which is consistent with our negative result.

## 2. Candid novelty assessment

### Rejected novelty claims (must not be made)
1. **"First to use layer-wise domain discrepancy to decide where to adapt."** False: Deep Domain
   Confusion (2014) used MMD to place the adaptation layer.
2. **"First layer selection for PEFT in remote sensing."** False: CrossEarth-Gate selects modules per
   layer (Fisher), and SPECTRA allocates LoRA rank per stage on Prithvi.
3. **"First training-free / label-free layer selection for LoRA."** False: Act-LoRA (activations), the
   LREC 2026 inter-layer-cosine work, and LS-LoRA (input-output similarity) all exist, albeit in NLP.
4. **"Potsdam → Vaihingen is a new benchmark for this question."** False: CrossEarth-Gate already
   reports P2V and V2P.
5. **"Middle layers are best" as a discovery.** Unsafe: layer-dependence of fine-tuning benefit is well
   documented (Surgical FT; LS-LoRA). Ours is one setting, with a decoder confound.
6. **"Selective LoRA is more efficient."** Not established: no uniform-LoRA, full-FT, time, memory or
   latency comparison exists yet.

### What could still be a contribution (hypotheses, to be earned by Phase 3)
- **C1. A depth-controlled test of label-free selectors.** None of the methods read here tests whether
  its selection signal beats **depth-only rules**:
  - CrossEarth-Gate and SPECTRA compare against uniform PEFT and other methods.
  - Act-LoRA's random-parity caveat suggests the problem is real.
  - Phase 2D shows a DSS signal with ρ = 0.94 to depth and partial ρ = 0.076.

  A rigorous, pre-registered demonstration that depth explains most "layer-importance" signals for a
  GFM under RS domain shift, replicated in an independent setting, is a defensible empirical
  contribution. **Novelty risk: moderate.** Partly anticipated by Surgical FT and the random-parity
  report.
- **C2. A label-free selector that beats a non-linear depth prior** in at least two independent
  settings. This would be a method contribution. **Prior probability: low**, given Phase 2D.
- **C3. Label-free vs cheap label-using signals.** Compare discrepancy (label-free) with LogME (SPECTRA's
  signal), Fisher and Auto-RGN (label-using) against the same oracle. This quantifies whether labels are
  needed to choose where to adapt. **Useful and under-reported**, especially for GFMs.

Overall: **the method-novelty space for "a new discrepancy score" is narrow and crowded. The
evaluation-methodology space (depth-controlled, oracle-validated, cross-setting) is less crowded and
better matches the evidence we already have.**

## 3. Must-read before any submission (not completed here)
- The full texts of CrossEarth-Gate (appendix: k and N; whether DA Fisher uses target pseudo-labels),
  the IEEE TIP 2025 paper (#4), Act-LoRA and its random-parity critique (2604.17573), LS-LoRA (2610.11620)
  and Surgical FT (Auto-RGN definition).
- Works on intermediate-layer transfer in ViTs and MAEs (to position the middle-block observation), and
  on CKA and representation-similarity limits.

Sources (pages accessed): arxiv.org/abs/2511.20302 and /html/2511.20302; arxiv.org/abs/2608.01751 and
/html/2608.01751; arxiv.org/abs/1412.3474; arxiv.org/abs/2210.11466; arxiv.org/abs/2404.03784;
arxiv.org/abs/2102.11005; arxiv.org/abs/2303.10512; arxiv.org/abs/2412.02732; arxiv.org/abs/2412.04204;
arxiv.org/abs/2110.08733 and zenodo.org/records/5706578; mdpi.com/2078-2489/17/3/283;
aclanthology.org/2026.lrec-1.810; papers.cool/arxiv/2610.11620; arxiv.org/pdf/2604.17573;
api.openalex.org (DOI 10.1109/TIP.2025.3588041); search.napstic.cn (GeoSA, ISPRS JPRS 230);
arxiv.org/pdf/2504.17397; neurips.cc/virtual/2026/179983.
