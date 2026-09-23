# PRESENTATION_SCRIPT.md
### DSSA — Team Teaching Document & Presentation Guide

This document has two jobs:
1. Teach the whole DSSA project to a teammate who knows nothing about it — starting from zero.
2. Tell the team exactly what to say for each of the 4 slides in `DSSA_HOD_Presentation.pptx`.

Everything here is based on our own project abstract (`DSSA_Final_Project_Abstract.pdf`) and the two papers we studied — SPECTRA and CrossEarth-Gate. Where something is still a **proposal** (not yet tested), this document says so clearly. Nothing here should be read as a proven result.

---

## Table of Contents

- [Section A — DSSA: Project Explained from Zero](#section-a)
- [Section B — DSSA in One Simple Story](#section-b)
- [Section C — Paper 1: SPECTRA](#section-c1)
- [Section C — Paper 2: CrossEarth-Gate](#section-c2)
- [Section D — SPECTRA vs CrossEarth-Gate vs DSSA](#section-d)
- [Section E — What is Missing? (Our Research Gap)](#section-e)
- [Section F — DSSA Methodology, Step by Step](#section-f)
- [Section G — What is Actually Experimental](#section-g)
- [Section H — How to Explain the PPT (Slide by Slide)](#section-h)
- [Section I — Image Cheat Sheet](#section-i)
- [Section J — HOD Q&A (25 Questions)](#section-j)
- [Section K — 30-Second Emergency Explanation](#section-k)
- [Section L — 2-Minute Full Explanation](#section-l)
- [Section M — Terms to Memorize](#section-m)

---

<a name="section-a"></a>
# DSSA — Project Explained from Zero

Read this section top to bottom, in order. Each idea builds on the one before it.

### 1. What is our project?

Our project is called **DSSA** — Domain Sensitivity-guided Selective Parameter-Efficient Adaptation for Cross-Sensor Remote Sensing Semantic Segmentation.

In plain words: we are studying whether an AI model that looks at satellite images and labels every pixel (road, building, water, forest...) can be **taught to work on a new satellite's images cheaply**, by only adjusting the small parts of the model that actually get confused by the new satellite — instead of retraining the whole thing.

### 2. What problem are we trying to solve?

AI models trained on satellite images from one satellite often perform worse when used on images from a **different** satellite, region, or season. Fixing this today usually means either:
- retraining the entire model (expensive, slow), or
- adding small trainable patches everywhere in the model, whether they are needed or not (still wasteful).

We are exploring a smarter middle ground.

### 3. What is a satellite image?

**In simple words:** A photo of the Earth's surface taken by a camera mounted on a satellite orbiting the planet.

**Technical meaning:** Unlike a normal photo, a satellite image often has multiple "bands" — separate grayscale layers capturing different wavelengths of light, including some humans can't see (like infrared).

**In our project:** All our source and target data is satellite imagery, and the bands available can differ between satellites.

### 4. What is a satellite sensor?

**Simple meaning:** The actual camera-like instrument on the satellite that records the image.

**Technical meaning:** Different sensors (e.g., on Sentinel-2, Landsat, or other satellites) have different resolutions, band sets, and calibration — so the same location can produce very different raw pixel values depending on which sensor took the photo.

**Real-life example:** Think of two different phone cameras taking a photo of the same street. One phone might make colors look warmer, another sharper — same street, different-looking photo.

**In our project:** "Cross-sensor" in our project title means we are adapting a model trained on one sensor's images to work on another sensor's images.

### 5. Why can two satellite images of similar places look different?

Because of differences in: sensor type, spatial resolution (how zoomed-in a pixel is), atmospheric conditions (haze, clouds), time of day, season, and geographic region. Two images of farmland — one from summer in India, one from winter in Brazil — can look statistically very different to an AI model, even though both show "farmland."

### 6. What is a domain?

**Simple meaning:** A "domain" is the general condition or setting that a batch of data comes from.

**Technical meaning:** In machine learning, a domain is defined by the statistical distribution of the input data — what the data "typically looks like" in terms of pixel values, resolution, noise, etc.

**In our project:** Our **source domain** is the sensor/dataset we train on; our **target domain** is the sensor/dataset we want the model to work well on afterward.

### 7. What is domain shift?

**Simple meaning:** When the data you test a model on looks statistically different from the data you trained it on.

**Technical meaning:** A mismatch between the source-domain data distribution (used for training) and the target-domain data distribution (used at deployment/testing), even though the task (e.g., segmenting roads and buildings) stays the same.

**In our project:** Domain shift is the central problem DSSA is trying to handle — caused by sensor, region, season, resolution, or atmospheric differences.

### 8. Simple real-life example of domain shift

Imagine you learn to recognize a teacher's handwriting really well. Now someone hands you a page written by a completely different person, in a different pen, on lined paper instead of plain paper. Even though it's still "handwriting," you may misread several words — not because your reading ability disappeared, but because the *style* changed. That style change is domain shift.

### 9. Why domain shift hurts a trained model

A deep learning model doesn't just learn "what a road looks like" in the abstract — it partly learns the specific pixel statistics, colors, and textures of its training data. When those statistics change (new sensor, new season), the model's internal assumptions become slightly wrong, and its predictions get less accurate, even though the real-world objects in the image haven't changed.

### 10. What is semantic segmentation?

**Simple meaning:** Labeling *every single pixel* of an image with what it is, not just saying "there is a road somewhere in this image."

**Technical meaning:** A dense prediction task where the model outputs a class label (e.g., building, road, water, forest, background) for each pixel, producing a full label map the same size as the input image.

**In our project:** Our final output is a segmentation map of the target satellite image — every pixel colored by what land-cover class it belongs to.

### 11. Simple segmentation example

Think of a coloring book. Instead of you coloring it by hand, the AI colors every pixel of the picture automatically: blue for water, gray for roads, green for trees, brown for bare soil. That colored-in picture is a segmentation map.

### 12. What is a foundation model?

**Simple meaning:** A large AI model that has already been trained on a huge amount of general data, so it already "understands" broad patterns before we specialize it for our exact task.

**Technical meaning:** A large pretrained neural network (often a transformer) intended to be reused and adapted across many downstream tasks, instead of training a new model from scratch for each task.

**Real-life example:** Like hiring someone who already has years of general experience in a field, instead of training a complete beginner from day one.

**In our project:** We build on top of a pretrained geospatial foundation model rather than training a segmentation model from zero.

### 13. Why are we using Prithvi-EO-2.0?

Prithvi-EO-2.0 is a foundation model built by NASA and IBM specifically for Earth observation (satellite) imagery. It was already trained on a large amount of satellite data before we touch it, so it starts with a useful, general understanding of satellite images. Our project abstract names it as our initial chosen backbone model. *(Source: Prithvi-EO-2.0 paper, arXiv:2412.02732, 2024.)*

### 14. What is fine-tuning?

**Simple meaning:** Continuing to train an already-trained model on your own, more specific data, so it becomes good at your particular job.

**Technical meaning:** Updating a pretrained model's parameters (weights) using a new, usually smaller, task-specific dataset.

**In our project:** We fine-tune (adapt) Prithvi-EO-2.0 so it segments target-domain satellite images well.

### 15. Why is full fine-tuning expensive?

Foundation models like Prithvi-EO-2.0 have hundreds of millions of internal numbers (parameters). Updating *all* of them needs a lot of GPU memory, time, and data — and risks the model "forgetting" some of its useful general knowledge. Our team is working with Kaggle/Colab-scale resources, so full fine-tuning is a real cost concern, not just a theoretical one.

### 16. What is PEFT?

**Simple meaning:** Parameter-Efficient Fine-Tuning — adjusting only a small number of parameters instead of the whole model.

**Technical meaning:** A family of techniques (adapters, LoRA, visual prompt tuning, etc.) that freeze most of a pretrained model's weights and add or adjust a small number of new, trainable parameters to specialize the model for a new task.

**In our project:** LoRA is our chosen PEFT mechanism.

### 17. What is LoRA?

**Simple meaning:** Low-Rank Adaptation — a specific, lightweight way of adjusting a pretrained model without changing its original weights.

**Technical meaning:** Instead of directly updating a large weight matrix, LoRA freezes it and adds a small "correction" made of two much smaller matrices multiplied together. Only those small matrices are trained, drastically reducing the number of trainable parameters compared to full fine-tuning.

### 18. LoRA explained with a very simple analogy

Imagine a big, already-printed textbook (the frozen foundation model). Instead of reprinting the whole book to fix or update it, you stick a few small sticky notes with corrections in the margins. The book itself never changes — only the sticky notes are new, and they're small and cheap to write. LoRA is those sticky notes.

### 19. What is uniform LoRA?

**Simple meaning:** Sticking a correction sticky-note on *every single page* of the book, regardless of whether that page needed one.

**Technical meaning:** Inserting LoRA modules into every transformer layer of the model uniformly, without checking which layers actually need adaptation.

### 20. Why might adapting every layer be wasteful?

If only a few pages of the book actually contain outdated information, sticking notes on every page wastes effort — more trainable parameters than necessary, more compute, and possibly no benefit on pages that were already fine. This wastefulness is the starting concern behind DSSA's hypothesis.

### 21. What is a transformer layer?

**Simple meaning:** One processing "floor" in a tall building made of many stacked floors. Information enters at the bottom floor, gets processed a little, and passes up to the next floor.

**Technical meaning:** A transformer model is built from a stack of repeating blocks ("layers"), each performing self-attention and feed-forward processing on its input before passing the result to the next layer. Prithvi-EO-2.0, like most foundation models, is organized this way.

**In our project:** DSSA looks at each of these layers individually and decides, layer by layer, whether it needs adaptation.

### 22. Why might different layers be affected differently by domain shift?

Different layers tend to capture different kinds of information — some more general (basic textures, edges), some more specific/abstract. It is reasonable to expect that domain shift (a new sensor, a new region) might disturb some layers' understanding much more than others. **This is our project's hypothesis, not yet a proven fact** — it is exactly what DSSA is set up to test.

### 23. What is a representation / feature?

**Simple meaning:** As an image passes through the model, each layer turns it into a list of numbers that captures what that layer "noticed" about the image.

**Technical meaning:** At any given layer, the model's internal output for a given input is called a hidden representation (or feature) — a vector (or set of vectors) summarizing what that layer has extracted from the input so far.

**Real-life example:** Like taking notes at different stages of reading a book — your notes after chapter 1 capture different things than your notes after chapter 10.

### 24. What is representation drift?

**Simple meaning:** How much a layer's "notes" change when you switch from source-domain images to target-domain images.

**Technical meaning:** The difference between the distribution of hidden representations a layer produces for source-domain inputs versus target-domain inputs.

**In our project:** Representation drift, measured per layer, is the raw signal DSSA uses to decide where to adapt.

### 25. What is Domain Sensitivity Score (DSS)?

**Simple meaning:** A single number, computed for each layer, that tells you how much that layer's understanding changed between the source domain and the target domain.

**Technical meaning:** For a transformer layer *l*, DSS quantifies the statistical drift between the source-domain and target-domain feature distributions produced at that layer. A high DSS means the layer's behavior is strongly affected by the domain shift.

**In our project:** DSS is our project's central proposed metric — the whole "selective" part of DSSA depends on it.

### 26. How do we compare source and target representations?

We pass a set of source-domain images and a set of target-domain images through the same frozen model, collect the hidden representations produced at a chosen layer for both sets, and then apply a statistical formula that measures how different these two groups of representations are.

### 27. Where do CKA, MMD and cosine distance fit?

These are three different statistical formulas — candidate ways of measuring "how different are these two groups of representations":

- **Cosine distance:** compares the *direction* of representation vectors; ignores their overall size/magnitude.
- **MMD (Maximum Mean Discrepancy):** checks whether two sets of representations look like they came from the same overall statistical distribution.
- **CKA (Centered Kernel Alignment):** compares the overall structural similarity between two sets of representations, and is more robust to certain kinds of rotation/scaling differences.

Our project abstract lists all three as **candidates**; the final metric is meant to be chosen empirically (by testing), not decided in advance.

### 28. Why does DSS use unlabeled target images?

In the real world, when you move to a new sensor or region, you usually don't have ground-truth labels for it yet — labeling satellite images pixel by pixel is slow and expensive. DSS is designed to work using only the *raw* target images the model can already see, without needing anyone to label them, for the layer-selection step specifically.

### 29. Why do we calculate DSS before adaptation?

Because DSS is meant to *guide* the adaptation, not follow it. The idea is: first figure out where the model is struggling because of the domain shift, and only then adapt that part — instead of adapting blindly everywhere and hoping for the best.

### 30. What is Top-K layer selection?

**Simple meaning:** After ranking all the layers from most to least domain-sensitive (by DSS), just pick the top K of them — say, the top 3 — to actually adapt.

**Technical meaning:** A selection rule where only the K highest-scoring layers (by DSS) are chosen for adaptation; an alternative is a threshold rule, where any layer whose DSS exceeds a chosen cutoff is selected.

### 31. What does selective LoRA mean?

Instead of putting a LoRA "sticky-note patch" on every layer (uniform LoRA), we put it **only** on the Top-K / threshold-selected, most domain-sensitive layers. Every other layer stays completely frozen — untouched, exactly as pretrained.

### 32. Complete DSSA workflow

1. Train the foundation model on labeled **source** data → source-trained model.
2. Pass unlabeled **target** images through the frozen backbone → layer-wise representations.
3. Compare source vs. target representations at each layer → DSS per layer.
4. Rank layers by DSS, select Top-K / threshold → adaptation mask.
5. Insert LoRA **only** into the selected layers → adapted backbone.
6. Run target images through the adapted backbone + segmentation decoder → target segmentation maps.

### 33. What exactly are we trying to prove experimentally?

Whether DSSA (label-free, layer-selective adaptation) can reach segmentation quality close to full fine-tuning and uniform LoRA, **while using clearly fewer trainable parameters and less compute** — and whether the layers DSS picks actually matter more than picking layers randomly or by fixed position (early/middle/late).

### 34. What are our baselines?

Source-only (no adaptation), Full fine-tuning, Uniform LoRA, Adapters, Visual Prompt Tuning (if compatible), and DSSA itself.

### 35. What metrics will we measure?

- **Segmentation quality:** mIoU, per-class IoU, F1 score, pixel accuracy.
- **Efficiency:** trainable parameter count, GPU memory, training time, inference latency/throughput.
- **Robustness:** performance across whichever domain shifts (sensor/region/season/resolution) our chosen datasets actually support.
- **Analysis:** feature drift visualizations, qualitative prediction maps, failure cases.

### 36. What would count as success?

DSSA reaching segmentation performance **competitive with** (close to) full fine-tuning and uniform LoRA, while using substantially fewer trainable parameters — plus evidence that the DSS-selected layers genuinely matter (not just a coincidence). **This is the target outcome we are testing for, not something we have demonstrated yet.**

### 37. What are the current limitations / risks?

- DSSA is a **proposed research direction**; our own abstract requires a targeted novelty check against recent literature before any novelty claim.
- The exact source–target dataset pair (currently planned: LoveDA → DeepGlobe, with ISPRS Potsdam/Vaihingen/DynamicEarthNet for extra validation) is not finalized — it must be locked only after checking sensor bands, resolution, labels, licensing, and preprocessing compatibility.
- The final DSS metric (cosine / MMD / CKA) is not fixed yet — it needs a small empirical study.
- We must not claim cross-sensor transfer if the datasets we end up using don't actually provide a defensible domain shift.
- Compute is Kaggle/Colab-scale, which limits experiment size and speed.

---

<a name="section-b"></a>
# DSSA in One Simple Story

Remember the project this way:

> A model learns to segment satellite images from one sensor (the **source**). Then we give it images from a **different** sensor or region (the **target**). Its performance may drop — that's domain shift.
>
> Instead of retraining the whole model, we:
>
> 1. Look at the source images.
> 2. Look at the unlabeled target images.
> 3. Compare what the model "sees" (its representations) at each transformer layer, for both.
> 4. Find which layers changed the most.
> 5. Give those layers a high Domain Sensitivity Score (DSS).
> 6. Select the most sensitive layers (Top-K).
> 7. Put LoRA only on those layers.
> 8. Keep every other layer frozen.
> 9. Run the target images through this adapted model to get segmentation maps.
> 10. Compare the result against source-only, full fine-tuning, and uniform LoRA to see whether this selective approach is competitive while using far fewer trainable parameters.

If you remember nothing else, remember this: **DSSA tries to find out where the model got confused, and fix only that, instead of fixing everything.**

---

<a name="section-c1"></a>
# Paper 1 — SPECTRA

### In simple words

SPECTRA is a research paper that also tries to adapt a satellite foundation model — the same one we use, Prithvi-EO-2.0 — to work on a new sensor. Its problem is similar to ours: the new sensor's images might not even have the exact same "bands" (color channels) as what the model was trained on, and adapting the whole model is expensive.

Their solution has two parts:
1. **BRE (Band-Routed Embedding):** a small trainable piece at the very start of the model that re-maps whatever bands the new sensor gives you into the band format the pretrained model expects — like a universal adapter plug for a wall socket.
2. **Stage-Wise LoRA:** instead of giving every part of the model the same amount of adaptation, SPECTRA checks — using a small amount of **labeled** target data — which parts (they call them "stages," a stage being a group of layers) are more useful to adapt, and gives those stages a bigger LoRA "patch" (higher rank) and gives less-useful stages a smaller patch.

They measure "how useful is this stage" with something called a **transferability score**, calculated using a method called LogME. To calculate it, they need actual labels for a few target-domain examples.

### Why it is relevant to our project

SPECTRA is the closest published match to our own idea: same backbone (Prithvi-EO-2.0), same "cross-sensor adaptation" goal, and the same instinct that *not every part of the model deserves the same amount of adaptation*. This makes it our chosen **primary base paper**.

### Its important limitation, relative to DSSA

SPECTRA's stage-scoring step needs **labeled** target data (their LogME formula literally includes the target labels, called `Y`, in its calculation). It also only decides at the **stage** level (a group of several layers together), not for individual layers. Our proposed DSSA direction is exactly trying to see whether this same kind of decision can be made **without any target labels**, and at the **individual layer** level, using only the model's own frozen representations.

### Technical version

**Full title:** *SPECTRA: Band-Routed Embedding and Stage-Wise LoRA for Cross-Sensor Fine-Tuning of Geospatial Foundation Models*
**Authors:** Xingyan Li, Jordan A. Caraballo-Vega, Jie Gong, Mark L. Carroll, Jianwu Wang
**Venue:** ACM SIGSPATIAL 2026 — **arXiv:2608.01751**

**Problem addressed:** Adapting geospatial foundation models to downstream sensors that (a) have mismatched spectral bands from the pretraining sensor, and (b) require adaptation at low compute/parameter cost.

**Backbones tested:** Prithvi-EO-2.0 (ViT-Huge, ~600M parameters), SatMAE, ScaleMAE.

**Datasets:** Sen1Floods11, FireScars, Landslide4Sense, SA Crop Type — all labeled downstream segmentation/classification sets.

**Method, precisely:**
- **Band-Routed Embedding (BRE):** a trainable gating + small adapter module that remaps arbitrary input bands into a "virtual input image" matching the pretrained patch-embedding's expected band space, without modifying the frozen patch embedding itself.
- **Stage-Wise Transferability-aware LoRA (ST-LoRA):** the pretrained encoder is divided into stages (in the figure we use on Slide 2, four stages, each containing several attention blocks). A small labeled sample of target data is passed through the *frozen* encoder to get per-stage features; a **LogME transferability score** `q_s = LogME(Φ_s(X_sel), Y)` is computed per stage; an "ST-Planner" then maps each stage's score to a LoRA rank (higher score → higher rank, i.e., more trainable capacity), under an overall parameter budget.
- Only the BRE module, the inserted LoRA weights, and the task decoder are trained; the pretrained patch embedding and pretrained encoder stages themselves stay frozen.

**Main limitation relevant to our project:** The transferability-scoring step is **supervised** — it requires labeled target-domain data (`Y` in the LogME formula) — and operates at **stage** granularity, not individual transformer-layer granularity. The authors themselves note the resulting gains are "not universal" across every backbone/task combination tested.

---

<a name="section-c2"></a>
# Paper 2 — CrossEarth-Gate

### In simple words

CrossEarth-Gate tackles a related but slightly different problem: it says that domain shift in satellite images isn't just "one kind of difference" — it can show up as a difference in spatial layout, in the meaning/semantics of objects, or in frequency patterns (fine texture detail) — and one single fixed adaptation method might not handle all of these well.

Their solution: build a "toolbox" of *three* different adaptation modules — one good at spatial differences (LoRA), one good at semantic differences (an Adapter), and one good at frequency/texture differences (a Frequency module) — and insert all three into every layer/block. Then, instead of using all three all the time, they use a signal called **Fisher Information** (a measure, from the training gradients, of how important each module currently is for reducing the task's error) to decide, block by block, **which one or two of the three modules should stay "activated" and which should stay frozen**. This importance check is recalculated periodically **while the model is training**, using either the source labels or pseudo-labels (guessed labels) on the target data.

### Why it is relevant to our project

CrossEarth-Gate is the closest published idea to DSSA itself: it already does a kind of "measure importance, then only activate the important parts" selective adaptation for remote-sensing segmentation — and it even uses some of the same datasets our own abstract lists (LoveDA, ISPRS Potsdam, Vaihingen). This is why we study it as **closely related work**, not as our base paper.

### Its important limitation, relative to DSSA

CrossEarth-Gate's importance signal (Fisher Information) needs **gradients from the task loss**, which means it needs some form of labels — either real source labels or pseudo-labels guessed for the target — and it has to be **recomputed repeatedly during training**. Our proposed DSSA direction instead computes its signal (DSS) **once**, **before** any adaptation training starts, purely from the model's own frozen representations on **unlabeled** target images — no gradients, no pseudo-labels, no repeated recalculation.

### Technical version

**Full title:** *CrossEarth-Gate: Fisher-Guided Adaptive Tuning Engine for Efficient Adaptation of Cross-Domain Remote Sensing Semantic Segmentation*
**Authors:** Shilei Cao, Ziyang Gong, Hehai Lin, Yang Liu, Jiashun Cheng, Xiaoxing Hu, Haoyuan Liang, Guowen Li, Chengwei Qin, Hong Cheng, Xue Yang, Juepeng Zheng, Haohuan Fu
**Venue:** arXiv, 2025–2026 — **arXiv:2511.20302**

**Problem addressed:** Static or uniform PEFT cannot handle the "multifaceted" (spatial, semantic, and frequency) nature of domain gaps in cross-domain remote-sensing segmentation.

**Backbones tested:** DINOv2 (S/B/L), SAM-Huge, SatMAE-L, ScaleMAE-L (does not use Prithvi-EO-2.0).

**Datasets:** CASID (12 cross-domain, cross-climate-zone scenarios), RescueNet, and Potsdam↔Vaihingen, Rural↔Urban splits of LoveDA — some of the same datasets named in our own project abstract.

**Method, precisely:** A "Remote Sensing Module Toolbox" combining three module types — LoRA (targeting spatial differences), an Adapter (targeting semantic differences), and a Frequency module (based on Earth-Adapter/Fourier decomposition, targeting texture/frequency differences) — inserted at every block. Module importance is scored with the **diagonal Fisher Information Matrix** of the task loss:

`F̂_θ = (1/N) Σ (∇_θ log P_θ(Y_j | X_j))²`

computed periodically during training, using source labels (in the domain-generalization setting) or target pseudo-labels (in the domain-adaptation setting). Only the Top-k most important modules per block stay active; the rest are frozen.

**Main limitation relevant to our project:** Selection requires **gradients** of a supervised task loss (hence pseudo-labels are needed on the target side in the DA setting), and it is a **dynamic, training-time** process, not a one-shot, label-free, purely representational measurement. The paper reports competitive results across many of its benchmark comparisons, which means DSSA cannot claim that selective adaptation for remote-sensing segmentation is untried — only that DSSA's *specific* signal (unsupervised representation drift, computed once, per individual layer) is different from CrossEarth-Gate's.

---

<a name="section-d"></a>
# SPECTRA vs CrossEarth-Gate vs DSSA

| Aspect | SPECTRA | CrossEarth-Gate | DSSA (proposed) |
|---|---|---|---|
| Data required for selection | A small **labeled** target sample | Source labels, or target **pseudo-labels** | **Unlabeled** target images only |
| Target labels needed? | Yes | Indirectly (pseudo-labels in the DA setting) | No |
| Selection signal | Transferability score (LogME) | Fisher Information (from task-loss gradients) | Representation drift (cosine / MMD / CKA) |
| When selection happens | Once, before fine-tuning, using a small probe | Repeatedly, **during** training | Once, **before** adaptation training begins |
| Selection granularity | Encoder **stage** (a group of layers) | **Module type**, per block | Individual **transformer layer** |
| What gets selected | LoRA rank assigned per stage | Which module (spatial / semantic / frequency) stays active | Which individual layers receive LoRA |
| PEFT method | LoRA (variable rank) + Band-Routed Embedding | LoRA + Adapter + Frequency-module toolbox | LoRA only, on selected layers |

### In plain English

All three papers agree on one thing: **adapting everything equally is wasteful.** They disagree on *how to decide what to adapt*:

- **SPECTRA** asks a small labeled sample of the target data, "which stage helps you the most?"
- **CrossEarth-Gate** watches the training gradients and asks, repeatedly, "which module is currently pulling its weight?"
- **DSSA** proposes to skip labels and training signals entirely, and instead ask the frozen model itself, "which of your layers changed the most when I showed you the new domain?" — and to ask this question just once, before touching the model at all.

That's the one-sentence answer if the HOD asks "what's different between these three?"

---

<a name="section-e"></a>
# What is Missing?

We do **not** claim that nobody has tried selective adaptation before — CrossEarth-Gate already does something in that spirit, and reports strong results doing it. We also do not claim DSSA is "the first" of anything. Our own project abstract explicitly says DSSA is a **proposed research direction** and requires a targeted novelty check against recent literature before any novelty claim is made.

What we can say carefully is this:

The existing approaches we studied (SPECTRA and CrossEarth-Gate) both rely on **target-related or training-derived signals** to decide where adaptation should happen — either labeled target examples, or gradients/pseudo-labels computed during training.

**DSSA investigates whether:**

> UNLABELED TARGET DATA
> \+ SOURCE–TARGET REPRESENTATION DRIFT
> \+ LAYER-WISE SENSITIVITY
> \+ BEFORE ADAPTATION

...can be used to decide where LoRA should be inserted — without needing target labels or a training loop to compute the selection signal.

### Why this is an interesting question

If it works, it would mean useful adaptation decisions can be made from a much cheaper, more available signal (raw images only) than what SPECTRA or CrossEarth-Gate need. If it doesn't work as well, that is also a useful, honest finding — it would tell us that label-free representation drift isn't a strong enough signal on its own, and that supervised or gradient-based signals really are necessary. Either outcome is a valid contribution of the project.

### Clearly separating four things

| | Status |
|---|---|
| **Existing research** (SPECTRA, CrossEarth-Gate) | Published, with reported results. Verified via their papers. |
| **Our hypothesis** | Domain shift affects transformer layers unequally, and this can be detected via label-free representation drift. **Not yet tested.** |
| **Our proposed methodology** | DSSA's 6-stage pipeline (Section F). Designed, not yet implemented/run. |
| **Things not yet proven** | Whether DSSA matches full fine-tuning / uniform LoRA accuracy; whether DSS-selected layers genuinely outperform randomly-selected layers; which DSS metric works best. All labeled "Expected" until tested. |

---

<a name="section-f"></a>
# DSSA Methodology — Step by Step

## Step 1 — Source Training

**What happens:** We take the pretrained Prithvi-EO-2.0 foundation model and train it (with a segmentation decoder on top) on our **labeled source dataset**, producing a "source-trained model."

**Why we do it:** We need a working, accurate model on the source domain first — this is the starting point that domain shift will later disturb, and it's also what several of our baselines (source-only, full fine-tuning) are built from.

**Simple example:** Like training a student thoroughly using one specific textbook before testing them on a different textbook's questions.

## Step 2 — Target Analysis

**What happens:** We take **unlabeled** target-domain images (a different sensor/region/season) and pass them through the **frozen** source-trained backbone, just to observe what it produces — no training happens in this step.

**Why we do it:** This lets us see how the model "reacts" to the new domain, without needing anyone to label the target images — a key requirement of our proposed direction.

**Simple example:** Like showing the trained student a new type of question, just to watch how they think about it, without grading them yet.

## Step 3 — Feature Extraction

**What happens:** As the target images pass through the frozen model, we save the hidden representations produced **at each transformer layer**.

**Why we do it:** These layer-by-layer "notes" are what we will compare against the source domain's layer-by-layer notes, to see where the biggest change happened.

**Simple example:** Like collecting the student's scratch-work notes at every stage of solving a problem, not just their final answer.

## Step 4 — DSS Computation

**What happens:** For each transformer layer, we compare the source-domain representations against the target-domain representations, using a statistical distance/similarity measure, to get a Domain Sensitivity Score (DSS) for that layer.

**Why we do it:** A high DSS at a layer means that layer's understanding changed a lot due to the domain shift — this is our proposed signal for "this layer probably needs adaptation."

**Candidate metrics (to be chosen empirically, per our abstract):**
- **Cosine distance** — compares the direction of the representation vectors.
- **MMD (Maximum Mean Discrepancy)** — checks whether the two groups of representations come from a similar overall statistical distribution.
- **CKA (Centered Kernel Alignment)** — compares the overall structural similarity between the two groups of representations.

None of these three is fixed as final yet; our plan is to test candidates and pick the one that works best (this is Experiment E9, see Section G).

**Simple example:** Like measuring, chapter by chapter, how different the student's scratch-work looks when solving the new textbook's problems compared to the old textbook's problems.

## Step 5 — Layer Selection

**What happens:** We rank all the transformer layers by their DSS, from highest to lowest, and select either the Top-K layers or all layers above a chosen threshold.

**Why we do it:** This turns the DSS scores into an actual decision: exactly which layers will receive adaptation.

**Simple example:** Like picking only the 3 chapters where the student's approach changed the most, instead of re-teaching the entire textbook.

## Step 6 — Selective LoRA

**What happens:** LoRA modules are inserted **only** into the selected (high-DSS) layers. Every other layer stays completely frozen.

**Why we do it:** This is where we expect to save trainable parameters compared to uniform LoRA (which patches every layer) and full fine-tuning (which updates every parameter).

**Simple example:** Sticky-note corrections only on the 3 chapters that actually needed fixing, leaving the rest of the textbook exactly as printed.

## Step 7 — Target Segmentation

**What happens:** The adapted backbone (frozen layers + selectively-inserted LoRA layers) is combined with the segmentation decoder and run on target-domain images to produce the final pixel-by-pixel segmentation maps.

**Why we do it:** This is the actual deliverable — segmenting the new domain's images — and it's what we measure (mIoU, F1, etc.) to judge whether DSSA worked.

**Simple example:** The final, graded exam: does the adapted model correctly label roads, buildings, water, and forest in the new satellite's images?

---

<a name="section-g"></a>
# What is Actually Experimental

**Everything about DSSA's performance is currently a proposal, not a result.** Nothing has been trained or measured yet. The following experiments (from our project abstract) are the planned way we will find out whether DSSA works.

| Experiment | What it tests |
|---|---|
| Source-only | How badly does the model perform on the target domain with *no* adaptation at all? (a "how bad is the problem" baseline) |
| Full fine-tuning | The accuracy you get if you update the *entire* model — our upper reference point for accuracy, at maximum cost. |
| Uniform LoRA | The accuracy you get from standard PEFT, patching every layer equally — our main PEFT reference point. |
| Early-layer adaptation | What if we only adapt the first few layers? Tests whether low-level features are the most domain-sensitive. |
| Middle-layer adaptation | What if we only adapt the middle layers? |
| Late-layer adaptation | What if we only adapt the last few layers? Tests whether high-level/semantic features are the most domain-sensitive. |
| DSSA selection | Our proposed method: adapt only the layers DSS says are most sensitive. |
| Top-K sensitivity | Does using more or fewer selected layers change the result? |
| DSS metric ablation | Compare cosine distance vs. MMD vs. CKA — which one actually predicts useful layers? |
| Cross-domain validation | Does a layer-selection pattern that worked for one domain shift also work for a different one? |
| Efficiency analysis | Compare trainable parameters, GPU memory, training time, and inference time across all the above. |
| Representation analysis | Visualize and explain *why* particular layers were selected, and look at failure cases. |

### Why each experiment exists, in one line

Early/Middle/Late-layer experiments exist so that **DSSA's Top-K selection has something fair to be compared against** — if DSSA just reinvents "adapt the last few layers," that's an important, honest thing to find out.

### The metrics, explained simply

- **mIoU (mean Intersection-over-Union):** for each class (road, water, etc.), compare the predicted area to the true area — how much they overlap divided by how much they cover in total, averaged across classes. Higher is better; a perfect match is 1.0.
- **Per-class IoU:** the same idea, but reported separately for each class (so we can see if, say, "roads" are easy but "water" is hard).
- **F1 score:** a balance between catching all the correct pixels (recall) and not falsely labeling wrong pixels (precision).
- **Pixel accuracy:** simply, what fraction of all pixels were labeled correctly. (Can be misleading if one class, like "background," dominates the image.)
- **Trainable parameters:** how many numbers in the model actually get updated during adaptation — lower is cheaper.
- **GPU memory:** how much video memory is needed to run the adaptation — matters a lot on Kaggle/Colab-scale hardware.
- **Training time:** how long adaptation takes to run.
- **Inference time:** how long it takes the adapted model to segment one new image, after training is done.

**Simple example:** Imagine grading a map-coloring exercise. mIoU checks how well the colored regions overlap with the correct regions, class by class. Trainable parameters and GPU memory measure how much "effort and machine power" it took the student to prepare for the exam.

---

<a name="section-h"></a>
# How to Explain the PPT

There are exactly **4 slides**. This section explains each one, visual by visual, with a natural speaking script.

---

## Slide 1 — "Problem Statement & Related Work"

### What the audience sees

- On the left: a small vertical flow — **SOURCE DOMAIN** (marked with a navy square) → **FOUNDATION MODEL** → **TARGET DOMAIN** (marked with a rust/orange square) → **DOMAIN SHIFT** → **PERFORMANCE ↓**.
- On the right: two short paper mentions — **SPECTRA** (labeled "Primary Base Paper") and **CrossEarth-Gate** (labeled "Related Work"), each with a one-line description and citation.
- At the bottom: our central motivating question in quotes.

### What each visual means

- **SOURCE DOMAIN / TARGET DOMAIN (colored squares):** the navy square and the rust square are a simple color code — navy always means "the domain we trained on," rust always means "the new domain we're testing on." This tiny color distinction is the whole point of the visual: two different domains, same real-world scene.
- **FOUNDATION MODEL:** Prithvi-EO-2.0, sitting between the two domains — it's the same model seeing both, which is exactly why domain shift is a problem for it.
- **DOMAIN SHIFT → PERFORMANCE ↓:** this is the punchline of the flow — the mismatch between domains causes the drop, not any error in the model's design.
- **SPECTRA / CrossEarth-Gate boxes:** these are simply naming our two studied papers before we go into detail on the next slide.
- **The central question in quotes:** this is *our* research question, not a slogan — it previews exactly what Slide 3 will build up to.

### What the presenter should say (about 30–40 seconds)

> "Our project looks at a real problem with satellite AI models — a model trained on images from one satellite often performs worse when you point it at a different satellite, region, or season. That's called domain shift, and you can see it here: same model, but performance drops once the domain changes. Two recent papers deal with this — SPECTRA, which is our main base paper, and CrossEarth-Gate, which we studied as closely related work. Both try to adapt only part of the model instead of the whole thing. That leads to our question: can we figure out *where* to adapt using just the raw images, without needing labels?"

### What the presenter should NOT say

- Don't say "this is the first time anyone has studied this" — it isn't established, and CrossEarth-Gate already does something close.
- Don't say "our method already works" — nothing has been tested yet.

### Likely HOD question → Simple answer

**Q: "Why does domain shift even happen for satellite images specifically?"**
**A:** "Because different satellites have different sensors, resolutions, and capture conditions — even the same location can look statistically different depending on which satellite and season it was captured in."

---

## Slide 2 — "Existing Methodologies"

This is the most detail-heavy slide — walk through both real paper figures carefully.

### The SPECTRA figure — what to point at, bottom to top

1. **"All Bands" box (bottom):** this is the raw input — whatever spectral bands the new sensor happens to provide.
2. **"BRE" box, next to it:** point here and say — this is the Band-Routed Embedding, a small trainable piece that remaps those bands into the format the pretrained model expects, like a universal plug adapter.
3. **"Pretrained Patch Embedding" (frozen, snowflake icon):** the model's original input layer — untouched.
4. **"Stage-Wise Pretrained Encoder," Stage 1 through Stage 4 (frozen, snowflake icons):** these are groups of transformer layers, frozen.
5. **The "r=8 / r=8 / r=16 / r=32" boxes next to each stage, with flame icons:** these are the LoRA patches — point out that the rank number (r) is *different* per stage — bigger patches for stages judged more useful.
6. **"ST-Planner" box, on the right:** this is where the transferability score decides those different rank numbers, using a small labeled target sample.
7. **"Task Decoder" (flame icon) → "Prediction" (top):** the final trainable decoder producing the output.

**One simple sentence:** "SPECTRA remaps the input bands, then gives each stage of the model a differently-sized LoRA patch based on a labeled-data transferability score."

### The CrossEarth-Gate figure — what to point at

1. **"Input Xj / Label Yj" (left):** the training data, including labels (or pseudo-labels).
2. **The 3D landscape visualization ("Domain Distribution Gap in Gradient"):** this represents different domain conditions (different colored dots/regions) and how much the gradient signal shifts between them — don't over-explain this part, just say it visualizes how different domains create different gradient behavior.
3. **The formula box ("Fisher-Guided Adaptive Selection"):** this is the Fisher Information formula — say simply, "this measures, from the training signal, how important each module currently is."
4. **The "Remote Sensing Module Toolbox" (right side, Frequency / Semantic / Spatial boxes feeding into MSA/MLP):** point out the red triangle ("Activated") vs. blue snowflake ("Frozen") icons — this is the actual selective step: only some modules, in some blocks, stay switched on.

**One simple sentence:** "CrossEarth-Gate watches the training gradients and switches on only the most important adaptation module, block by block, while training is happening."

### What the presenter should say (about 40–50 seconds)

> "Here's how these two existing methods actually decide where to adapt. SPECTRA — on the left — remaps the input bands with this BRE module, then scores each stage of the model using a small amount of labeled target data, and gives more-useful stages a bigger LoRA patch — you can see the rank numbers differ per stage. CrossEarth-Gate — on the right — keeps a toolbox of three adaptation types and uses the training gradients, through this Fisher Information formula, to decide which module to switch on in which block, while training is ongoing. Both of these approaches work by leaning on a signal that comes from labels or from training itself."

### What the presenter should NOT say

- Don't say "this is just the architecture" and move on — always point at BRE/stages/ranks, or Fisher formula/toolbox, specifically.
- Don't claim exact accuracy numbers for either paper unless independently verified.

### Likely HOD question → Simple answer

**Q: "Why do both these papers need labels or training signal?"**
**A:** "Because their importance-scoring formulas — LogME for SPECTRA, Fisher Information for CrossEarth-Gate — are both built from label information, either real labels or gradients from a task loss."

---

## Slide 3 — "What is Missing?"

### What the audience sees

- Two short text chains: **SPECTRA** (Target labels → Stage-wise selection → LoRA) and **CrossEarth-Gate** (Training signal → Module selection → Adaptation), both flowing down into...
- A highlighted **"OUR QUESTION"** box: *"Can domain shift itself tell us WHERE to adapt?"*
- Below that, a **"DSSA — Research Direction"** box listing: Unlabeled target data + Source ↔ target feature drift + Layer-wise sensitivity + Before adaptation.
- A closing line: *"DSSA investigates whether representation drift can guide selective adaptation."*

### What each part means

- **The two chains:** these are literally the two "existing methodology" flows from Slide 2, compressed to their essence — this repetition is intentional, so the audience sees the pattern before the question is asked.
- **"OUR QUESTION":** this box is deliberately labeled a *question*, not a claim — we are not saying we already know the answer.
- **"DSSA — Research Direction":** notice the wording — "Research Direction," not "Our Discovery" or "Our Result." Each of the four listed ingredients (unlabeled data, feature drift, layer-wise sensitivity, before adaptation) is the answer to "what's different from the two chains above."

### Why this question follows naturally from Slides 1 and 2

Slide 1 showed the problem (domain shift hurts performance). Slide 2 showed that existing fixes both lean on labels or training signal to decide where to adapt. Slide 3 simply asks: what if we didn't need that signal at all — what if the domain shift itself, visible in the frozen model's own representations, was enough?

### What the presenter should say (about 30–40 seconds)

> "So both existing approaches end up needing some kind of label or training signal to decide where to adapt. That's the pattern you can see in these two chains. Our question is simple: can domain shift itself — just the difference between how the model represents source images versus target images — tell us where to adapt, without needing any of that? That's the direction we're calling DSSA: using unlabeled target data, measuring feature drift, looking at it layer by layer, and doing all of this before any adaptation training even starts."

### What the presenter should NOT say

- Avoid "no one has ever tried this" — say "research direction" or "investigates whether," as written on the slide itself.

### Likely HOD question → Simple answer

**Q: "Isn't this basically what CrossEarth-Gate already does?"**
**A:** "It's the closest related idea, yes — but CrossEarth-Gate's signal comes from gradients and needs labels or pseudo-labels, recomputed during training. We're testing whether a one-time, label-free, purely representational signal, computed before training starts, can do a similar job."

---

## Slide 4 — "Proposed Methodology — DSSA"

### What the audience sees

- A 7-box pipeline: Source Training → Target Analysis → Feature Extraction → DSS → Layer Selection → Selective LoRA → Target Segmentation.
- Below it, "Inside Selective LoRA": a Foundation Model box, followed by 8 small layer boxes — most gray ("frozen"), a few teal ("LoRA") — followed by a Segmentation box.
- A one-line comparison: **UNIFORM LoRA → LoRA on many/all layers** vs. **DSSA → LoRA on sensitive layers only.**
- A closing goal line, marked "(to be validated experimentally)."

### Explaining the 7-stage pipeline

1. **Source Training** — labeled source data trains Prithvi-EO-2.0 into a working source model.
2. **Target Analysis** — unlabeled target images pass through the *frozen* backbone.
3. **Feature Extraction** — we record what each layer produced for those target images.
4. **DSS** — we compare those to the source representations, layer by layer, to compute a sensitivity score.
5. **Layer Selection** — we rank the layers and keep the Top-K.
6. **Selective LoRA** — only those layers get LoRA; everything else stays frozen.
7. **Target Segmentation** — the adapted model, plus the segmentation decoder, produces the final pixel-level output.

### Explaining the layer-strip visual

Point at the row of 8 small boxes and say: "This is a simplified picture of one transformer encoder — most layers, in gray, stay exactly as pretrained. Only a few, in teal, marked high-DSS, get a LoRA patch." This is the single clearest visual answer to "what does 'selective' actually mean."

### Explaining "Uniform LoRA vs. DSSA"

This one line is the whole efficiency argument in miniature: uniform LoRA touches every layer; DSSA only touches the ones flagged as sensitive. Fewer touched layers should mean fewer trainable parameters.

### Explaining the final goal

Read the goal line as written — fewer trainable parameters *and* lower adaptation cost, *while keeping* segmentation quality competitive. Then immediately point at "(to be validated experimentally)" and say plainly that this is the target, not a finished result.

### What the presenter should say (about 45–60 seconds)

> "This is our full proposed pipeline. We start by training on labeled source data, using Prithvi-EO-2.0. Then we pass unlabeled target images through the frozen backbone and record what each layer produces. We compare that to the source representations to get a Domain Sensitivity Score per layer, rank the layers, and pick the top ones. Only those selected layers get a LoRA patch — you can see that here, most layers stay frozen, in gray, and only a few, in teal, get adapted. Then the adapted model runs the target images through the segmentation decoder to produce the final output. Compared to uniform LoRA, which patches every layer, DSSA only patches the sensitive ones. Our goal is fewer trainable parameters and lower adaptation cost, while keeping segmentation performance competitive — but that's still something we need to test experimentally, which is exactly what our six-month plan is for."

### What the presenter should NOT say

- Don't claim any specific parameter-saving percentage — we don't have one yet.
- Don't say "DSSA beats uniform LoRA" — say "we expect" or "we are testing whether."

### Likely HOD question → Simple answer

**Q: "What if DSSA doesn't beat uniform LoRA?"**
**A:** "That would still be a useful, honest finding — it would tell us that a label-free signal isn't strong enough on its own, and that the labeled or gradient-based signals SPECTRA and CrossEarth-Gate use really are necessary. Either result adds to our understanding."

---

<a name="section-i"></a>
# Image Cheat Sheet

### Image 1 — SPECTRA architecture figure (Slide 2, left)

- **Source:** Li, Caraballo-Vega, Gong, Carroll, Wang — *SPECTRA*, ACM SIGSPATIAL 2026, arXiv:2608.01751. (Cropped from the paper's own comparison figure, panel showing "SPECTRA (ours)".)
- **What it represents:** The full SPECTRA adaptation pipeline for one backbone — from raw input bands to final prediction.
- **Important parts:** The BRE box (input remapping), the four Stage boxes with their differing LoRA ranks (r=8/8/16/32), and the ST-Planner (where the transferability score decides those ranks).
- **What NOT to focus on:** The exact rank numbers (8/8/16/32) are just one example configuration from the paper — don't imply these are fixed rules.
- **One simple sentence:** "This shows SPECTRA giving each part of the model a differently-sized LoRA patch, based on a labeled-data score."

### Image 2 — CrossEarth-Gate figure (Slide 2, right)

- **Source:** Cao, Gong, Lin, Liu, Cheng, Hu et al. — *CrossEarth-Gate*, arXiv:2511.20302, 2025–26. (Cropped from the paper's overview figure, panel (b), "CrossEarth-Gate".)
- **What it represents:** How Fisher Information, computed from labeled input/label pairs, is used to decide which adaptation module (Frequency, Semantic, or Spatial) gets activated in a given block.
- **Important parts:** The Fisher Information formula box, and the "Activated" (red triangle) vs. "Frozen" (blue snowflake) icons on the module toolbox.
- **What NOT to focus on:** The 3D landscape visualization ("Domain Distribution Gap in Gradient") is illustrative — don't try to explain its exact math live; just say it represents how gradient behavior differs across domains.
- **One simple sentence:** "This shows CrossEarth-Gate using training gradients to switch on only the most important adaptation module in each block."

### Image 3 — Layer-strip visual (Slide 4)

- **Source:** Our own diagram, illustrating the proposed DSSA mechanism (not from either paper).
- **What it represents:** A simplified row of transformer layers, showing which ones would receive LoRA (teal, high-DSS) versus which stay frozen (gray, low-DSS).
- **Important parts:** The contrast between teal and gray boxes — that contrast *is* the entire idea of "selective adaptation."
- **What NOT to focus on:** The specific count (8 layers, 3 selected) is illustrative, not a fixed number from any experiment.
- **One simple sentence:** "This is a simplified picture of DSSA adapting only the layers it judges to be domain-sensitive."

---

<a name="section-j"></a>
# HOD Q&A

### 1. What is your problem statement?
**Short answer:** Satellite segmentation models trained on one sensor often perform worse on a different sensor, region, or season — this is domain shift, and fixing it usually means expensive full retraining or wasteful uniform adaptation.
**If HOD asks further:** Our abstract frames this specifically as: can we adapt efficiently, without full fine-tuning and without labeled target data?

### 2. Why is domain shift a problem?
**Short answer:** Because deep models partly learn the statistics of their training data, not just the underlying real-world objects — so when those statistics change, accuracy drops even though the real world didn't change.
**If HOD asks further:** This can come from sensor differences, resolution, region, season, or atmospheric conditions — anything that shifts the pixel-value distribution.

### 3. What is your base paper?
**Short answer:** SPECTRA — "Band-Routed Embedding and Stage-Wise LoRA for Cross-Sensor Fine-Tuning of Geospatial Foundation Models," ACM SIGSPATIAL 2026.
**If HOD asks further:** It uses the same backbone we use, Prithvi-EO-2.0, and adapts it across sensors using stage-wise LoRA guided by a labeled-data transferability score.

### 4. Why did you choose SPECTRA?
**Short answer:** Same backbone as ours, same cross-sensor goal, and a clean, explainable two-part method with a clear limitation — it needs labeled target data — that our proposed direction directly targets.
**If HOD asks further:** We compared it against several other candidates (CrossEarth-Gate, Earth-Adapter, DEFLECT, CrossEarth) and SPECTRA gave the clearest narrative bridge to our own idea.

### 5. Why did you also study CrossEarth-Gate?
**Short answer:** Because it's the closest published idea to DSSA itself — it already does a form of importance-guided selective adaptation for remote-sensing segmentation, so we study it honestly as related work.
**If HOD asks further:** Hiding it would make our novelty claim look weaker under scrutiny — disclosing it and explaining the real difference is the more defensible approach.

### 6. What is different between SPECTRA and your work?
**Short answer:** SPECTRA needs labeled target data and selects at the stage level; DSSA proposes using unlabeled target data and selecting at the individual layer level.
**If HOD asks further:** SPECTRA's scoring formula, LogME, literally requires the target labels as an input; DSS is designed to work without them.

### 7. What is different between CrossEarth-Gate and your work?
**Short answer:** CrossEarth-Gate's importance signal comes from training gradients (Fisher Information), recomputed during training; DSS is computed once, before training, from frozen representations only.
**If HOD asks further:** CrossEarth-Gate also selects module *types* per block, not individual transformer layers.

### 8. What exactly is DSS?
**Short answer:** Domain Sensitivity Score — a per-layer number measuring how much a layer's representation changes between source-domain and target-domain images.
**If HOD asks further:** It's computed by comparing the frozen model's hidden representations for source vs. target images at that layer, using a statistical distance measure (cosine, MMD, or CKA — to be chosen empirically).

### 9. Why do you need unlabeled target data?
**Short answer:** Because in practice, labels for a brand-new sensor or region usually aren't available yet — DSS is designed to work with what's actually easy to get: the raw images.

### 10. Why not use target labels?
**Short answer:** We could, but that's exactly what SPECTRA already does — our research question is specifically about whether we can skip that requirement.

### 11. Why layer-wise selection?
**Short answer:** Our abstract's hypothesis is that domain shift doesn't affect every transformer layer equally — layer-wise selection lets us test that directly, instead of assuming it.

### 12. Why not adapt every layer?
**Short answer:** Adapting every layer (uniform LoRA) uses more trainable parameters than may be necessary, if only some layers are actually affected by the domain shift.

### 13. What is LoRA?
**Short answer:** Low-Rank Adaptation — a lightweight way to adapt a frozen model by adding small trainable "correction" matrices instead of updating the original weights directly.
**If HOD asks further:** It drastically reduces trainable parameters compared to full fine-tuning, since the added matrices are much smaller than the original weight matrices.

### 14. Why Prithvi-EO-2.0?
**Short answer:** It's a geospatial foundation model built by NASA and IBM, already pretrained on satellite imagery, and it's the backbone named in our project abstract.

### 15. What is CKA?
**Short answer:** Centered Kernel Alignment — a way of measuring how structurally similar two sets of representations are, one of our candidate DSS metrics.

### 16. What is MMD?
**Short answer:** Maximum Mean Discrepancy — a statistical test for whether two sets of representations come from the same overall distribution, another candidate DSS metric.

### 17. Why cosine distance?
**Short answer:** It's a simple, fast way to compare the direction of representation vectors — one of three candidate metrics we plan to test empirically, not our final choice yet.

### 18. How do you choose Top-K?
**Short answer:** We plan to test different values of K experimentally (Experiment E8, "Top-K sensitivity") to see how the number of selected layers affects both accuracy and parameter savings.

### 19. What datasets are you planning to use?
**Short answer:** LoveDA as our primary source, DeepGlobe as our primary target, with ISPRS Potsdam, Vaihingen, and DynamicEarthNet as additional validation — pending a compatibility check on sensor bands, resolution, and labels.

### 20. How will you prove DSSA works?
**Short answer:** By comparing DSSA against source-only, full fine-tuning, and uniform LoRA baselines on segmentation quality (mIoU) and efficiency (trainable parameters, training time), across our planned experiment set.

### 21. What are your baselines?
**Short answer:** Source-only, full fine-tuning, uniform LoRA, adapters, and visual prompt tuning (if compatible).

### 22. What if DSSA performs worse?
**Short answer:** That's still a valid, useful research outcome — it would tell us a label-free signal isn't sufficient on its own, which is meaningful information for the field, not a failed project.

### 23. What is your actual novelty?
**Short answer:** We are not claiming proven novelty yet — our abstract requires a targeted novelty check first. What we can say is our proposed signal (label-free, one-shot, individual-layer representation drift) differs from both SPECTRA's (labeled, stage-level) and CrossEarth-Gate's (gradient-based, training-time, module-level) signals.

### 24. What are the limitations?
**Short answer:** DSSA is unproven so far; our dataset pair isn't finalized; our DSS metric isn't finalized; and we have limited (Kaggle/Colab-scale) compute.

### 25. What is your expected contribution?
**Short answer:** A tested answer to whether label-free, layer-wise representation drift can guide efficient adaptation — plus an open-source implementation and analysis of where and why it succeeds or fails, regardless of the outcome.

---

<a name="section-k"></a>
# If HOD Says: "Explain Your Project in 30 Seconds"

> "Satellite AI models often get worse when you point them at a different satellite or region — that's domain shift. Current fixes either retrain the whole model, or adapt it the same amount everywhere, using labels or training signals to decide where. We're testing something simpler: can we just compare what the model 'sees' on the old versus new images, layer by layer, using only unlabeled images, and adapt only the layers that changed the most? If it works, that means cheaper, more targeted adaptation — that's what we're building and testing over the next six months."

---

<a name="section-l"></a>
# 2-Minute Project Explanation

> "Our project is called DSSA, and it's about making satellite AI models adapt to new sensors and regions more cheaply.
>
> Here's the problem: a model trained to segment satellite images — labeling every pixel as road, building, water, and so on — often performs worse when you give it images from a different satellite, a different region, or a different season. That's called domain shift, and it happens because the model partly learns the statistics of its training images, not just the real-world objects in them.
>
> The usual fixes are expensive. You can retrain the whole model, which costs a lot of compute, or you can use a lightweight technique called LoRA and patch every part of the model equally, whether or not that part actually needs fixing.
>
> We studied two recent papers that try to be smarter about this. SPECTRA, our base paper, adapts a satellite foundation model called Prithvi-EO-2.0 — the same one we're using — by checking, with a small amount of labeled target data, which parts of the model are worth adapting more. CrossEarth-Gate, a closely related paper, does something similar but uses training gradients, recomputed while the model trains, to decide which adaptation module to switch on.
>
> Both of these need some kind of label or training signal to make that decision. Our research question is: can the model's own frozen representations — just comparing what it produces for old images versus new images — tell us where to adapt, without needing labels at all?
>
> That's the idea behind DSSA. We call it the Domain Sensitivity Score: for each layer of the model, we measure how much its output changes between the source domain and an unlabeled batch of target-domain images. Layers that change a lot get a high score. We rank all the layers, pick the top few, and only add LoRA there — everything else stays frozen.
>
> To evaluate this, we'll compare DSSA against source-only performance, full fine-tuning, and uniform LoRA, measuring both segmentation accuracy and how many trainable parameters and how much compute each approach needs. None of this is proven yet — it's a proposed direction, and that evaluation is exactly our plan for the next six months."

---

<a name="section-m"></a>
# Terms to Memorize

| Term | One-line meaning |
|---|---|
| **Domain** | The general condition/setting a batch of data comes from (e.g., a specific sensor, region, season). |
| **Domain Shift** | A mismatch between the data a model was trained on and the data it's later tested on. |
| **Semantic Segmentation** | Labeling every pixel of an image with what it is (road, water, building, etc.). |
| **Foundation Model** | A large model pretrained on lots of general data, meant to be adapted for many specific tasks. |
| **Prithvi-EO-2.0** | The NASA/IBM geospatial foundation model we use as our backbone. |
| **Transformer Layer** | One processing block in a stack of many, that a model's input passes through sequentially. |
| **Representation** | The internal numbers a layer produces to summarize what it "understood" about the input. |
| **Representation Drift** | How much a layer's representations change between the source domain and the target domain. |
| **PEFT** | Parameter-Efficient Fine-Tuning — adapting a model by training only a small number of new parameters. |
| **LoRA** | Low-Rank Adaptation — a specific PEFT method that adds small trainable "correction" matrices instead of changing original weights. |
| **Uniform LoRA** | Applying LoRA to every layer of a model equally, without checking which layers need it. |
| **DSS** | Domain Sensitivity Score — our proposed per-layer measure of how much a layer is affected by domain shift. |
| **CKA** | Centered Kernel Alignment — a candidate statistical measure of structural similarity between two sets of representations. |
| **MMD** | Maximum Mean Discrepancy — a candidate statistical test for whether two representation distributions differ. |
| **Cosine Distance** | A candidate measure comparing the direction of two representation vectors. |
| **Top-K** | Selecting only the K highest-scoring items (here, the K most domain-sensitive layers). |
| **Selective Adaptation** | Adapting only the layers/parts judged necessary, instead of adapting everything. |
| **Cross-Sensor Adaptation** | Adapting a model trained on one satellite sensor's images to work on a different sensor's images. |
| **mIoU** | Mean Intersection-over-Union — the main accuracy metric for segmentation, averaged across classes. |

---

*This document is a living reference for the team. If the dataset pair, DSS metric, or any methodology detail changes after experimentation, update this file rather than relying on memory of an earlier version.*
