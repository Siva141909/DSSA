# Phase 3: risk register

Scoring: L = likelihood, I = impact, each high (H), medium (M) or low (L).

| # | Risk | Type | L | I | Mitigation | Stop / trigger condition |
|---|---|---|---|---|---|---|
| R1 | No label-free selector beats the depth prior (likely, given Phase 2D) | Scientific | H | M | Path 2 is primary: the null result is a planned outcome, not a failure. Pre-register the screening rule | None. Report it as the finding |
| R2 | The depth prior itself fails to transfer (the utility curve is setting-specific) | Scientific | M | M | It is itself a publishable result (hypothesis F). Stage C reports it | If the prior's ρ < 0.3 in the new setting, skip arm 6 in Stage D and reconsider the scope |
| R3 | Decoder confound: the L23-only decoder shapes the utility curve | Scientific | M | H | State it as a scope limit. Optional ablation: a multi-level decoder on 3 blocks × 3 seeds | Do not generalise beyond the L23 decoder without the ablation |
| R4 | Pretraining-scale mismatch (30 m HLS vs 5–9 cm) limits generality | Scientific | H | M | Scope statement. LoveDA (0.3 m) is still far from 30 m, so no setting near the pretraining scale exists here | Do not claim GFM-general behaviour |
| R5 | Single-block utility does not predict joint utility | Scientific | M | H | Stage D K = 3 tests this directly | If joint arms disagree with single-block rankings, report hypothesis E and drop selector-practicality claims |
| R6 | Under-powered contrasts (σ_c ≈ 0.0099 vs δ = 0.010) | Statistical | H | H | 10 seeds for confirmatory contrasts; larger validation and test tile sets; Holm correction | Never add seeds post hoc without a new manifest |
| R7 | Metric fishing (many signals × many endpoints) | Statistical | M | H | At most 3 label-free candidates + 2 label-using references; primary endpoints fixed in the protocol; all results reported | Any endpoint added after seeing data is labelled exploratory |
| R8 | Reusing the Phase 2D validation tiles as "validation" | Leakage | M | H | Phase 2D data is development-only (protocol §2) | Any claim must rest on the new setting and the tests |
| R9 | Potsdam labels opened before the split is frozen | Leakage | M | H | Split rule and manifest hashed before any label read; the script checks the manifest hash | If violated, the Potsdam setting becomes development-only |
| R10 | Locked tests opened early or repeatedly | Leakage | L | H | One opening, pre-registered configurations, hashed evaluation script | Reported if it happens; no re-tuning |
| R11 | Radiometric transform fitted on Potsdam images while Potsdam is the target | Leakage (mild) | M | L | Unsupervised use only; decide refit vs reuse in Stage A and pre-register | — |
| R12 | Potsdam 6000² tiles exceed evaluation memory or time | Compute | M | M | Stage A memory test; sliding-window evaluation at step 2,000 only; keep the 11.5 GB footprint limit | Stage A failure means changing the tiling before any run |
| R13 | Long unattended runs on a laptop: sleep, charger and lid incidents (INCIDENT_001–010) | Compute and operations | H | M | Existing guards, watchdogs and recovery manifests; keep the charger connected; lid open | Existing stop rules |
| R14 | Total compute (≈ 105–185 h) exceeds the project timeline | Compute | M | H | The fallback paper needs A–C only (≈ 50–60 h) | Decide at the end of Stage C |
| R15 | Full fine-tuning infeasible on this hardware | Compute | H | L | Report as infeasible; do not imply efficiency without the measurement | — |
| R16 | Novelty overlap: CrossEarth-Gate (same pair, Fisher selection), SPECTRA (Prithvi, LogME pre-training allocation), DDC, Act-LoRA, LS-LoRA | Novelty | H | H | Claim only C1 and C3 from the literature audit; cite and compare; include LogME and Fisher as baselines | If a 2026 paper already reports a depth-controlled selector evaluation on GFMs, re-scope to the replication and the RS-specific evidence |
| R17 | The literature audit is partly snippet-based ([S] items) | Novelty | M | M | Full-text reading of the must-read list before writing | Do not cite [S] or [U] details as fact |
| R18 | LoveDA licence (CC BY-NC-SA; Google Earth terms) and RGB-only band mapping | Dataset | M | M | Academic use only; document the band mapping; no NIR | If licence acceptance or the mapping is unclear, drop LoveDA and narrow the claims |
| R19 | ISPRS terms (research use only; no distribution; the DGPF citation is required) | Dataset | L | M | Attribution in any paper; no data redistribution; figures follow the guide-approved practice | — |
| R20 | Reviewers see "negative result" as a low contribution | Publication | M | M | Frame as selector *evaluation methodology* with replication and label-free vs label-using comparison; target venues that value rigorous evaluation | — |
| R21 | Selector-implementation bugs (B = 0 at LoRA init makes ∂L/∂A = 0; misuse of the K0 checkpoint) | Technical | M | M | Unit-test each signal on synthetic inputs; the Fisher definition uses B gradients with a fixed K0 decoder | — |
