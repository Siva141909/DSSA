# DSSA — Complete Final Review Presentation Script

**Presentation:** Domain Sensitivity-Guided Selective Adaptation for Remote Sensing Segmentation — Layer Selection versus Budget Spreading for LoRA Adaptation of Prithvi-EO-2.0
**Deck:** `DSSA_Final_Review.pptx` (10 slides; `DSSA_Final_Review_image-free.pptx` is the same deck without the ISPRS images)
**Audience:** Faculty, HOD, examiners and students with little or no background in remote sensing or deep learning.
**Suggested time:** about 15 minutes of talk (1.5 minutes per slide) plus questions.

---

# Before the presentation: Understand the whole project in one simple story

Imagine that you teach a student to recognise roads, buildings, trees and cars using aerial photographs of one city.

Then you give the student photographs of another city, taken with a different camera and from a different height. The student still recognises many things, but makes more mistakes. This is **domain shift**.

To help the student, you could retrain everything they know. That is expensive. Or you could give them a few small "correction notes". In AI, these small correction notes are called **LoRA**.

Our model, **Prithvi-EO-2.0**, has 24 internal processing stages called **transformer blocks**. The question we started with was:

> *Which of the 24 blocks should receive the correction notes?*

Our idea was a score called the **Domain Sensitivity Score (DSS)**. It measures how differently each block "sees" the two cities. We expected the blocks that see the cities most differently to be the best places for LoRA.

We tested this idea very carefully, in **both directions** (Potsdam → Vaihingen and Vaihingen → Potsdam), with **217 trained models**, and a **final test set that was opened only once**.

What we found:

1. **Adaptation clearly helps.** Every method improved accuracy on held-out test images.
2. **The block you adapt does matter**, but the best blocks change when the direction of transfer changes.
3. **DSS did not find the useful blocks.** It mostly ranked blocks by depth, and its picks were no better than random. Five other scores also failed.
4. **Most important:** with exactly the same number of LoRA parameters, putting a *tiny* amount of LoRA into *every* block beat putting a larger amount into *3 chosen* blocks — on every seed. Tiny LoRA everywhere also kept **88%** of the gain of standard LoRA while using **8 times fewer** LoRA parameters.

So our final message is: **"Spread, don't select."**

Keep this distinction in mind throughout: *the project's original hypothesis (selection) was not supported, but the project produced a clear, trustworthy and useful answer about how to spend a small adaptation budget.*

---

# Slide 1 — Title

## What is displayed on the slide?

- Title: Domain Sensitivity-Guided Selective Adaptation for Remote Sensing Segmentation.
- Subtitle: Layer Selection versus Budget Spreading for LoRA Adaptation of Prithvi-EO-2.0.
- Project team and roll numbers.
- Guide: Dr. Nagarjuna Devi.
- Four tags: Domain shift · Prithvi-EO-2.0 · Selective vs uniform LoRA · Potsdam ⇄ Vaihingen.
- November 2026 | Major Project Final Review.

## What you should say

"Good morning, respected HOD, faculty members, examiners and everyone present.

We are presenting the final review of our major project, DSSA — Domain Sensitivity-Guided Selective Adaptation for Remote Sensing Segmentation, carried out under the guidance of Dr. Nagarjuna Devi.

In our mid-phase review we showed that our layer-selection score mostly followed the depth of the network. Since then we have completed the full study: we repeated the experiments in the reverse direction, tested five more scores, compared selective adaptation with uniform adaptation at exactly the same parameter budget, and evaluated all final models once on a held-out test set.

The subtitle summarises the final question we answered: if you have a small budget of trainable parameters, should you spend it on a few selected layers, or spread it across all layers?

I will first explain the problem, then our method, the experiments, the final results, and what we conclude."

## Explain the four tags

### Domain shift
The difference between the data a model was trained on and the data it is used on — here, two different cities photographed with different cameras and resolutions.

### Prithvi-EO-2.0
A large pretrained "foundation model" for Earth observation, released by IBM and NASA. We use the 300-million-parameter version, which has 24 transformer blocks.

### Selective vs uniform LoRA
*Selective* = add LoRA to only a few chosen blocks. *Uniform* = add LoRA to all 24 blocks. Comparing these two at the same budget is the core experiment of the final phase.

### Potsdam ⇄ Vaihingen
Two German cities from the ISPRS aerial-image benchmark. The double arrow means we tested transfer in **both** directions.

## Likely questions

**Q1. What changed since the mid-phase review?**
We ran the reverse direction (Vaihingen → Potsdam, 75 more single-block runs), froze and tested six block scores, ran 67 equal-budget comparison runs with up to 10 seeds, and opened the Potsdam test set once for all 70 final models.

**Q2. In one sentence, what is your result?**
Adaptation helps a lot, but our scores cannot reliably choose which blocks to adapt, and at an equal budget, spreading LoRA over every block beats selecting blocks.

**Q3. Is the project a failure if the hypothesis failed?**
No. A research project answers a question. Our answer is clear, tested on held-out data, and gives a practical recommendation. A well-tested negative result prevents others from wasting effort on the same idea.

---

# Slide 2 — Domain Shift in Remote Sensing

## What is displayed on the slide?

- Two aerial images of the same ground size (50 m × 50 m): Potsdam (5 cm) and Vaihingen (9 cm). *(The image-free deck shows grey placeholder boxes instead.)*
- A small table: classes, ground resolution, acquisition, number of tiles.
- Trainable parameters: **306.7M** for full fine-tuning and **2.87M** for the LoRA budget we compare.
- "Where should these 98,304 LoRA parameters go?"
- Two research questions.
- Image credit line (ISPRS, DGPF, BSF Swissphoto).

## What you should say

"This slide explains the problem.

On the left are two real crops from our data. Both cover exactly 50 by 50 metres of ground and are shown at the same size. Potsdam was captured at about 5 centimetres per pixel and Vaihingen at about 9 centimetres, so the Vaihingen image is coarser. The buildings, roads and trees also look different because they are different cities captured in different campaigns.

Both datasets have the same six classes, so the task is the same — only the appearance of the data changes. That is domain shift.

On the right are the costs. Fine-tuning the whole model means training about 306.7 million parameters. In our comparisons we train only the small decoder plus exactly 98,304 LoRA parameters — about 2.87 million in total, less than 1% of the model.

That leads to our two research questions. First: can the difference between source and target features tell us which transformer blocks to adapt? Second: with an equal LoRA budget, is adapting a few chosen blocks better than spreading LoRA over all blocks?"

## 1. Why does domain shift happen in aerial images?

- **Location:** different cities have different building styles, road layouts and vegetation.
- **Sensor:** different cameras record colours and brightness differently.
- **Resolution:** 5 cm and 9 cm pixels show objects at different sizes.
- **Acquisition:** different dates, lighting and flight conditions.

## 2. What do the images show?

- They are **IRRG** images: Infrared, Red and Green bands. Infrared is displayed as red, so **vegetation appears red**.
- Both crops cover the same ground, so the difference in sharpness is real, not a zoom effect.
- The images illustrate the domain difference; they are not a measurement of accuracy loss.

## 3. The table

| Row | Potsdam | Vaihingen | Meaning |
|---|---|---|---|
| Classes | 6 ISPRS classes | same 6 | impervious surface, building, low vegetation, tree, car, clutter |
| Ground resolution | 5 cm | 9 cm | ground size of one pixel |
| Acquisition | different campaign | different campaign | captured separately |
| Tiles | 38 | 33 | number of large image tiles we use |

A **tile** is one large image file covering part of the city. A Potsdam tile is 6000 × 6000 pixels.

## 4. Trainable parameters

- **Full fine-tuning: 306.7M** = backbone 303.9M + decoder 2.77M. Every weight changes.
- **Our comparison budget: 2.87M** = decoder 2.77M + 98,304 LoRA parameters ≈ 0.93% of all parameters.
- The backbone stays **frozen** (unchanged) in every experiment.

### Why exactly 98,304?
LoRA of rank 8 on the query and value projections of one block costs 32,768 parameters. Three blocks cost 3 × 32,768 = **98,304**. Rank 1 on all 24 blocks costs 24 × 4,096 = **98,304** — exactly the same. This exact match lets us compare "select" and "spread" fairly.

## 5. The two research questions

1. **Selection question:** can a feature-difference score tell us which blocks to adapt?
2. **Budget question:** at an equal budget, is selecting a few blocks better than spreading over all blocks?

The first was our original DSSA hypothesis. The second checks the efficiency claim of our proposal.

## Likely questions — Slide 2

**Q1. Why these two datasets?**
They share the same six classes, so the task is identical, but they differ in city, resolution and acquisition — a clean, well-known domain-shift pair.

**Q2. Prithvi was trained on 30 m satellite data. Why use it on 5–9 cm aerial images?**
That makes the shift even larger, which makes adaptation more important. It is a hard test case. It is also a limitation: results might differ for satellite data closer to Prithvi's training data.

**Q3. Is 0.93% the same as "100 times cheaper"?**
It is about 100 times fewer *trainable* parameters. Training time and memory are not reduced by the same factor, because the full backbone still runs forward and backward. We did not run full fine-tuning, so we make no claim about beating it.

**Q4. Did you have permission to use the images?**
The ISPRS benchmark is for research use, and the slide carries the required acknowledgements. The image-free version of the deck is available for any setting where images should not be shown.

---

# Slide 3 — Implemented DSSA Architecture

## What is displayed on the slide?

- **Path A — DSS layer selection:** source + target images → fixed preprocessing → frozen Prithvi (24 blocks) → DSS per block (schematic bars) → keep Top-K (example K = 2: L22, L19).
- **Path B — Target segmentation training:** two rows of 24 blocks.
  - *Selective LoRA (DSSA):* rank 8 only in the selected blocks.
  - *Uniform LoRA (baseline):* rank 1 or 8 in all 24 blocks.
- Both feed the same decoder on L23, which outputs a 6-class map.
- Legend: frozen backbone 303.9M; trainable decoder 2.77M + LoRA (32,768 per block at rank 8; 4,096 at rank 1).

## What you should say

"This is the system we built. It has two parts.

Path A, at the top, runs once before any training and uses only images, no labels. Images from both cities pass through the same fixed preprocessing and through the frozen Prithvi model. For each of the 24 blocks we compute the Domain Sensitivity Score — how far the target-city features are from the source-city features, compared with the normal spread inside the source city. We rank the blocks and keep the top K. The bars here are a schematic; in reality DSS rose roughly with depth.

Path B is the training. In DSSA, LoRA goes only into the selected blocks — shown by the dashed arrows. The baseline we compare against puts LoRA into all 24 blocks, either at rank 1, which costs exactly the same as three rank-8 blocks, or at rank 8, which is standard LoRA.

In every method the backbone stays frozen and the decoder is identical. It always reads the last block, L23, and produces the six-class segmentation map. So the only thing that changes between methods is where the LoRA parameters go."

## Path A — step by step

1. **Images, unlabelled.** No labels are used to compute DSS.
2. **Fixed preprocessing.** Prithvi expects 6 satellite bands; our images have 3 (IRRG). We map them to the matching input channels and apply one fixed radiometric transform fitted on source images only. We do not normalise each dataset separately, because that would hide the very difference DSS tries to measure.
3. **Frozen Prithvi-EO-2.0-300M.** 24 blocks, embedding size 1,024. A 224 × 224 crop becomes 196 patch tokens.
4. **DSS per block** (details in the formulas section):
   - average the block's token features for each image;
   - build the **source centroid** (average source feature);
   - measure the cosine distance of each target image from that centroid;
   - standardise it against how far source images are from each other by chance.
5. **Rank blocks, keep Top-K.**

### What is a transformer block?
One processing stage. Early blocks capture simple patterns such as edges and colours; later blocks capture more abstract structure.

### What is a feature?
A list of numbers (here 1,024) that summarises what a block "sees" in an image.

### What is cosine distance?
A measure of how different the *direction* of two feature vectors is: 0 means the same direction, larger means more different.

## Path B — step by step

1. **Labelled target training tiles.** Random 224 × 224 crops with flips and rotations.
2. **Frozen backbone + LoRA.** LoRA adds a small trainable update W = W₀ + (α/r)·B·A to the query and value weights. B starts at zero, so training starts from the original model.
3. **Decoder.** Four upsampling stages turn the 14 × 14 feature map into a full-resolution 6-class map. It has 2,766,726 parameters.
4. **Loss.** Cross-entropy + Dice, equal weight. Dice helps with small classes like cars.

### What is rank?
The size of the LoRA update. Rank 8 gives each adapted matrix 8 "directions" of change; rank 1 gives one. Parameters per block = 4,096 × rank.

### Why does the decoder always read L23?
If it read a different block for each method, we could not tell whether a result came from LoRA placement or from the decoder seeing different features. Keeping it fixed makes the comparison fair.

## Important scientific distinction

Path A uses **no labels**. Path B is **supervised** on target labels. So this is *not* unsupervised domain adaptation: only the **choice of layers** is label-free.

## Likely questions — Slide 3

**Q1. Why LoRA on Q and V only?**
That is the standard choice from the original LoRA paper and keeps the parameter count small and comparable across methods.

**Q2. Why α = 16 for rank 8 but α = 2 for rank 1?**
We keep α/r = 2 in every run, so the scale of the update is consistent across ranks.

**Q3. Is the decoder the same in uniform and selective runs?**
Yes — same architecture, same starting weights for a given seed, same training data order.

**Q4. Why not compute DSS with labels?**
The point of DSS was to decide *before* training, without labels. We did also test two label-based scores (Fisher and LogME) as references — see Slide 6.

---

# Slide 4 — Datasets and Experiments

## What is displayed on the slide?

- **Setting 1 · Potsdam → Vaihingen (Phase 2):** split bar 15 train, 5 train + probe, 5 val, 8 test (locked). Source: 38 Potsdam tiles, images only.
- **Setting 2 · Vaihingen → Potsdam (Phase 3):** split bar 15 train, 5 + probe, 8 val, 10 test. Source: 20 Vaihingen training tiles, images only.
- **217 training runs** + 700 test-tile evaluations · up to 10 seeds · 2,000 steps each.
- Table of the studies.
- Same recipe · paired seeds · frozen in advance.

## What you should say

"We used the two cities in two settings.

In setting 1, from our mid-phase work, Potsdam images are the source and Vaihingen is the target. The Vaihingen test tiles were locked and never opened.

In setting 2, the final phase, we reversed the roles: Vaihingen is the source and Potsdam is the target. This is important because the Potsdam labels had never been used before, so this setting is a genuinely new test. We split the 38 Potsdam tiles by sorted name — 20 for training, 8 for validation, 10 for the final test — before reading any label.

In total we trained 217 models. 75 single-block runs in each direction measure how useful each block is. Six block scores were compared against those measurements. 67 more runs compared ten methods at the same budget. Finally, all 70 final models were evaluated once on the 10 Potsdam test tiles — 700 evaluations.

Every run used the same recipe. For each seed, all methods started from the same weights and saw the same data in the same order, so comparisons are fair. And the split, scores, thresholds and analysis code were all frozen before the experiments that would judge them."

## 1. Training, validation and test — a simple example

Think of an exam:
- **Training tiles** are the textbook — the model learns from them.
- **Validation tiles** are practice tests — used to compare methods during the study.
- **Test tiles** are the final exam — opened **once**, at the very end, for frozen models only.

If we kept checking the test while changing the method, we would slowly tune the method to the test, and the final score would be too optimistic.

### What is the probe set?
5 of the 20 training tiles whose **images** were used to compute label-free scores. They are still training tiles.

## 2. The study table

| Study | Runs | What it measures |
|---|---|---|
| Single-block, Potsdam → Vaihingen | 75 | gain of LoRA in each block alone (decoder-only + 24 blocks × 3 seeds) |
| Single-block, Vaihingen → Potsdam | 75 | the same on new target labels |
| Block scores | 6 scores | do scores predict the measured gains? |
| Equal-budget methods | 67 + 3 reused | ten methods at 98,304 LoRA parameters (+ a rank-8 reference) |
| Final test | 70 models × 10 tiles | one opening, one pre-registered test |

### What is a run?
One complete training of a model with one configuration and one seed: 2,000 training steps of 8 crops each, then evaluation.

### What is a seed?
A starting number for the random number generator. It controls the decoder's starting weights, LoRA's starting weights and the order of training crops. Seeds 1000, 2000, … 10000 are just labels; the same seed repeats the same random choices.

### Why "paired seeds"?
For seed 4000, the uniform-rank-1 model and the 3-block model start from identical decoder weights and see identical crops. So the difference between them comes from LoRA placement, not luck. We verified this with hashes before every run.

### What does "frozen in advance" mean?
Before each phase we wrote down the split, the scores, the pass/fail thresholds, the methods, the seeds and the analysis code, and stored their hashes (digital fingerprints). This is called **pre-registration**. It prevents us from choosing whatever analysis makes the result look best.

## Likely questions — Slide 4

**Q1. Why reverse the direction?**
To test our findings on labels we had never used. Any pattern seen only in one direction might be a coincidence of that dataset pair.

**Q2. Why 3 seeds for single-block but 10 seeds for the main comparison?**
Single-block studies have 25 configurations × 2 directions, so 3 seeds keeps them affordable. The main confirmatory comparison needed more precision, so it got 10 seeds.

**Q3. What hardware?**
A 16 GB Apple M5 laptop with PyTorch on the MPS backend. Every process was watched for memory, swap, temperature, sleep, battery and stalls. The highest memory peak was 10.35 GB.

**Q4. Did any runs fail?**
A few runs were stopped by our safety checks (for example the laptop sleeping or a slow GPU period). Each stopped run was kept as evidence and repeated with exactly the same seed and data. Nothing was retried automatically, and no result was changed.

**Q5. How much computation was this?**
More than 110 hours of computation in total, across training and evaluation.

---

# Slide 5 — Which Blocks Help? Single-Block Utility

## What is displayed on the slide?

- A line chart with 24 points per line — one per block.
  - **Navy:** Potsdam → Vaihingen (decoder-only baseline 0.518).
  - **Green:** Vaihingen → Potsdam (decoder-only baseline 0.569).
- Y-axis: Δ mIoU — the gain from LoRA in that one block over the same-seed decoder-only model, mean of 3 seeds, on validation.
- Cards: **L16 +0.037** (best on Vaihingen) · **L7 +0.052** (best on Potsdam) · **Upside-down U** in both directions.

## What you should say

"Before testing any score, we needed to know the truth: how much does each block actually help?

So we trained LoRA in each of the 24 blocks alone, three seeds each, in both directions, and measured the gain over a model that trains only the decoder.

The navy line is Potsdam to Vaihingen. Gains are small at the start, highest in the middle — L11 to L17 — with the best block L16 at +0.037, and lower again at the end.

The green line is the reverse direction. Every block helps here, and the best block moves earlier, to L7 at +0.052.

Both curves have an upside-down U shape. So the block you adapt clearly matters. But the useful region is not fixed — it moves when the source and target change. That is exactly what a good selector would have to predict."

## 1. What is utility?

Utility = mIoU(LoRA in block ℓ, seed s) − mIoU(decoder only, seed s).

It is "how much better than the baseline" one block makes the model. Positive is good.

## 2. What is mIoU?

- **IoU** for a class = overlap between predicted area and true area ÷ their combined area.
- **mIoU** = average IoU over the six classes. Each class counts equally, so small classes like cars matter as much as large ones.
- 0 means nothing correct; 1 means perfect.

## 3. Key observations

- Setting 1: L0 slightly hurts (−0.007); L11–L17 strongest; L23 low (+0.015).
- Setting 2: all 24 blocks help (+0.021 to +0.052); best three L7, L10, L8.
- Shape: rises, flattens, falls — an upside-down U — in both directions.

## 4. Why can't we just say "always use L16"?

Because in the other direction L16 is not the best. The best region moved from the middle-late blocks to the early-middle blocks.

## Likely questions — Slide 5

**Q1. Why are the Potsdam gains larger?**
Different target, different baseline and different difficulty. We compare within a direction, not across directions.

**Q2. Are neighbouring blocks really different?**
Not reliably. With 3 seeds, single-block differences of neighbouring blocks are within noise. The overall shape is reliable; exact ranks are not.

**Q3. Why does the middle help most?**
We do not know for sure. One possible reason: early blocks hold low-level patterns that everything depends on, and the last blocks feed the fixed decoder directly, so the middle may have the most useful room to change. We have not tested this explanation.

---

# Slide 6 — Can a Score Pick the Right Blocks?

## What is displayed on the slide?

- **Left (setting 1):** bars of Spearman correlation with measured utility: DSS 0.420, deeper-first rule 0.422, DSS with depth removed 0.076. "DSS ranking ≈ depth ranking (ρ = 0.94). Its top-1/3/5 picks were no better than 20,000 random picks."
- **Right (setting 2):** table of six scores with their top 3 blocks, correlation and gate result. "No label-free score passed. DSS now picks the earliest blocks."
- Banner: "DSS mostly tracks depth, and no score we tested reliably finds the useful blocks."

## What you should say

"Now we test the scores against the truth from the previous slide.

On the left is DSS in setting 1. Its correlation with the measured gains is 0.420. But a simple rule — 'prefer deeper blocks' — gets 0.422, the same. The DSS ranking itself correlates 0.94 with depth. When we remove the effect of depth, only 0.076 is left. And DSS's top picks were no better than random picks.

In setting 2 we went further. Before training, we froze six scores — DSS, a new resolution-based score, two more label-free scores, and two scores that use labels, Fisher and LogME. Each label-free score had to beat a fixed depth rule learned from setting 1 on four conditions. None passed.

Something surprising happened with DSS: in setting 1 it picked the deepest blocks, and in setting 2 it picked the earliest blocks — the opposite end of the network. A score that flips like this cannot guide block selection.

So our conclusion is that DSS mostly tracks depth, and none of the scores we tested reliably finds the useful blocks."

## 1. Correlation, simply

- **Spearman correlation (ρ)** compares two *rankings*. +1 = same order, 0 = unrelated, −1 = reversed.
- **Partial correlation controlling for depth** = the correlation left after removing what block depth already explains. If it is near 0, the score knows nothing beyond "how deep is this block".

## 2. The six scores (setting 2)

| Score | Uses labels? | What it measures | Result |
|---|---|---|---|
| DSS | No | source–target feature distance, standardised | picked L3–L5; failed |
| GSD sensitivity | No | how much a block's features change when a source image is resized to the target's resolution | copied the depth rule; failed |
| IO-similarity | No | how much a block changes its input | picked the first blocks; failed |
| Activation norm | No | size of the block's output | pointed the wrong way; failed |
| Fisher | Yes | how strongly the training loss reacts to the block's LoRA | reference only |
| LogME | Yes | how well the block's frozen features predict labels | reference only; found near-best single blocks |

## 3. The screening gate

A label-free score had to beat a fixed **depth prior** (an upside-down-U curve fitted on setting 1, never refitted). It passed only if all four held:
1. residual correlation ≥ 0.30 (it adds information beyond the prior);
2. it stays ≥ 0.15 when any one seed is left out;
3. it stays ≥ 0 when tiles are resampled;
4. its top-3 blocks are no worse than the prior's top-3.

DSS and IO-similarity passed the first three but failed the fourth: they had some extra information, but their actual picks were worse.

## 4. Why did DSS follow depth?

Deep blocks have very little natural variation between source images. DSS divides by that variation, so deep blocks get high scores mainly because the denominator is small — not because adaptation helps them most.

## Likely questions — Slide 6

**Q1. LogME found near-best blocks. Why not use it?**
It needs labels, and when its three blocks were trained together they were still no better than random blocks (Slide 8). Single-block gains did not add up when blocks were combined.

**Q2. What is a "depth prior"?**
A fixed formula, p(ℓ) = −1.8386×10⁻⁴ ℓ² + 4.9992×10⁻³ ℓ − 4.1343×10⁻⁴, fitted to the setting-1 gains. It encodes "middle blocks are best". Its top 3 are L14, L13, L15.

**Q3. Why test so many scores?**
To make sure the failure was not just a weakness of DSS. Six different kinds of score, including two that use labels, all failed to give a better choice than random.

---

# Slide 7 — Select or Spread? Same Budget, Different Placement

## What is displayed on the slide?

- Three strips of 24 blocks:
  - **3 chosen blocks, rank 8** (e.g. depth prior L13–L15) — 98,304.
  - **All 24 blocks, rank 1** — 98,304.
  - **All 24 blocks, rank 8** (standard LoRA reference) — 786,432.
- "3 × 32,768 = 24 × 4,096 = 98,304 LoRA parameters: an exact budget match."
- Validation table of ten methods (Potsdam, 8 tiles).
- Box: "At equal budget, spreading wins on validation."

## What you should say

"This slide is the heart of the final phase.

The top two strips have exactly the same number of LoRA parameters — 98,304. In the first, all of it goes into three chosen blocks at rank 8. In the second, it is spread thinly as rank 1 across all 24 blocks. The third strip is standard LoRA at rank 8 everywhere — eight times more parameters — used as a reference.

We tested seven ways of choosing three blocks: the depth prior, middle blocks, late blocks, DSS, Fisher, LogME, and ten random draws. All use the same 98,304 parameters as uniform rank 1.

On validation, uniform rank 1 reached 0.665, clearly above every three-block method. The best three-block method was not a clever score — it was random blocks, at 0.639. The depth prior, our pre-registered main candidate, reached 0.629."

## 1. The ten methods

| Method | Blocks | Seeds | Val mIoU | Gain |
|---|---|---|---|---|
| Uniform rank 8 | all 24 | 5 | 0.681 | +0.112 |
| **Uniform rank 1** | all 24 | 10 | **0.665** | **+0.095** |
| Random-3 | 10 draws | 10 | 0.639 | +0.070 |
| Fisher-3 | L12, L18, L21 | 5 | 0.634 | +0.064 |
| LogME-3 | L6, L7, L8 | 5 | 0.632 | +0.063 |
| Middle-3 | L10–L12 | 5 | 0.630 | +0.060 |
| Prior-3 | L13–L15 | 10 | 0.629 | +0.060 |
| DSS-3 | L3–L5 | 5 | 0.627 | +0.057 |
| Late-3 | L21–L23 | 5 | 0.617 | +0.048 |
| Decoder only | none | 10 | 0.569 | 0 |

## 2. Why Prior-3 was the main candidate

The protocol said: if a label-free score passes the gate, it becomes the main candidate; otherwise the frozen depth prior does. No score passed, so Prior-3 was tested against uniform rank 1 as our single confirmatory test.

## 3. Why is "Random-3" one seed per draw?

Random-3 uses 10 fixed random sets of 3 blocks, each trained with one seed. It represents "a typical random choice", not one particular set.

## Likely questions — Slide 7

**Q1. Isn't rank 1 too small to learn anything?**
That was our expectation too — but rank 1 in every block gave large gains. A small change in many places was more useful than a larger change in a few places.

**Q2. Why compare at exactly the same budget?**
Otherwise a method could win just by having more parameters. Equal budgets make it a fair test of *placement*.

**Q3. Why does standard LoRA (rank 8 everywhere) score highest?**
It has 8 times more LoRA parameters. It is our upper reference, not a competitor at the same budget.

---

# Slide 8 — Final Results: Potsdam Test Set

## What is displayed on the slide?

- Horizontal bars of **test mIoU** on 10 held-out Potsdam tiles (opened once), mean over seeds:
  Uniform r8 0.627 · Uniform r1 0.615 · Random-3 0.590 · Fisher-3 0.583 · LogME-3 0.582 · Middle-3 0.582 · Prior-3 0.581 · DSS-3 0.578 · Late-3 0.570 · Decoder only 0.529.
- Colours: green = uniform LoRA, grey = 3 selected blocks, orange = decoder only.
- Callouts: **+0.099** (standard LoRA gain) · **88%** (kept by rank 1) · **+0.042 to +0.062** (every 3-block choice).

## What you should say

"These are the final results on the Potsdam test set — ten tiles that nobody had looked at, opened once after all 70 models were frozen.

First, adaptation clearly helps: every method beats the decoder-only model, by between 4 and 10 mIoU points.

Second, standard LoRA on all blocks gains +0.099. Uniform rank 1 gains +0.087 — that is 88% of the gain with eight times fewer LoRA parameters.

Third, every three-block method, at the same budget as rank 1, gains only +0.042 to +0.062. And none of the scoring methods beat random blocks.

Finally, the ranking of all ten methods is exactly the same as on validation, and every score is about 0.04 to 0.05 lower. That consistency tells us our validation results were not over-fitted."

## 1. Why is test lower than validation?

The test tiles are different parts of the city, somewhat harder on average. What matters is that **every** method dropped by a similar amount and the **order did not change**.

## 2. How 88% is computed

Gain of uniform rank 1 ÷ gain of uniform rank 8 = 0.0869 ÷ 0.0985 ≈ 0.88.

## 3. Per-class view (from the report)

All classes improve with adaptation; cars improve the most; clutter remains the hardest class (IoU about 0.13–0.23 for every method).

## Likely questions — Slide 8

**Q1. Is uniform rank 1 better than full fine-tuning?**
We do not know — full fine-tuning did not fit in 16 GB of memory, so we did not run it. We only claim it is efficient compared with standard LoRA and better than selection at the same budget.

**Q2. How sure are you about these numbers?**
Each arm has 5 or 10 seeds with narrow 95% intervals (for example uniform rank 1: 0.611 to 0.620). The main comparison is tested formally on the next slide.

**Q3. Why is Random-3 better than score-based choices?**
Random draws often include early-middle blocks, which were most useful on Potsdam. The scores consistently picked blocks in less useful regions. It shows how hard block selection is.

---

# Slide 9 — Final Results: Selective vs Uniform LoRA

## What is displayed on the slide?

- Orange bars: test mIoU of Prior-3 minus uniform rank 1, for each of the 10 seeds. All negative, from −0.025 to −0.047.
- Dashed green line at **−0.010**: the margin for "as good as".
- Mean paired difference **−0.0341**; 95% CI **[−0.0392, −0.0291]**; needed: lower bound above −0.010.
- 10 / 10 seeds worse · tile bootstrap [−0.0387, −0.0304] · 0.581 vs 0.615.
- Box: "Selective adaptation is not as good."

## What you should say

"This is our single pre-registered test — the one we wrote down before the final experiments.

The question was: is the best frozen three-block choice at least as good as uniform rank 1, allowing a small margin of one mIoU point?

Each bar is one seed: the three-block model's test score minus the uniform model's score, with identical starting weights and data. For 'as good as', the bars needed to stay above the dashed line. Every single seed is far below it.

The mean difference is −0.034, and the 95% confidence interval runs from −0.039 to −0.029. To pass, the lower end had to be above −0.010. It is three times further away. Resampling the test tiles 10,000 times gives the same range, and not one resample came within the margin.

So the answer is clear: at the same budget, choosing three blocks loses about 3.4 mIoU points to spreading LoRA over all blocks."

## 1. What is a non-inferiority test?

It asks "is method A **not worse** than method B by more than a small margin?" — not "is A better?". We chose a margin of 0.010 mIoU (one point) in advance as the largest loss we would accept in exchange for using fewer blocks.

## 2. What is a 95% confidence interval?

A range that, given our 10 seeds, very likely contains the true average difference. Here the whole range is far below −0.010, so non-inferiority is rejected.

## 3. What is the tile bootstrap?

We randomly re-draw the 10 test tiles (with replacement) 10,000 times and recompute the difference. It checks that the result does not depend on a few particular tiles. It agreed fully.

## 4. Why only one confirmatory test?

Running many tests and reporting the best one inflates false positives. One test, fixed in advance, gives an honest yes/no answer. All other comparisons on these slides are descriptive.

## Likely questions — Slide 9

**Q1. Why a margin of 0.010?**
It was set before the experiment as a small, practically meaningful loss. The observed loss (0.034) is more than three times larger, so any reasonable margin would give the same answer.

**Q2. Could a better choice of 3 blocks have passed?**
We tested seven different ways of choosing, including label-based ones and random draws; all were below uniform rank 1. Even the best-performing choice (random) was 0.025 behind.

**Q3. What is the p-value?**
For non-inferiority, the one-sided p-value is essentially 1 — there is no evidence that selection is as good as uniform.

---

# Slide 10 — Key Findings and Conclusion

## What is displayed on the slide?

- **What held up:** adaptation clearly helps · spreading a small rank is efficient · layer choice matters.
- **What did not:** DSS as a layer selector · other block scores · selecting blocks at equal budget.
- **Limitations:** one backbone and one city pair · LoRA on Q/V, decoder on L23 · only ranks 1 and 8 · no full fine-tuning (16 GB memory).
- **Future work:** repeat on LoveDA · rank sweep · locked Vaihingen test · full fine-tuning · IGARSS 2027 paper.
- Banner: **"Spread, don't select."**

## What you should say

"To summarise.

What held up: adaptation clearly helps, by 4 to 10 mIoU points on held-out data. Spreading a small rank over all blocks is very efficient — 88% of standard LoRA's gain with eight times fewer LoRA parameters. And the block you adapt does matter.

What did not hold up: DSS as a layer selector — it tracks depth, is no better than random and flips between directions. None of the other scores helped either. And selecting three blocks lost clearly to spreading the same budget, on all ten seeds.

Our limitations: one backbone, one pair of cities, LoRA only on query and value, two ranks for uniform LoRA, and no full fine-tuning because of our 16 GB laptop.

For future work, we would repeat the study on a different dataset such as LoveDA, try more ranks, check our first study on the locked Vaihingen test tiles, compare with full fine-tuning on a bigger machine, and write up the study for IGARSS 2027.

Our final message is: spread, don't select. Layer choice matters, but no score we tested can make it reliably, and with an equal LoRA budget, a very small rank on every block is a simple, strong and cheap choice.

Thank you. We are happy to take questions."

## Important distinction: what failed and what did not

| Failed | Did not fail |
|---|---|
| DSS as a block selector | The DSS computation itself (repeatable, deterministic) |
| Selection at an equal budget | LoRA adaptation in general |
| Label-free scores as selectors | The experimental method (pre-registered, paired, single test opening) |

## Likely questions — Slide 10

**Q1. What is your contribution if the hypothesis failed?**
(1) A full map of block-wise LoRA utility in both directions for a geospatial foundation model. (2) A pre-registered test showing six scores do not reliably select blocks. (3) A clear, practical result: at a fixed budget, uniform low-rank LoRA beats block selection. (4) A reusable, carefully checked experimental pipeline.

**Q2. Can this be published?**
Yes, as a careful empirical study. Pre-registered negative results with a clear positive recommendation are valuable. We are targeting a 4-page IEEE IGARSS 2027 paper (deadline 11 January 2027). A third dataset such as LoveDA would make it stronger.

**Q3. What would you do differently?**
Plan the budget-matched comparison from the start, and use a machine with more memory so full fine-tuning can be included.

---

# Additional preparation: Technical terms you must understand

| Term | Simple explanation |
|---|---|
| Remote sensing | Collecting information about the Earth without touching it |
| Aerial imagery | Images captured from aircraft (our data), not satellites |
| Domain / domain shift | A data environment / differences between two data environments |
| Semantic segmentation | Giving every pixel a class |
| Tile | One large image file covering part of a city |
| Ground resolution (GSD) | Ground size of one pixel (5 cm, 9 cm) |
| IRRG | Infrared, Red, Green bands; vegetation appears red |
| Foundation model | A large model pretrained on huge data, reused for many tasks |
| Backbone | The main feature-extraction part of the network (frozen here) |
| Transformer block | One processing stage; Prithvi has 24 (L0–L23) |
| Feature | Numbers summarising what a block sees |
| Frozen / trainable parameter | Not updated / updated during training |
| Fine-tuning | Updating a pretrained model for a new task |
| LoRA | Low-Rank Adaptation: a small trainable update added to frozen weights |
| Rank (r) | Size of the LoRA update; 4,096 × r parameters per block here |
| Q, V | Query and value projections inside attention, where LoRA is added |
| Decoder | Turns features into the 6-class map (2,766,726 parameters) |
| DSS | Domain Sensitivity Score: standardised source–target feature distance per block |
| Depth prior | Fixed upside-down-U formula from setting 1; top 3: L14, L13, L15 |
| Fisher score | Label-based importance: how strongly the loss reacts to a block's LoRA |
| LogME | Label-based score of how well frozen features predict labels |
| GSD sensitivity | How much features change when a source image is resized to the target resolution |
| Screening gate | Four pre-set conditions a score had to meet to be used |
| Uniform LoRA | LoRA in all 24 blocks |
| Selective LoRA (K = 3) | LoRA in 3 chosen blocks |
| Budget match | Same number of LoRA parameters (98,304) |
| Seed | Starting number for randomness; same seed = same random choices |
| Paired comparison | Two methods compared on the same seed (same start, same data) |
| Validation set | Practice tests used during the study |
| Test set | Final exam, opened once |
| mIoU | Mean Intersection over Union across the 6 classes |
| Utility | mIoU gain over the same-seed decoder-only model |
| Spearman ρ | Rank correlation |
| Partial correlation | Correlation after removing the effect of another variable (depth) |
| Non-inferiority test | Tests "not worse by more than a margin" |
| Confidence interval | Plausible range for the true value |
| Bootstrap | Resampling the data many times to check stability |
| Pre-registration | Writing down the plan and analysis before seeing results |
| Hash | A digital fingerprint proving a file did not change |

---

# Formulas explained simply

## A. LoRA

W = W₀ + (α / r) · B · A

- W₀: frozen original weight. A, B: small trainable matrices. B starts at zero, so training begins from the original model.
- Parameters per block (Q and V): 2 × r × (1024 + 1024) = 4,096 × r → rank 8: 32,768; rank 1: 4,096.
- 3 blocks × 32,768 = 24 blocks × 4,096 = **98,304**.

## B. DSS — Domain Sensitivity Score

1. **Feature per image:** average the 196 patch tokens of block ℓ → f_ℓ(x).
2. **Source centroid:** average of source features, scaled to length 1 → c_ℓ.
3. **Raw drift:** D_ℓ = average over target images of (1 − cos(f_ℓ(t), c_ℓ)).
4. **Null baseline:** split source images into two random groups many times, compute the same distance → mean μ_ℓ and spread σ_ℓ.
5. **Score:** DSS_ℓ = (D_ℓ − μ_ℓ) / σ_ℓ. High = target is much further from source than source images are from each other.

## C. Depth prior

p(ℓ) = −1.8386×10⁻⁴ ℓ² + 4.9992×10⁻³ ℓ − 4.1343×10⁻⁴ — fitted on setting 1, never refitted.

## D. Screening gate

r_res = Spearman(score, z(Ū) − z(p)): does the score explain what the depth prior does not? Pass needs r_res ≥ 0.30, every leave-one-seed-out ≥ 0.15, tile-bootstrap 2.5th percentile ≥ 0, and top-3 regret ≤ the prior's.

## E. Metrics

- IoU_c = TP / (TP + FP + FN); mIoU = mean of the 6 class IoUs.
- Utility U(ℓ, s) = mIoU(ℓ, s) − mIoU(decoder only, s).

## F. Confirmatory test

- d_s = test mIoU(Prior-3, seed s) − test mIoU(Uniform r1, seed s), for 10 seeds.
- Mean ± t(9) × sd / √10 gives the 95% interval (t = 2.262).
- Pass if the lower bound > −0.010. Result: −0.0341, interval [−0.0392, −0.0291] → **not passed**.

---

# Important numbers to memorise

| Item | Value |
|---|---:|
| Prithvi backbone parameters | 303,886,336 |
| Transformer blocks | 24 (L0–L23) |
| Decoder parameters | 2,766,726 |
| Full fine-tuning parameters | ≈ 306.7M |
| LoRA per block, rank 8 / rank 1 | 32,768 / 4,096 |
| Equal budget (3 × r8 = 24 × r1) | 98,304 |
| Standard LoRA (24 × r8) | 786,432 |
| Comparison budget share of all parameters | ≈ 0.93% |
| Potsdam / Vaihingen tiles | 38 / 33 |
| Potsdam split (train / val / test) | 20 / 8 / 10 |
| Vaihingen split (train / val / test, locked) | 20 / 5 / 8 |
| Resolution Potsdam / Vaihingen | 5 cm / 9 cm |
| Total training runs | 217 (75 + 75 + 67) |
| Test-tile evaluations | 700 (70 models × 10 tiles) |
| Seeds | 1000–10000 (3 for single-block, up to 10 for main) |
| Training steps per run | 2,000 (batch of 8 crops, 224 × 224) |
| Highest memory peak | 10.35 GB of 16 GB |
| Setting 1 decoder-only mean val mIoU | 0.518 |
| Setting 1 best block | L16, +0.037 |
| Setting 2 decoder-only mean val mIoU | 0.569 |
| Setting 2 best block | L7, +0.052 |
| DSS vs utility / deeper-first / depth removed | 0.420 / 0.422 / 0.076 |
| DSS vs depth | ≈ 0.94 |
| Depth prior vs Potsdam utility | 0.533 |
| Val: uniform r1 / Prior-3 / Random-3 | 0.665 / 0.629 / 0.639 |
| Test: uniform r8 | 0.627 (+0.099) |
| Test: uniform r1 | 0.615 (+0.087) |
| Test: Random-3 | 0.590 (+0.062) |
| Test: Prior-3 | 0.581 (+0.053) |
| Test: Late-3 | 0.570 (+0.042) |
| Test: decoder only | 0.529 |
| Uniform r1 share of standard LoRA gain | 88% |
| C3 mean difference | −0.0341 |
| C3 95% interval | [−0.0392, −0.0291] |
| C3 margin | −0.010 |
| Seeds with selection worse | 10 / 10 |
| Tile bootstrap interval | [−0.0387, −0.0304] |

---

# Difficult questions the panel may ask

## 1. Your main hypothesis failed. What did you achieve?

We answered the research question clearly and reliably. We built a full block-utility map in both directions, showed that six scores do not reliably select blocks, and found a practical rule — spread a small LoRA rank over all blocks — that keeps 88% of standard LoRA's gain with one eighth of its LoRA parameters and beats selection at an equal budget on every seed.

## 2. Why should we trust a negative result?

Everything was frozen before it was tested; there was one confirmatory test; all comparisons are paired by seed and checked by hash; the effect is about five times the seed-to-seed noise; and the test set was opened once for frozen models. The ranking on validation and test was identical.

## 3. Did you look at the test set while designing the method?

No. The Potsdam test tiles were opened once, after all 70 models and the analysis script were frozen. Each test process could open only its own tile, and every result file records which files it opened. The Vaihingen test tiles were never opened at all.

## 4. Why not just choose the best blocks from the single-block study?

That uses validation labels to choose, which is what we wanted to avoid. Also, the best blocks changed between directions, and LogME — which found near-best single blocks — still did not beat random when the three blocks were trained together.

## 5. Why does uniform rank 1 work so well?

Every block helps on its own, so a method that leaves 21 of 24 blocks untouched gives up gains that a rank-1 update can collect cheaply. We did not test the deeper mechanism.

## 6. Is your conclusion general?

Not yet. It holds for Prithvi-EO-2.0-300M, the ISPRS city pair, LoRA on Q and V and our training recipe. That is why LoveDA and other backbones are in future work.

## 7. Why didn't you compare with full fine-tuning?

It did not fit in the 16 GB memory of our machine. We state this as a limitation and make no claim about it.

## 8. Why only 2,000 training steps?

It was fixed in the protocol for all runs to keep the hundreds of runs affordable. All methods got the same steps, so the comparison is fair, but longer training could change absolute numbers.

## 9. Why does DSS flip between directions?

DSS divides by how much source images vary at each block. When the source changes, that variation changes, and the ranking changes with it. This makes it unstable as a selector.

## 10. What is the practical recommendation for someone adapting Prithvi?

If you have a small LoRA budget, do not spend time choosing layers. Put a low rank on every block.

---

# Final advice for presenting

1. Do not memorise every sentence; understand the story and speak naturally.
2. On each slide, say **what question it answers** before showing numbers.
3. Point at the chart or table you are describing.
4. Say "aerial images", not "satellite images", for our data.
5. Never say high DSS means high usefulness.
6. Never claim we beat full fine-tuning — we did not test it.
7. Say "the hypothesis was not supported", not "the project failed".
8. Mention that the test set was opened **once** — examiners value this.
9. Keep the two numbers ready: **−0.034 on all 10 seeds** and **88% with 8× fewer parameters**.
10. If you do not know an answer, say what the experiments show and what is still untested.

**The one sentence you should remember above everything else:**

"Choosing which layers to adapt does matter, but no score we tested can choose them reliably — and with the same small budget, spreading LoRA thinly over every layer beat selecting layers on every seed."
