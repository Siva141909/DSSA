# DSSA — Complete Mid-Phase Review Presentation Script

**Presentation:** Domain Sensitivity-Guided Selective Adaptation for Remote Sensing Segmentation  
**Slides:** 7  
**Audience:** Faculty, HOD and students with little or no background in remote sensing or deep learning.

---

# Before the presentation: Understand the project in one simple story

Imagine that you teach a student to identify roads, buildings, trees and cars using photographs taken in one city.

The student learns what roads and buildings generally look like. Now imagine that you give the student photographs from another city, taken using a different camera, at a different resolution, under different conditions.

The student may still recognise many objects, but some objects may look different from what the student learned earlier. The student's performance may decrease.

This is similar to what happens with an AI model.

An AI model trained using images from one geographical area or sensor may not perform equally well when it receives images from another area or sensor.

This problem is called **domain shift**.

Our project investigates whether we can identify which internal layers of a large AI model are most affected by differences between two image domains.

Instead of updating the entire model, we investigate whether we can update only selected layers using a technique called **LoRA**.

We use a model called **Prithvi-EO-2.0**, which has 24 transformer blocks.

Our method calculates a score called the **Domain Sensitivity Score (DSS)** for each block. The score measures how different the model's internal representations are between the source and target images.

We initially expected that blocks showing larger representation differences might benefit more from adaptation.

However, our experiments did not support that hypothesis. The DSS ranking mostly followed the depth of the transformer blocks, and its selected blocks performed no better than random selections at the tested top-K values.

That negative result is important. It tells us that detecting a representation difference is not the same as identifying where adaptation will be useful.

Keep this distinction in mind throughout the presentation.

---

# Slide 1 — DSSA Mid-Phase Review

## What is displayed on the slide?

- DSSA: Domain Sensitivity-Guided Selective Adaptation.
- Remote sensing segmentation.
- Layer-wise adaptation utility in Prithvi-EO-2.0.
- Project team members.
- Project guide.
- Major Project Mid-Phase Review.

## What you should say

"Good morning, respected HOD, faculty members and everyone present.

Today, we are presenting the mid-phase progress of our major project, DSSA.

DSSA stands for Domain Sensitivity-Guided Selective Adaptation.

Our project is related to remote sensing and semantic segmentation.

Before going into the implementation, let me briefly explain the problem we are trying to study.

Suppose we train an AI model using aerial images from one geographical area. The model learns to identify objects such as buildings, roads, vegetation and cars.

Now, if we provide images captured from another geographical area using a different camera or at a different resolution, the appearance of those objects may change.

The model may not perform in the same way on those new images. This is one example of domain shift.

Our project investigates whether we can identify which internal layers of a pretrained AI model are more affected by this difference.

Instead of modifying the entire model, we study whether adapting only selected layers can be useful.

For this purpose, we use a foundation model called Prithvi-EO-2.0, which contains 24 transformer blocks.

We developed a score called the Domain Sensitivity Score to measure differences between the internal representations of source and target images.

Today, I will explain the datasets, architecture, experimental process, results and what we learned from those experiments."

## Explain the title

### Domain Sensitivity

Domain means the general environment or setting from which the data comes.

For example:
- Images captured over Potsdam form one domain.
- Images captured over Vaihingen form another domain.

Sensitivity means how strongly something responds to a change.

In our context, domain sensitivity refers to how much a model's internal representations differ between the source and target image domains.

### Selective Adaptation

Selective means choosing only some parts instead of changing everything.

Adaptation means adjusting a pretrained model so that it works better with a different target dataset.

Therefore, selective adaptation means choosing particular layers of the model for adaptation rather than adapting every layer.

### Remote Sensing

Remote sensing means collecting information about the Earth's surface without directly touching it.

Examples include:
- Satellite images.
- Aerial photographs captured from aircraft.
- Images collected using drones.

Our Potsdam and Vaihingen datasets are airborne aerial-image benchmarks.

### Segmentation

Segmentation means assigning a class to every pixel in an image.

For example, imagine an aerial image containing a road, buildings, trees and cars.

A segmentation model examines the image and assigns a class to each pixel.

The final result is a coloured map showing which pixels belong to which category.

## Likely questions

**Q1. What exactly is DSSA?**

DSSA is our research approach for investigating whether source-target representation differences can guide the selection of transformer layers for parameter-efficient adaptation.

**Q2. What is the main objective?**

To investigate whether a label-free representation-discrepancy score can identify layers that benefit more from adaptation.

**Q3. What is the difference between remote sensing and satellite imagery?**

Satellite imagery is one type of remote sensing. Remote sensing also includes aerial images captured from aircraft and drones.

**Q4. Why is this a mid-phase review?**

Because we are presenting the implementation completed so far, the experimental evaluation, the results and the remaining research work.

---

# Slide 2 — Domain Shift in Remote Sensing

This is one of the most important slides. Do not rush through it.

The audience should understand the actual problem before you discuss the model.

## 1. Start with a real-world situation

Say:

"Before explaining the model, let us understand the problem using a simple situation.

Imagine that we have an aerial image of a city. We train an AI model to identify buildings, roads, trees and cars.

The model learns patterns from these images.

Now imagine that we collect another aerial image of a different city.

The buildings may have different shapes. The roads may have different widths. The vegetation may look different. The image may also have been captured using another camera or at another resolution.

Even though both images contain the same types of objects, their visual appearance is different.

This difference between the data environments is called domain shift.

The important point is that the actual objects may remain the same, but their appearance in the images changes."

## 2. Why does domain shift happen more in remote sensing?

Explain that remote sensing images are collected under many different conditions.

### A. Different geographical locations

A residential area in one city may contain small houses and narrow roads.

Another city may contain large buildings, wide roads and different vegetation.

The objects belong to the same general categories, but their appearance and arrangement differ.

### B. Different sensors and cameras

Different imaging instruments may record the Earth's surface differently.

They can differ in:
- Spectral sensitivity.
- Image resolution.
- Radiometric response.
- Camera characteristics.
- Acquisition settings.

As a result, the same type of object may have different pixel values in two datasets.

### C. Different spatial resolution

Spatial resolution tells us how much ground area is represented by one pixel.

For example:
- A 5 cm resolution image represents approximately 5 cm of ground per pixel.
- A 9 cm resolution image represents approximately 9 cm of ground per pixel.

The 5 cm image can show finer spatial details than the 9 cm image.

### D. Different seasons and environmental conditions

Vegetation can look different during different seasons.

The same agricultural field may look green during one period and dry during another.

Lighting, shadows and atmospheric conditions can also affect the image.

### E. Different acquisition campaigns

An acquisition campaign is a particular data-collection operation or survey.

Images collected during different campaigns may have different cameras, flight conditions, dates and processing characteristics.

**Important:** These are general reasons why remote sensing domain shift occurs. Do not claim that every one of these differences was separately measured in our Potsdam-Vaihingen experiment.

## 3. Explain the two datasets

Point to the left and right sides of the slide.

### Left side: Potsdam — Source Dataset

Say:

"On the left, we have the ISPRS Potsdam dataset.

We use Potsdam as our source dataset.

It contains aerial images with approximately 5 centimetres of ground resolution.

We use all 38 Potsdam tiles for two purposes: fitting the fixed radiometric preprocessing transformation and building the source-versus-source baseline.

However, the source reference used for the primary DSS R2 calculation is computed from only 16 Potsdam tiles, specifically the first 16 tiles in sorted order.

So, although all 38 tiles contribute to preprocessing and the baseline, only 16 are used to calculate the DSS source centroid.

We use the images, not Potsdam segmentation labels, to calculate this source representation reference."

### Right side: Vaihingen — Target Dataset

Say:

"On the right, we have the ISPRS Vaihingen dataset.

We use Vaihingen as our target dataset.

Its images have approximately 9 centimetres of ground resolution.

We use 33 image tiles from this dataset.

Unlike Potsdam, Vaihingen is also the dataset on which we train and evaluate our segmentation model.

We use labelled Vaihingen training tiles to train the decoder and selected LoRA parameters.

We use separate validation tiles to measure adaptation utility."

## 4. What exactly is a tile?

A tile is a smaller image section of a larger geographical area.

Imagine taking a large aerial photograph of an entire city and dividing it into smaller square pieces.

Each smaller piece is called a tile.

Why do we use tiles?

Because processing one enormous image at once would require a lot of memory and computation.

Dividing it into tiles allows us to:
- Process smaller image sections.
- Manage memory.
- Prepare training samples.
- Maintain separate training, validation and test regions.

In our experiment:
- Potsdam: 38 image tiles.
- Vaihingen: 33 image tiles.

These numbers represent image tiles, not the number of pixels and not the number of classes.

## 5. Explain the six semantic classes

Both datasets use six semantic classes.

| Class | Simple meaning |
|---|---|
| Impervious surfaces | Roads, pavements and other hard surfaces |
| Building | Houses, offices and other buildings |
| Low vegetation | Grass, small plants and low vegetation |
| Tree | Individual trees and tree-covered areas |
| Car | Cars and similar vehicles |
| Clutter/background | Objects or areas that do not fit the other defined classes |

Explain with an example:

"Imagine looking at an aerial photograph of a residential area.

The road pixels belong to impervious surfaces.

The house pixels belong to building.

The grass around the house belongs to low vegetation.

Large trees belong to the tree class.

Visible cars belong to the car class.

Other difficult or unclassified objects are assigned to the clutter/background category according to the dataset annotation scheme."

**Important:** These are semantic labels assigned to image pixels. They are not six separate image files.

## 6. Explain the images in the two frames

If the placeholders have been replaced with actual Potsdam and Vaihingen crops, say:

"These two images are actual crops from the datasets used in our project.

The left image comes from Potsdam, our source dataset.

The right image comes from Vaihingen, our target dataset.

We selected comparable areas so that we can observe differences in the visual appearance of the two domains.

Look at the structures, buildings, roads, vegetation and overall image texture.

Even when both images contain similar types of objects, the way those objects appear can differ.

That is the type of visual difference we want to study."

### Why should both crops cover the same ground area?

Because the two datasets have different spatial resolutions.

If we compare the same number of pixels from both datasets, they represent different ground areas.

For a 50 m × 50 m area:

- Potsdam at 5 cm per pixel needs approximately 1,000 × 1,000 pixels.
- Vaihingen at 9 cm per pixel needs approximately 556 × 556 pixels.

Both crops represent the same physical ground area.

We display them at the same size on the slide.

This helps the audience compare the images without accidentally comparing different geographical footprints.

### What does IRRG mean?

IRRG means:
- I: Infrared, specifically near-infrared imagery in this dataset.
- R: Red.
- G: Green.

These are three image bands.

A normal RGB photograph uses:
- Red.
- Green.
- Blue.

An IRRG image instead contains:
- Infrared.
- Red.
- Green.

When we display IRRG as a three-channel image, we map the infrared band to the display's red channel, the red band to the green display channel, and the green band to the blue display channel.

This creates a false-colour image.

### Why does vegetation appear red?

Healthy vegetation reflects a relatively high amount of near-infrared radiation.

Since the near-infrared band is displayed in the red channel, vegetation often appears red or reddish in an IRRG image.

This is not the actual colour of the vegetation.

It is a display representation of infrared information.

Say:

"So, when you see red vegetation in these images, it does not mean the trees or grass are actually red. It means that the near-infrared band has been mapped to the red display channel."

### Where exactly is the domain shift visible?

Do not claim that every visible difference is caused by one specific sensor.

Instead, explain:

"We can observe differences in spatial detail, image texture, object appearance and colour response.

These differences are evidence that the two image collections do not have identical visual characteristics.

However, a visual comparison alone does not tell us which transformer layer will benefit from adaptation. That is what our experiments investigate."

## 7. Explain the comparison table

### Classes: Six ISPRS classes

Both datasets have the same six semantic categories.

Why is that useful?

Because we want to study changes in image representation without changing the basic segmentation task.

If one dataset had different classes, it would become difficult to separate domain differences from differences in the task itself.

### Ground resolution: 5 cm versus 9 cm

Potsdam has approximately 5 cm ground resolution.

Vaihingen has approximately 9 cm ground resolution.

A smaller ground distance per pixel means finer spatial detail.

This does not mean the 5 cm image is automatically better for every task. It means it represents the ground at a finer spatial scale.

### Acquisition: Different acquisition campaign

The two datasets were collected in different acquisition campaigns.

This means the image collections do not come from the same survey.

Do not claim a specific camera model or acquisition date unless you have verified it from the official dataset documentation.

### Tiles used here: 38 versus 33

We use 38 Potsdam tiles and 33 Vaihingen tiles.

The 33 Vaihingen tiles are split into training, validation and locked test groups, which we will explain on Slide 4.

## 8. Explain the domain-shift statement

The slide says:

"Domain differences can affect how well a model transfers across locations and sensors."

Explain:

"Transfer means using a model on data that is different from the data it originally learned from.

If the model performs well on one dataset but performs poorly on another, that indicates a transfer problem.

Our project studies this type of situation.

However, we did not run a separate source-trained segmentation evaluation to measure the exact performance drop from Potsdam to Vaihingen. So this sentence explains the general problem, not a measured performance drop from our experiment."

## 9. Explain trainable parameters

The slide compares:

- Full fine-tuning: 306.7 million trainable parameters.
- K = 1 selective LoRA: 2.80 million trainable parameters.
- Approximately 0.91% of all model parameters.

First explain what a parameter is.

A parameter is a numerical value inside a neural network that the model learns during training.

A neural network contains many such values.

During training, the model updates selected parameter values to improve its predictions.

### What are trainable parameters?

Trainable parameters are the numerical values that are allowed to change during training.

Frozen parameters are kept fixed.

### Full fine-tuning

In full fine-tuning, we allow the pretrained backbone and decoder to update.

Our approximate parameter count is:

- Prithvi backbone: 303.9 million.
- Decoder: 2.77 million.
- Total: approximately 306.7 million trainable parameters.

### Selective LoRA with K = 1

K means the number of transformer blocks selected for adaptation.

K = 1 means we select one transformer block.

We use LoRA with:
- Rank 8.
- Query projection.
- Value projection.

This adds 32,768 trainable LoRA parameters to one block.

The decoder also remains trainable.

Therefore:

2,766,726 decoder parameters + 32,768 LoRA parameters = 2,799,494 trainable parameters.

Approximately 2.80 million.

That is about 0.91% of the total model parameter count used in the comparison.

### What is LoRA?

LoRA stands for Low-Rank Adaptation.

Instead of updating a large existing weight matrix directly, LoRA introduces smaller trainable matrices that modify its behaviour.

Imagine a large machine that already works reasonably well.

Instead of rebuilding the entire machine, we add a small adjustable component that changes how it behaves.

That is the basic idea behind LoRA.

### What are Q and V?

In a transformer, attention helps the model decide which information is important when processing tokens.

The three common projections are:

- Q: Query — what information am I looking for?
- K: Key — what information is available?
- V: Value — what information should be passed forward?

Our implementation applies LoRA to the Query and Value projections.

We do not apply LoRA to every projection.

### What does K = 1 mean in the slide?

It means one transformer block receives LoRA.

The decoder is still trainable.

The other backbone parameters remain frozen.

### Important limitation

The parameter count shows that K = 1 has fewer trainable parameters than full fine-tuning.

It does not prove that K = 1 gives equal or better segmentation performance.

We have not completed the uniform-LoRA and full-fine-tuning comparisons needed to make that claim.

Say:

"This comparison explains the parameter-count difference. It does not yet establish that our selective method is more efficient in terms of accuracy, training time or final performance."

## 10. Explain the research question

The slide asks:

"Can source-target representation differences help identify which transformer layers benefit from adaptation?"

Break it down.

- Source: Potsdam.
- Target: Vaihingen.
- Representation: the numerical features produced inside the neural network.
- Difference: how those features change between the two datasets.
- Transformer layers: the 24 blocks inside Prithvi.
- Benefit from adaptation: whether updating a particular block improves validation segmentation performance.

The actual question is:

"If a particular transformer block produces very different internal features for Potsdam and Vaihingen, does updating that block improve the segmentation result?"

That is the central question of DSSA.

## 11. Explain related work

The slide mentions SPECTRA and CrossEarth-Gate.

Say:

"We also studied related research.

SPECTRA investigates stage-wise adaptation and LoRA allocation for Prithvi-EO-2.0.

CrossEarth-Gate investigates selecting modules using task-related training information, such as gradient or Fisher-related signals.

These works are relevant because they also investigate where adaptation should happen.

Our research question is different in the signal we test: can we use source-target representation discrepancy, measured before adaptation and without labels, to guide layer selection?"

Do not say that nobody has ever used layer-wise discrepancy. Earlier research, including Deep Domain Confusion, has already studied layer-wise domain discrepancy.

## Likely questions — Slide 2

**Q1. Why did you choose Potsdam and Vaihingen?**

They provide two ISPRS aerial-image domains with the same six semantic classes but different image resolutions and acquisition characteristics. This allows us to investigate representation differences while keeping the segmentation categories consistent.

**Q2. Why is Potsdam the source and Vaihingen the target?**

Our experimental protocol defines Potsdam as the reference domain for source representations. Vaihingen is the target domain used for the supervised segmentation training and validation.

**Q3. Why not use the labels from Potsdam?**

Our DSS calculation uses image representations, not Potsdam segmentation labels. The segmentation model is trained using labelled Vaihingen training tiles.

**Q4. Are these satellite images?**

They are airborne aerial images. Both belong to remote sensing, but they are not satellite imagery.

**Q5. What does 5 cm resolution mean?**

It means one pixel represents approximately 5 centimetres of ground distance.

**Q6. Why do we use the same six classes?**

It keeps the semantic segmentation task consistent across the two datasets.

**Q7. What is the difference between an image and a tile?**

An image is the visual data. A tile is a defined image section representing a particular geographical area.

**Q8. Does red vegetation mean the vegetation is actually red?**

No. IRRG is false-colour imagery. Near-infrared information is displayed through the red channel, which makes vegetation appear red.

**Q9. Does the visual difference prove domain shift?**

It demonstrates visual differences between the datasets. Our DSS analysis examines differences in the model's internal representations. A visual comparison alone does not establish adaptation utility.

**Q10. Why are we comparing trainable parameters?**

To show how many model parameters are allowed to change under different adaptation approaches. However, a smaller parameter count alone does not prove better efficiency or accuracy.

---

# Slide 3 — Implemented DSSA Architecture

This slide explains the actual architecture we implemented.

It contains two main paths:

A. DSS layer selection.

B. Target segmentation training.

Explain these separately.

## Start with the big picture

Say:

"This slide explains how our implemented system works.

We divide the process into two paths.

The first path identifies which transformer blocks have higher source-target representation discrepancy.

The second path trains the segmentation model using labelled target data and LoRA in selected blocks.

The first path calculates DSS before adaptation training. The second path performs supervised segmentation training."

## Path A — DSS layer selection

### Step 1: Potsdam + Vaihingen images

The first box contains Potsdam and Vaihingen images.

Explain:

"We take images from both datasets.

For calculating DSS, we do not need their segmentation labels. We only need the images.

The purpose is to understand how the frozen model represents the source and target image domains."

### Step 2: Fixed preprocessing

The next box says:

"Fixed preprocessing — radiometric transform, band mapping."

Explain preprocessing first.

Preprocessing means preparing the raw images so that they can be supplied consistently to the model.

Our datasets use IRRG images, while Prithvi expects a particular multispectral input structure.

We therefore need to map the available bands into the model's expected input format.

In our implementation:

- Infrared is mapped to the model's narrow-NIR input.
- Red is mapped to the red input.
- Green is mapped to the green input.
- Unavailable Blue, SWIR1 and SWIR2 bands are zero-filled in normalized space.
- We use one temporal observation, T = 1.

We also apply a fixed radiometric transformation.

Radiometric transformation means adjusting the numerical pixel-value scale so that the inputs follow a consistent representation.

The transformation was fitted using Potsdam source data and then frozen.

Why is it fixed?

Because we do not want preprocessing to change independently during the experiment.

A fixed preprocessing pipeline helps make comparisons between source and target more controlled.

### Step 3: Frozen Prithvi-EO-2.0-300M

The diagram shows:

"Frozen Prithvi-EO-2.0-300M: features read from all 24 blocks."

Explain what Prithvi is.

Prithvi-EO-2.0 is a geospatial foundation model developed for Earth-observation data.

A foundation model is a model pretrained on a large amount of data so that it learns useful general representations before being adapted to a particular task.

Our selected checkpoint contains approximately 303.9 million parameters.

It has 24 transformer blocks.

### What is a transformer block?

Think of a transformer block as one processing stage inside the model.

The input image is converted into numerical representations called tokens.

Each block processes those representations and produces new representations.

As the information moves through the blocks, the model builds increasingly complex features.

Early blocks may capture relatively basic patterns.

Later blocks may represent more complex combinations of information.

This is a simplified explanation. It does not mean every block has one fixed visual responsibility.

### Why is the backbone frozen?

Frozen means its pretrained parameters are not updated during the DSS calculation.

We want to observe how the same pretrained model represents Potsdam and Vaihingen.

If we trained the model first, the representations would already have changed due to training.

Freezing the backbone allows us to examine its existing representations before adaptation.

### Step 4: DSS per block

This is the main part of our method.

The model contains 24 blocks.

We extract features from each block.

Then we compare the source and target representations.

Explain the calculation in simple terms:

"Imagine that a particular block produces numerical feature vectors for the 16 Potsdam source tiles used by the primary DSS R2 calculation.

We calculate a reference centre, the source centroid, from those source features.

For the primary DSS R2 calculation, we use five Vaihingen probe tiles. These five tiles are also part of the 20 training tiles.

We pass their images through the frozen Prithvi model and extract representations from each transformer block.

We then measure how far the features of these five Vaihingen probe tiles are from the Potsdam source centroid.

We use the images only for this DSS calculation. We do not use their segmentation labels to calculate DSS.

We use cosine distance to measure the difference in direction between feature vectors.

We also standardise this difference using a source-versus-source baseline.

This gives us a score for that block."

### What is a feature?

A feature is a numerical representation produced by the neural network.

A normal image contains pixels.

A neural network transforms the input into numerical representations that capture patterns useful for processing.

### What is a centroid?

A centroid is the average or central reference point of a collection of numerical vectors.

Imagine a group of students standing in a playground.

If we calculate their average position, we get a central point.

That is the basic idea of a centroid.

In our experiment, the source centroid is calculated from source feature representations.

### What is cosine distance?

Cosine similarity compares the direction of two vectors.

Cosine distance expresses how different those directions are.

A larger cosine distance generally means the vectors point in less similar directions.

We use it to measure representation differences.

### What does standardisation mean here?

A raw difference alone may be difficult to interpret.

We compare the source-target discrepancy against a source-versus-source reference.

This helps us understand whether the target difference is large relative to the variation already present within the source dataset.

### What does a high DSS mean?

A high DSS means the target representations differ more from the source reference for that block, relative to the chosen baseline.

It does not automatically mean that the block will benefit more from adaptation.

This distinction becomes important when we discuss the results.

### Step 5: Rank blocks and keep Top-K

The diagram gives an example:

"K = 2: L22, L19."

Explain:

"We calculate a score for each of the 24 blocks.

Then we rank the blocks according to their DSS values.

Top-K means selecting the K blocks with the highest scores.

For example, if K equals 2, we select the two highest-scoring blocks.

In this example, those are L22 and L19."

Clarify:

- L0 means the first transformer block.
- L23 means the final transformer block.
- There are 24 blocks in total, numbered from 0 to 23.
- K = 2 means two blocks are selected.

**Important:** This is an example of the DSS selection path. Our Phase 2D validity study tested every block independently using K = 1. Do not confuse the diagram's K = 2 example with the main Phase 2D experiment.

## Path B — Target segmentation training

Now move to the lower half of the slide.

Say:

"After selecting blocks, we move to the training path.

Here, we use labelled Vaihingen training tiles."

### Step 1: Labelled Vaihingen training tiles

We use 20 training tiles.

Five of these also form the probe set used in DSS checks.

The labels provide the correct class for each pixel.

For example, the model predicts that a pixel belongs to a building.

The ground-truth label tells us whether that prediction is correct.

### Step 2: Frozen backbone + LoRA

The diagram shows:

"Frozen backbone · LoRA r = 8 on Q/V only in the selected blocks."

Explain:

"We keep the original Prithvi backbone frozen.

We add LoRA modules only to the selected transformer blocks.

The LoRA rank is 8.

The LoRA modules are attached to the Query and Value projections.

This means the pretrained backbone mostly remains unchanged, while a relatively small number of additional parameters can be trained."

### What does rank 8 mean?

LoRA approximates a large weight update using smaller low-rank matrices.

The rank controls the size of this low-rank update.

Rank 8 means we use a low-rank representation with rank 8.

It is not the number of selected transformer blocks.

### Step 3: Decoder

The slide shows a trainable decoder.

Explain:

"The backbone extracts useful representations from the input image.

But those representations are not yet the final six-class segmentation map.

We need a decoder to convert the extracted features into pixel-level class predictions.

The decoder is the task-specific part of the model.

It is trained using labelled Vaihingen training data."

### Why is the decoder trainable?

Because we need the model to learn how to convert its pretrained features into the six segmentation classes required by our task.

The decoder has approximately 2.77 million parameters.

### Step 4: Six-class map

The diagram shows a small six-class map marked illustrative.

Explain:

"The decoder produces a segmentation map.

Each pixel receives one of the six class labels.

The small coloured map shown here is illustrative. It is not a prediction produced by our trained model."

This distinction is important.

## What is the difference between Path A and Path B?

Path A:
- Uses images without segmentation labels.
- Calculates DSS.
- Ranks transformer blocks.
- Selects candidate blocks before adaptation.

Path B:
- Uses labelled Vaihingen training images.
- Trains LoRA and the decoder.
- Produces segmentation predictions.

The first path decides which blocks to investigate.

The second path measures what happens when those blocks are adapted.

## Important scientific distinction

The architecture is based on the hypothesis that high representation discrepancy might identify useful adaptation locations.

But our results show that this hypothesis did not hold in the tested configuration.

A high DSS score means more representation discrepancy, not proven adaptation benefit.

## Likely questions — Slide 3

**Q1. Why do we use a frozen backbone for DSS?**

To measure the source-target representation difference before adaptation changes the pretrained model.

**Q2. Why do we need 24 DSS scores?**

Because we want to compare representation discrepancy at every transformer block and investigate whether some blocks are more sensitive than others.

**Q3. What does L23 mean?**

It is the 24th transformer block, because indexing begins at zero.

**Q4. Why use cosine distance?**

It measures differences in vector direction and provides a way to compare high-dimensional feature representations.

**Q5. What is the difference between DSS and accuracy?**

DSS measures representation discrepancy. Accuracy or mIoU measures segmentation performance. They answer different questions.

**Q6. Does high DSS guarantee high adaptation utility?**

No. Our experiments show that the DSS-selected blocks were not better than random selections at the tested top-K values.

**Q7. Why use LoRA on Q and V?**

It provides a limited, parameter-efficient way to modify the attention projections without updating the entire backbone.

**Q8. What is the role of the decoder?**

It converts the backbone's feature representations into six-class pixel-level segmentation predictions.

**Q9. Does the small map show our actual prediction?**

No. It is illustrative only.

**Q10. Is the complete architecture trained end-to-end?**

The backbone remains frozen. The decoder and selected LoRA parameters are trained.

---

# Slide 4 — Dataset and Experimental Methodology

This slide explains exactly how we divided the datasets and how we measured representation discrepancy and adaptation utility.

## 1. Source dataset

The slide says:

"Source: ISPRS Potsdam IRRG · 38 tiles · images only, used for DSS."

Say:

"We use all 38 Potsdam tiles for two purposes: fitting the fixed radiometric preprocessing transformation and building the source-versus-source baseline.

However, the source reference used for the primary DSS R2 calculation is computed from only 16 Potsdam tiles, specifically the first 16 tiles in sorted order.

So, although all 38 tiles contribute to preprocessing and the baseline, only 16 are used to calculate the DSS source centroid.

The Potsdam segmentation labels are not used to train our decoder or calculate DSS."

Why?

Because our DSS signal is intended to use image representations rather than source segmentation labels.

## 2. Target dataset

The slide says:

"Target: ISPRS Vaihingen IRRG · 33 tiles, split locked before training."

Say:

"We use 33 Vaihingen tiles as our target dataset.

Before running the experiments, we divided these tiles into training, validation and test groups.

We fixed this split in advance so that the experimental roles of the tiles would not change during the evaluation."

## 3. Explain the split

The slide shows:

- 15 train.
- 5 train + probe.
- 5 validation.
- 8 test (locked).

Explain carefully:

"The 33 Vaihingen tiles are divided into three main groups.

First, we have 20 training tiles.

These 20 tiles consist of 15 training-only tiles and five tiles that also form the probe set.

Second, we have five validation tiles.

Third, we have eight locked test tiles."

Check the total:

15 + 5 + 5 + 8 = 33.

### What is training data?

Training data is used to teach the model.

In our case, the labelled Vaihingen training tiles are used to train the decoder and LoRA parameters.

### What is the probe set?

The probe set is a subset of five training tiles used in the DSS checks.

It is not a separate group outside the 20 training tiles.

These five tiles are also part of the training group.

This is why the slide says "5 train + probe."

### What is validation data?

Validation data is used to measure how well the model performs during experimentation.

We use the five validation tiles to calculate segmentation metrics and adaptation utility.

The validation set is not used to update model parameters.

### What is test data?

Test data is intended for final evaluation after model and experimental choices are complete.

Our eight test tiles remained locked.

They were not opened or used in the Phase 2D experiments.

Why keep test data locked?

Because if we repeatedly inspect test results while changing the method, we can indirectly tune the method to the test set.

That would make the final evaluation less trustworthy.

Say:

"We protected the eight test tiles throughout this experiment. Our integrity audit confirmed that none of the eight test tiles was opened across the 82 audit records."

## 4. Explain the training, validation and test difference using an example

Imagine preparing for an examination.

- Training data is like the textbook and practice exercises used to learn.
- Validation data is like practice tests used to check progress and compare approaches.
- Test data is like the final examination, which should not be used while preparing the method.

This is not a perfect technical analogy, but it helps explain why the three groups must remain separate.

## 5. Explain what DSS measures

The slide contains a diagram with:

- Source centroid.
- Potsdam features.
- Vaihingen features.

Say:

"This diagram explains the calculation behind DSS.

We pass Potsdam and Vaihingen images through the frozen Prithvi model.

For each transformer block, we extract feature representations.

We calculate a source centroid using the Potsdam feature representations of the first 16 Potsdam tiles.

For the primary DSS R2 calculation, we use five Vaihingen probe tiles. These five tiles are also part of the 20 training tiles.

We then measure the average cosine distance of the features of these five Vaihingen probe tiles from the Potsdam source centroid.

We use the images only for this DSS calculation. We do not use their segmentation labels to calculate DSS.

We standardise this difference using a source-versus-source baseline.

This gives us the DSS value for that block."

**Important distinction:**

- 33 Vaihingen tiles belong to the complete dataset.
- 20 belong to the training group.
- Five of those 20 are also used as the DSS probe set.
- The primary DSS R2 calculation uses those five probe tiles, not all 33 Vaihingen tiles.

### What is source-versus-source?

We compare variation within the source dataset against the source-target difference.

For example, Potsdam images may naturally differ from one another.

We should not interpret every difference between Potsdam and Vaihingen as meaningful domain discrepancy without considering this natural source variation.

The source-versus-source baseline gives us a reference for that comparison.

### What does higher DSS mean?

The slide says:

"Higher = that block's representation shifts more."

Explain:

"A higher DSS means that the target feature representations are more different from the source reference for that block.

It does not mean that the block has lower accuracy.

It does not mean that adapting that block will necessarily improve the result."

## 6. Explain the experimental setting

The slide says:

"Target-supervised segmentation with unsupervised source-target representation-discrepancy-guided layer selection."

This sentence is important because it describes exactly what we did.

Break it down.

### Target-supervised segmentation

We use labelled Vaihingen training tiles to train the segmentation model.

The model learns from target-domain labels.

### Unsupervised source-target representation discrepancy

For DSS calculation, we use images without segmentation labels.

We compare source and target feature representations.

### Layer selection

We use the DSS values to rank transformer blocks.

The intended purpose is to select which blocks to adapt.

### Why is this not conventional unsupervised domain adaptation?

Because the target segmentation model is trained using labelled Vaihingen data.

Only the layer-selection signal is label-free.

Do not describe the complete training pipeline as unsupervised domain adaptation.

Say:

"Our setup is target-supervised segmentation with unsupervised representation-discrepancy-guided layer selection."

## Likely questions — Slide 4

**Q1. Why do we need separate training, validation and test datasets?**

To train the model, compare experimental configurations and preserve an independent final evaluation set.

**Q2. Why does the probe set overlap with training?**

The five probe tiles are a subset of the 20 training tiles. Their images (not labels) are the Vaihingen input to the primary DSS R2 calculation. They are not an additional independent test set.

**Q3. Why did you not use the eight test tiles?**

To preserve an untouched final evaluation set and prevent information leakage into experimental decisions.

**Q4. How many Vaihingen tiles are used for training?**

Twenty tiles, including the five train/probe tiles.

**Q5. How many validation tiles are used?**

Five.

**Q6. How many test tiles are used?**

Eight, and they remain locked and unopened.

**Q7. Are Potsdam labels used?**

No. The Potsdam images are used for source representations in DSS.

**Q8. Are Vaihingen labels used?**

Yes. Training labels are used to train the decoder and LoRA. Validation labels are used to measure utility.

**Q9. What does higher DSS mean?**

Greater source-target representation discrepancy relative to the chosen baseline. It does not directly indicate adaptation benefit.

**Q10. Why call the layer-selection signal unsupervised?**

Because DSS is calculated from images without using segmentation labels.

**Q11. Is the entire method unsupervised?**

No. The segmentation training is supervised using labelled Vaihingen training tiles.

---

# Slide 5 — Experiments Completed and Results

This is the most important evidence slide.

Explain the experimental process first, then the graph, then the correlation.

Do not jump directly to the conclusion.

## 1. Explain the 75 completed runs

The slide says:

"75 completed runs — 12 pilot + 63 oracle · 3 seeds · 2,000 steps each."

Say:

"After completing the preprocessing, model verification and DSS protocol, we performed a layer-utility experiment.

We have 75 completed runs in this Phase 2D study.

These consist of 12 pilot runs and 63 additional oracle runs.

Each run was trained for 2,000 steps.

We used three random seeds to examine how results change when the training randomness changes."

### What is a run?

A run is one execution of the training experiment using a particular configuration and random seed.

### What is a seed?

Training includes random operations such as parameter initialization and data ordering.

A random seed controls these operations so that an experiment can be repeated under a defined random setup.

Using multiple seeds helps us understand whether an observed result is consistent or depends heavily on randomness.

### What do seed 1000, seed 2000 and seed 3000 mean?

A seed is just a starting number for the random number generator. If you give the same seed, the computer produces exactly the same sequence of "random" choices again. If you give a different seed, it produces a different sequence.

The numbers 1000, 2000 and 3000 have **no special meaning**. They are simply three different labels. 1000 was the default training seed fixed in the Phase 2C protocol, and 2000 and 3000 were added in Phase 2D to get two more independent repeats.

In our training, the seed controls three things:

| What the seed controls | What it means in our experiment |
|---|---|
| Starting weights of the decoder | The decoder begins from slightly different random weights for each seed |
| Starting weights of LoRA (matrix A) | LoRA's A matrix is drawn from a separate generator (seed + 7,000,000); matrix B always starts at zero |
| The training data stream | Which training tile is picked, where the 224 × 224 crop is cut, and which flips/rotations are applied, for all 2,000 steps × 8 crops |

What the seed does **not** change: the frozen Prithvi backbone, the dataset split, the learning rate, the number of steps and the validation tiles. These are identical for every run.

**Why the same seed matters (paired comparison):**

For a given seed, the K = 0 baseline and every K = 1 block run start from the **same decoder weights** and see the **same crops in the same order**. The only difference is where LoRA is added. So when we compute

utility = mIoU(block ℓ, seed 1000) − mIoU(K = 0, seed 1000),

the difference comes from the LoRA block, not from luck in initialisation or data order. We verified this before every run by checking hashes of the starting decoder, LoRA A and the data stream.

**Why three seeds (repeats):**

Running the same setup with seeds 1000, 2000 and 3000 shows how much results move just because of randomness. For example, the K = 0 baseline scored 0.5264, 0.5194 and 0.5084, a spread of about 0.018 mIoU. A block's improvement is only convincing if it is clearly larger than this kind of variation, which is why we report the mean of the 3 seeds.

**Simple analogy:** think of a seed as the order in which a shuffled deck of cards is dealt. Seed 1000 is one particular shuffle. Every configuration trained with seed 1000 gets the same shuffle, so they can be compared fairly. Seeds 2000 and 3000 are two other shuffles, used to check that the conclusion does not depend on one lucky shuffle.

**Not to be confused with:** seed 1234 in the DSS formulas. That seed only fixes the 40 random 8-vs-8 shuffles used for the DSS null baseline; it has nothing to do with training.

### What is a training step?

A training step is one update of the model's trainable parameters using a batch of training data.

Each run completed 2,000 such steps.

### What does pilot mean?

A pilot experiment is an initial, smaller experiment used to check the setup and examine preliminary behaviour.

Our pilot covered:
- Decoder-only baseline K = 0.
- Layer L0.
- Layer L12.
- Layer L23.

Each configuration was run with three seeds.

That gives 12 pilot runs.

### What does oracle mean here?

The oracle study evaluates the utility of individual transformer blocks using labelled validation data.

We trained the remaining 21 blocks independently with three seeds each.

21 × 3 = 63 additional runs.

The term oracle is used because this evaluation uses validation labels to measure which block actually helped.

This does not mean the oracle is a deployable label-free selection method.

## 2. Explain the experimental timeline

### Phase 1 — Verification

We verified the pretrained checkpoint, preprocessing and dataset integrity.

We confirmed that the backbone remained frozen.

### Phase 2A–B — DSS, split and protocol

We examined DSS behaviour and fixed the target split and experimental protocol.

### Phase 2C — First batch of a planned 39-run training matrix

Phase 2C was the first batch of five runs from a planned 39-run training matrix.

The five completed runs were:

1. K = 0: decoder-only baseline.
2. DSSA K = 2: two blocks selected using DSS.
3. Early K = 2: two early transformer blocks.
4. Late K = 2: two late transformer blocks.
5. Lowest-DSS K = 2: two blocks with the lowest DSS scores.

These five runs belong to Phase 2C. They are separate from the 75 Phase 2D pilot and oracle runs.

What to say during the presentation:

"Before the Phase 2D study, we had already started a separate Phase 2C training matrix. We completed its first five runs, covering a decoder-only baseline and four K = 2 selection strategies.

The Phase 2C matrix was planned for 39 runs, but only the first five were completed in that batch. These results should not be mixed with the 75 runs from Phase 2D, which form our main individual-layer utility study."

### Phase 2D — Layer-utility study

We tested individual transformer blocks.

We wanted to measure whether the layers selected by DSS actually improved segmentation performance.

## 3. Explain the first graph — Mean adaptation utility per block

The graph shows the average utility of each of the 24 transformer blocks.

The horizontal axis shows the block number:

L0, L1, L2, ... L23.

The vertical axis shows the adaptation utility.

### What is adaptation utility?

We compare the validation mIoU of a layer-adapted run against the decoder-only K = 0 baseline using the same seed.

The calculation is:

Utility = Layer-adapted validation mIoU − Same-seed K = 0 validation mIoU.

For example:

If the decoder-only baseline has validation mIoU of 0.52 and a layer-adapted run has 0.55, the utility is:

0.55 − 0.52 = +0.03.

This means the adapted configuration improved validation mIoU by 0.03 compared with the baseline.

If the utility is negative, the adapted configuration performed worse than the baseline.

### What is mIoU?

mIoU stands for mean Intersection over Union.

It is a common metric used for semantic segmentation.

For one class, Intersection over Union compares:

- The pixels correctly predicted as that class.
- The total area covered by the predicted and ground-truth regions for that class.

In simple terms:

It measures how much the predicted region overlaps with the correct region.

We calculate IoU for each of the six classes and take the mean.

Higher mIoU generally means better segmentation overlap.

### Explain the graph's key observations

Say:

"Here, we can see that adaptation utility is not equal across all transformer blocks.

Some blocks provide better validation improvements than others.

The strongest mean utility is observed at L16, with approximately +0.0372.

The gains are generally concentrated around the middle blocks, particularly L11 to L17.

L0 has a slightly negative mean utility of approximately -0.0073.

L23 has a mean utility of approximately +0.0146."

### What does this tell us?

It suggests that the choice of transformer block matters in this experimental configuration.

However, three seeds and five validation tiles are not enough to make strong generalisation claims.

The uncertainty around individual layer estimates is substantial.

The median 95% interval half-width is approximately 0.034.

Therefore, we should not claim that every neighbouring block has a reliably different utility.

## 4. Explain the second graph — Does DSS predict utility?

The graph compares two things:

1. How well DSS ranking correlates with adaptation utility.
2. How well a simple late-layer rule correlates with adaptation utility.

### What is correlation?

Correlation measures how two quantities vary together.

If two values tend to increase together, their correlation is positive.

If one increases while the other decreases, their correlation is negative.

### What is Spearman correlation?

Spearman correlation measures whether the ranking of one variable is associated with the ranking of another.

It is useful here because DSS produces a ranking of transformer blocks.

A value close to +1 indicates a strong positive ranking relationship.

A value near zero indicates little monotonic ranking relationship.

A negative value indicates an inverse ranking relationship.

### DSS R2: 0.420

The DSS ranking has a Spearman correlation of approximately 0.420 with adaptation utility.

This indicates a moderate positive ranking association in the observed data.

However, we cannot stop here.

We need to ask whether DSS provides information beyond simply preferring deeper transformer blocks.

### Late-layer rule: 0.422

A simple rule that ranks deeper blocks higher has a correlation of approximately 0.422 with adaptation utility.

That is almost identical to DSS.

This is an important finding.

It suggests that DSS is not providing much additional information compared with simply using block depth.

### Partial correlation controlling for depth: 0.076

This is the most important number on the graph.

The partial correlation asks:

"After accounting for the relationship with transformer depth, does DSS still have a meaningful association with adaptation utility?"

The answer in our results is approximately 0.076.

This is close to zero.

Therefore, the observed relationship between DSS and utility largely disappears after controlling for depth.

### What does this mean in simple language?

Imagine a student ranking people by height and claiming that height predicts their exam scores.

But suppose the ranking is actually following age, and age explains the relationship.

Then height may not be providing much independent information.

In our experiment, DSS rankings closely follow transformer depth.

Once we account for depth, DSS no longer provides a meaningful additional ranking signal.

## 5. Explain the main result

Say:

"The main result is that DSS did not successfully identify the transformer blocks that benefited most from adaptation.

Although DSS showed a positive correlation with utility, the same relationship was observed with a simple late-layer rule.

After controlling for depth, the partial correlation was only 0.076.

Our additional top-K analysis also showed that DSS-selected blocks were no better than random selections.

Therefore, the original DSS-based layer-selection hypothesis was not supported by this experiment."

## 6. What does the experiment actually prove?

Be careful with the word prove.

Our experiment provides evidence for the following conclusions within the tested setup:

- Individual transformer blocks have different observed adaptation utilities.
- The middle blocks had the highest mean utilities.
- DSS ranking closely followed depth.
- DSS did not outperform random top-K selections.
- The DSS-utility association largely disappeared after controlling for depth.

It does not establish that:
- Middle layers will always be best.
- DSS can never work on another backbone or dataset.
- Selective adaptation is useless.
- Full fine-tuning is worse than LoRA.
- Our method is more computationally efficient than all alternatives.

## Likely questions — Slide 5

**Q1. Why did you run 75 experiments?**

We evaluated the decoder-only baseline and individual transformer blocks across three seeds. This allowed us to measure layer-specific adaptation utility.

**Q2. Why three seeds?**

To examine sensitivity to training randomness. Three seeds provide useful preliminary evidence, but the uncertainty remains substantial.

**Q3. Why 2,000 steps?**

It was the fixed training budget defined in the Phase 2D protocol. We compared all runs at the same fixed step.

**Q4. What is the K = 0 baseline?**

It is the decoder-only configuration. The backbone is frozen and no LoRA block is adapted.

**Q5. What is the difference between K = 0 and K = 1?**

K = 0 trains the decoder without LoRA. K = 1 trains the decoder plus LoRA in one transformer block.

**Q6. Why compare against the same-seed baseline?**

Because different seeds can produce different baseline performance. Comparing within the same seed reduces the influence of those baseline differences.

**Q7. Why is L16 the best?**

It achieved the highest mean validation utility among the 24 individually adapted blocks in this experiment.

**Q8. Does that mean L16 is always the best layer?**

No. It is the best mean result in this specific setup. It needs independent validation.

**Q9. What does 0.420 mean?**

It is the Spearman correlation between DSS ranking and observed adaptation utility across the 24 blocks.

**Q10. What does 0.076 mean?**

It is the partial correlation between DSS and utility after controlling for depth. It indicates very little remaining association.

**Q11. Why compare DSS against a late-layer rule?**

To test whether DSS provides information beyond the simple fact that transformer blocks have different depths.

**Q12. Why is a correlation of 0.420 not enough?**

Because a similar correlation is obtained using depth alone. DSS does not show a clear additional benefit.

**Q13. What is random top-K selection?**

It means selecting the same number of blocks randomly instead of using DSS scores. We compare DSS selection against this baseline to test whether DSS provides a useful selection advantage.

**Q14. Did DSS outperform random selection?**

No. Its top-1, top-3 and top-5 selections were no better than random selections in the reported analysis.

**Q15. Did you evaluate on the test set?**

No. The eight test tiles remained locked and unopened.

**Q16. Is the middle-layer finding confirmed?**

No. It is exploratory because it was identified after examining the results. It needs independent validation using a protocol fixed in advance.

---

# Slide 6 — Phase 2 Results: Validation mIoU

This slide gives the actual mIoU numbers behind the utility graph on Slide 5. Slide 5 shows only the *change* (Δ); this slide shows the full scores.

## What is displayed on the slide?

- The top line says how every number was measured: Vaihingen validation set (5 tiles, 6 classes), at the end of training (step 2,000). Δ means "mIoU minus the same-seed K = 0 baseline".
- **Left card — K = 0:** the decoder-only baseline.
- **Top-right table — K = 2:** the four Phase 2C runs, two LoRA blocks each.
- **Bottom table — K = 1:** all 24 single-block Phase 2D runs, mIoU and Δ for every block, averaged over 3 seeds. Green block labels (L11–L17) mark the strongest region.
- **Bottom line:** the best and worst single blocks and the best K = 2 run.

## What you should say

"This slide shows the actual validation mIoU values for everything we trained in Phase 2.

First, K = 0. Here only the decoder is trained and the Prithvi backbone has no LoRA at all. Across our three seeds it scores 0.5264, 0.5194 and 0.5084, so the average is about 0.518. This is the reference every other run is compared against.

Second, K = 1. Here we add LoRA to exactly one transformer block. We did this for all 24 blocks, three seeds each. Every block except L0 improves on the baseline. The best block is L16 with 0.5553, which is +0.0372 above the baseline. The worst is L0 with 0.5108, slightly below the baseline. The strongest region is L11 to L17, shown in green.

Third, K = 2. In Phase 2C we tried four ways of choosing two blocks, with one seed only. The two blocks chosen by DSS, L23 and L19, gave 0.5520, the best of the four. The Late rule, L23 and L22, gave 0.5442. Lowest DSS, L0 and L3, gave 0.5294, and Early, L0 and L1, gave 0.5258.

The DSS pick looked good at K = 2. But the full K = 1 study showed that DSS mainly prefers deeper blocks, and once depth is taken into account it does not predict which block is useful. That is the finding on the next slide."

## Explain the three K values simply

| K | What is trained | Phase | Seeds | Result |
|---|---|---|---|---|
| 0 | Decoder only | 2C and 2D | 3 (2D) | 0.518 mean |
| 1 | Decoder + LoRA in one block | 2D | 3 per block | 0.511 (L0) to 0.555 (L16) |
| 2 | Decoder + LoRA in two blocks | 2C | 1 | 0.5258 (Early) to 0.5520 (DSS) |

## What the seed numbers on this slide mean

"Seeds 1000 / 2000 / 3000" are three independent repeats of the same training setup with different random starting weights and a different random order of training crops. Runs with the same seed share exactly the same starting point and crops, so the Δ values are fair like-for-like comparisons. The full explanation is under Slide 5, "What do seed 1000, seed 2000 and seed 3000 mean?".

## Important cautions

1. **K = 2 used one seed only.** Seed-to-seed variation in this setup is about 0.01 mIoU, so the K = 2 differences are indicative, not proven.
2. **K = 1 and K = 2 come from different phases.** Do not say "K = 2 is worse than K = 1 at L16". They were separate experiments with different purposes.
3. **These are validation scores, not test scores.** The 8 test tiles were never opened.
4. **The gains are small in absolute terms (about 0.01–0.04 mIoU),** but they are measured against a same-seed baseline, so they are fair comparisons.

## Likely questions — Slide 6

**Q1. Why is K = 0 already 0.518 if the backbone is frozen?**

The pretrained Prithvi features are already useful. The decoder learns to turn them into the 6 classes. LoRA then adds a small extra improvement.

**Q2. Why is L0 below the baseline?**

L0 is the first block and processes very low-level patterns. Changing it slightly disturbs everything after it, and in our Vaihingen setting it did not help.

**Q3. Why did DSS do well at K = 2 if the hypothesis was not supported?**

DSS ranks deep blocks highest, and deep blocks are generally useful. So the DSS pick works partly because it is a "deep blocks" rule. The K = 1 study showed that DSS adds almost nothing beyond depth (partial correlation 0.076).

**Q4. Why not report the best checkpoint instead of step 2,000?**

Choosing the best checkpoint uses the validation labels to pick, which inflates the score. Step 2,000 is a fixed, fair point for every run.

---

# Slide 7 — Key Findings

This slide separates what held up from what did not.

Explain both sides honestly.

## Start with the overall message

Say:

"After completing the 75 experiments, we separated the findings into two categories.

First, what we learned about selective adaptation.

Second, what we learned about our proposed DSS selection signal.

The important point is that some parts of our research direction received support, while the main DSS-based selection hypothesis did not."

## Left side — What held up

### 1. Layer choice matters

The slide says:

"Utility differs clearly across the 24 blocks."

Explain:

"When we adapted each transformer block independently, we observed different validation utilities.

Some blocks improved performance more than others.

This suggests that the location of adaptation matters in our experimental setup.

We should not assume that every transformer block contributes equally when we add LoRA."

### 2. Middle blocks worked best

The slide says:

"Gains peaked around L11–L17 (best: L16)."

Explain:

"The highest average validation improvement was observed around the middle transformer blocks.

L16 achieved the highest mean utility at approximately +0.0372.

However, this pattern was identified after examining the experimental results.

It was not a prospectively tested selection rule.

Therefore, we label it as an exploratory finding."

### What does exploratory mean?

Exploratory means we noticed a pattern while analysing the results.

We have not yet tested that pattern independently using a new, pre-defined experimental protocol.

### Why does independent validation matter?

Because a pattern discovered in one experiment may be specific to that dataset, model, split or random seed.

We need a new evaluation to check whether it happens again.

## Right side — What did not hold up

### 1. DSS mostly tracks depth

Explain:

"Our DSS ranking was strongly associated with the depth of the transformer blocks.

The ranking correlation between DSS and depth was approximately 0.94.

This means DSS largely ranked blocks in a similar order to a simple depth-based ranking."

### 2. DSS approximately random at top-K

Explain:

"When we selected the highest-scoring DSS blocks, those selected blocks were no better than random selections at the tested top-K values.

That means the score did not provide a useful advantage for selecting adaptation locations in this experiment."

### 3. Depth explains the link

Explain:

"The DSS-utility relationship became very small after controlling for depth.

The partial correlation was approximately 0.076.

So the relationship we initially observed was largely explained by transformer depth rather than a separate DSS signal."

## Explain the conclusion at the bottom

The slide says:

"The original DSS-based layer-selection hypothesis was not supported by our experiments."

Say:

"This is the main conclusion of our current study.

We initially expected that layers with higher representation discrepancy would benefit more from adaptation.

But our results did not support that expectation.

The score detected a representation difference, but it did not reliably identify the most useful adaptation layers."

Then:

"Selective adaptation is still worth studying because our experiments showed that different transformer blocks can have different adaptation utilities.

However, the current DSS selector needs improvement."

## Important distinction: What failed and what did not?

What did not work:
- The tested DSS-based layer-selection signal.
- The assumption that high discrepancy means high adaptation utility.

What remains interesting:
- Different blocks have different observed utilities.
- Selective adaptation may still be useful.
- A better selection signal may be possible.

Do not present the negative result as a complete failure of the project.

It is a result about the specific hypothesis and experimental configuration.

## Likely questions — Slide 7

**Q1. Did your proposed method fail?**

The DSS-based layer-selection hypothesis was not supported in the tested configuration. The broader question of selective adaptation remains open.

**Q2. Why is this still a useful research result?**

Because it shows that representation discrepancy alone was not enough to identify useful adaptation layers in our setup. It helps us avoid making an unsupported assumption.

**Q3. Why did middle layers work better?**

We observed higher mean adaptation utility around L11–L17. We do not yet know the mechanism behind this pattern.

**Q4. Can we simply select middle layers instead of using DSS?**

That is a possible next research direction, but the current middle-layer pattern is exploratory and requires independent validation.

**Q5. What does 0.94 mean?**

It is the Spearman correlation between the DSS ranking and transformer depth. It shows that DSS rankings closely followed block depth.

**Q6. What does it mean when DSS is no better than random?**

It means the selected blocks did not provide a better top-K utility than random selections in the tested analysis.

**Q7. Does this mean DSS is useless everywhere?**

No. We tested one backbone, one dataset pair and a specific training configuration. We cannot generalise the result to every model or dataset.

**Q8. What is the biggest learning from this project?**

A representation difference is not automatically a useful adaptation signal. We need to test whether a selection signal predicts actual adaptation benefit.

---

# Slide 8 — Limitations and Next Steps

This slide explains what remains incomplete and what we propose to investigate next.

Do not describe proposed work as completed work.

## 1. Current limitations

### One backbone and one dataset pair

Say:

"We used one backbone, Prithvi-EO-2.0-300M, and one source-target dataset pair, Potsdam to Vaihingen.

Therefore, we cannot claim that the same behaviour will occur with other foundation models or other remote sensing datasets."

Why does this matter?

Different models may have different architectures and representation behaviour.

Different datasets may also produce different types of domain shift.

### Three seeds and five validation tiles

Say:

"We used three random seeds and five validation tiles.

Although this provides repeated experimental observations, the statistical uncertainty remains substantial.

Small differences between neighbouring transformer blocks cannot be treated as reliably established."

### Single-block runs only

Say:

"In the main Phase 2D study, we adapted one transformer block at a time.

We did not test all possible combinations of multiple blocks.

For example, the result from adapting L16 alone does not tell us what will happen if we adapt L16 and L18 together."

Why?

The effect of combining two blocks may be different from simply adding their individual effects.

This is why joint K = 2 adaptation needs a separate experiment.

### No uniform-LoRA or full fine-tuning comparison yet

Say:

"We have measured the trainable parameter count for our selective LoRA configuration.

However, we have not completed the experimental comparisons against uniform LoRA and full fine-tuning.

Therefore, we cannot yet claim that our method provides better accuracy or better overall efficiency than those approaches."

### No held-out test evaluation yet

Say:

"We have not evaluated the final model on the eight locked test tiles.

We deliberately kept them untouched during the current study.

A future final evaluation can use them after the next experimental decisions are frozen."

## 2. Proposed next phase

Everything on the right side is future work.

### Step 1: Test depth-adjusted DSS and a middle-block prior

Explain:

"Since DSS largely follows transformer depth, one possible direction is to remove or account for the depth-related component before using DSS for selection.

We can also investigate a middle-block prior because the current experiments showed higher mean utility around L11 to L17.

However, these ideas need a new protocol and independent evaluation."

What is depth-adjusted DSS?

It means trying to separate the DSS signal from the information that can already be explained by the position of a block in the transformer.

What is a middle-block prior?

It means using the observed tendency of middle blocks to perform better as a hypothesis for the next experiment.

It is not yet an established rule.

### Step 2: Validate on an independent dataset or domain pair

Explain:

"We should repeat the study using another independent dataset pair.

This helps determine whether the observed behaviour is specific to Potsdam and Vaihingen or appears in another remote sensing setting."

### Step 3: Compare joint K = 2 adaptation with uniform LoRA

Explain:

"We should test whether adapting two selected blocks together produces a different result from adapting each block individually.

We should also compare that configuration with uniform LoRA, where LoRA is applied across the model according to a defined baseline configuration."

### Step 4: Add full fine-tuning and parameter-efficiency comparisons

Explain:

"We should compare selective LoRA with full fine-tuning.

We need to measure not only the number of trainable parameters but also segmentation quality, training time, memory use and inference cost where relevant.

Only then can we make a stronger claim about parameter efficiency."

### Step 5: Freeze the next protocol before running experiments

Explain:

"Before starting the next experiment, we should decide the datasets, splits, seeds, baselines, metrics and stopping conditions.

We should document these choices in advance.

This reduces the risk of changing the experimental design after seeing the results."

## 3. Explain the next objective

The slide says:

"Find out whether a reliable layer-selection signal can improve adaptation efficiency without sacrificing segmentation performance."

Say:

"Our next objective is not simply to find a layer with a high score.

We need to find a reliable signal that selects useful layers.

That signal should help us reduce unnecessary adaptation while maintaining segmentation performance.

We will only claim an efficiency advantage if the next experiments provide evidence for it."

## Closing statement

Say:

"To conclude, we implemented the DSS-based layer-selection pipeline and completed 75 Phase 2D experimental runs.

Our results showed that adaptation utility varies across transformer blocks.

However, the DSS ranking mostly followed transformer depth and did not outperform random selections at the tested top-K values.

Therefore, the original DSS-based selection hypothesis was not supported by our experiments.

Our next step is to investigate better selection signals and validate them using independent experiments and stronger baselines.

Thank you."

## Likely questions — Slide 8

**Q1. What is the most important remaining work?**

Independent validation of a better layer-selection signal, followed by joint multi-block and baseline comparisons.

**Q2. Why do you need another dataset pair?**

To determine whether the findings generalise beyond the current Potsdam-Vaihingen setup.

**Q3. Why test K = 2?**

Because the main Phase 2D study evaluated one block at a time. Combining blocks may produce interactions that individual-block experiments cannot reveal.

**Q4. Why compare against uniform LoRA?**

To determine whether selective block allocation provides an advantage over applying LoRA uniformly.

**Q5. Why compare against full fine-tuning?**

To understand the trade-off between trainable parameter count, performance and computational cost.

**Q6. Why have you not opened the test set?**

We preserved it for independent final evaluation and avoided using it during experimental selection.

**Q7. Can you claim parameter efficiency now?**

We can report the trainable parameter count. We cannot yet claim better overall efficiency or equivalent segmentation quality without the required comparisons.

**Q8. What is the final expected contribution?**

A carefully evaluated answer to whether representation-based layer selection can identify useful adaptation locations, including evidence about where the approach works and where it does not.

---

# Additional preparation: Technical terms you must understand

Use this section to revise before the presentation.

| Term | Simple explanation |
|---|---|
| Remote sensing | Collecting information about the Earth without direct contact |
| Aerial imagery | Images of the Earth's surface captured from aircraft or other airborne platforms |
| Satellite imagery | Images collected by satellites |
| Domain | A particular data environment, such as a location, sensor or acquisition condition |
| Domain shift | Differences between the data environments |
| Semantic segmentation | Assigning a category to every image pixel |
| Pixel | The smallest addressable element of a digital image |
| Tile | A defined image section representing a geographical area |
| Ground resolution | Ground distance represented by one pixel |
| IRRG | Infrared, Red and Green image bands |
| False colour | Displaying invisible or non-standard bands using visible display colours |
| Foundation model | A model pretrained on large datasets for reusable representations |
| Backbone | The main feature-extraction part of a neural network |
| Transformer | A neural-network architecture using attention mechanisms |
| Transformer block | One processing stage inside a transformer |
| Feature | A numerical representation produced by a model |
| Token | A unit of information processed by a transformer |
| Frozen parameter | A model parameter that is not updated during training |
| Trainable parameter | A model parameter that is allowed to change during training |
| Fine-tuning | Updating pretrained model parameters for a specific task |
| LoRA | Low-Rank Adaptation; adds smaller trainable updates instead of directly updating large weight matrices |
| Rank | Controls the size of the low-rank LoRA update |
| Query | Attention projection that represents what information is being sought |
| Key | Attention projection used to represent available information |
| Value | Attention projection that carries information forward |
| Decoder | Converts extracted features into task-specific outputs |
| Preprocessing | Preparing raw data for model input |
| Radiometric transformation | Adjusting numerical image-value scales |
| Centroid | A central reference point calculated from feature vectors |
| Cosine distance | A measure of difference in vector direction |
| DSS | Domain Sensitivity Score; measures source-target representation discrepancy |
| Source domain | The reference dataset, Potsdam |
| Target domain | The dataset being adapted to, Vaihingen |
| Top-K | The K highest-ranked blocks |
| Seed | A starting number for the random number generator; the same seed repeats the same random choices (initial weights, crops, flips). Seeds 1000, 2000 and 3000 are just three different labels |
| Training step | One model update using a batch |
| Validation | Evaluating a model using data not used for parameter updates |
| Test set | A reserved dataset for final independent evaluation |
| Oracle | In this experiment, a validation-label-based evaluation of individual layer utility |
| mIoU | Mean Intersection over Union across segmentation classes |
| IoU | Overlap between predicted and ground-truth regions |
| Spearman correlation | Measures how two rankings vary together |
| Partial correlation | Measures association after accounting for another variable |
| Exploratory finding | A pattern observed during analysis that still needs independent testing |
| Independent validation | Testing a finding on new data or a separately defined experiment |

---

# Formulas explained simply

Use this section if the panel asks "how exactly did you compute this?". Each formula is followed by a plain-language explanation.

## A. DSS — Domain Sensitivity Score (Phase 2B)

DSS is computed once, before any training, from **images only** (no labels). It gives each of the 24 blocks one number.

### Step 1 — Get one feature vector per image for each block

$$f_\ell(x) = \frac{1}{196} \sum_{p=1}^{196} h_{\ell,p}(x)$$

- x is a 224 × 224 image crop (the top-left crop of a tile), after the fixed radiometric transform.
- The frozen Prithvi model splits it into 196 patches (14 × 14). Block ℓ outputs a 1,024-number vector for each patch, h_{ℓ,p}.
- We average the 196 patch vectors into one 1,024-number vector, f_ℓ(x).

**In simple words:** for every block, we summarise each image as one "average feature" vector.

### Step 2 — Build the source centroid

$$c_{S,\ell} = \frac{\text{mean}_{s \in S}\, f_\ell(s)}{\lVert \text{mean}_{s \in S}\, f_\ell(s) \rVert}$$

- S = 16 Potsdam source tiles.
- We average their vectors and scale the result to length 1.

**In simple words:** the centroid is the "typical Potsdam image" as block ℓ sees it.

### Step 3 — Raw DSS: how far the target is from the source

$$D_\ell = \frac{1}{|T|} \sum_{t \in T} \Big(1 - \cos\big(f_\ell(t),\, c_{S,\ell}\big)\Big)$$

- T = the 5 Vaihingen probe tiles (images only).
- cos(a, b) is the cosine similarity: 1 when two vectors point the same way, smaller when they differ.
- 1 − cos is the **cosine distance**: 0 means identical direction, larger means more different.

**In simple words:** raw DSS is the average "distance" between Vaihingen images and the typical Potsdam image, measured inside block ℓ.

### Step 4 — Normalise against a source-vs-source baseline (null)

Different blocks have different natural spreads, so raw distances cannot be compared directly across blocks. We measure how far apart two groups of **Potsdam** images are by chance:

- take 16 other Potsdam tiles, shuffle them, split into 8 vs 8, compute the same distance;
- repeat 40 times (fixed random seed 1234), giving a mean μ_ℓ and a standard deviation σ_ℓ for each block.

$$\text{DSS}_\ell = z_\ell = \frac{D_\ell - \mu_\ell}{\sigma_\ell}$$

**In simple words:** DSS says how many "typical source-to-source differences" the Vaihingen images are away from Potsdam in block ℓ. A high DSS means the block sees an unusually large domain shift.

**Real example from our frozen scores:**

| Block | Raw distance D | Normalised DSS z |
|---|---:|---:|
| L0 | 0.152 (largest raw) | −1.24 (lowest) |
| L19 | 0.126 | +0.44 (2nd highest) |
| L23 | 0.092 (smallest raw) | +0.44 (highest) |

This shows why normalisation matters: L0 has the biggest raw distance, but Potsdam images also differ a lot from each other in L0, so after normalising it has the *lowest* DSS.

### Step 5 — Rank the blocks and select

- Sort the 24 blocks from highest to lowest DSS. Frozen ranking (Phase 2B): **L23, L19, L22, L18, L20, L17, … , L4, L3, L0**.
- **DSS (DSSA) selection, Top-K:** take the K highest. For K = 2 → **L23, L19**.
- **Lowest-DSS selection:** take the K lowest, as a "reverse" control. For K = 2 → **L0, L3**.
- **Early:** the first K blocks → L0, L1. **Late:** the last K blocks → L23, L22. These are simple depth rules used for comparison.

**In simple words:** DSS predicts "adapt the blocks that see the biggest domain shift". Lowest-DSS checks the opposite, to see whether the score direction matters.

## B. Performance metrics

All metrics come from the **confusion matrix**: a 6 × 6 table counting, for every pixel, the true class versus the predicted class. We add the counts of all 5 validation tiles together before computing the scores (pooled).

For one class c:

- **TP (true positive):** pixels of class c predicted as c.
- **FP (false positive):** pixels of other classes wrongly predicted as c.
- **FN (false negative):** pixels of class c predicted as something else.

### IoU — Intersection over Union (per class)

$$\text{IoU}_c = \frac{TP_c}{TP_c + FP_c + FN_c}$$

**In simple words:** overlap between the predicted area and the true area, divided by their combined area. 1 = perfect, 0 = no overlap.

Example: true building area 100 pixels, predicted 90, of which 80 are correct. TP = 80, FP = 10, FN = 20. IoU = 80 / (80 + 10 + 20) = 0.727.

### mIoU — mean IoU (our main metric)

$$\text{mIoU} = \frac{1}{6} \sum_{c=1}^{6} \text{IoU}_c$$

**In simple words:** the average IoU over the 6 classes (impervious surface, building, low vegetation, tree, car, clutter). Every class counts equally, so small classes like car matter as much as large ones.

### Pixel accuracy

$$\text{Pixel accuracy} = \frac{\sum_c TP_c}{\text{all pixels}}$$

**In simple words:** the share of pixels labelled correctly. Easy to understand, but large classes dominate it, which is why mIoU is the main metric.

### F1 score (per class) and macro F1

$$F1_c = \frac{2\, TP_c}{2\, TP_c + FP_c + FN_c}, \qquad \text{macro F1} = \frac{1}{6}\sum_c F1_c$$

**In simple words:** a balance of precision (how many predicted pixels are right) and recall (how many true pixels were found). It is always at least as high as IoU for the same class.

### Utility (Δ mIoU)

$$U_\ell = \text{mIoU}(\text{LoRA on block } \ell,\ \text{seed } s) - \text{mIoU}(K = 0,\ \text{seed } s)$$

$$\bar U_\ell = \text{mean over the 3 seeds}$$

**In simple words:** how much adding LoRA to block ℓ improves over the decoder-only baseline trained with the same seed. Using the same seed removes the effect of lucky or unlucky initialisation. Example: L16 averages 0.5553 and the baseline averages 0.5181, so the utility is +0.0372.

## C. Statistics used to test DSS

### Spearman rank correlation (ρ)

**In simple words:** rank the 24 blocks by DSS and, separately, by utility, then check how similar the two rankings are. +1 = same order, 0 = unrelated, −1 = opposite order. Our DSS–utility value is **0.420**, and a simple "later is better" rule gives **0.422**, almost the same.

### Partial correlation controlling for depth

**In simple words:** remove the part of DSS that is just "how deep the block is", remove the part of utility that is explained by depth, and correlate what is left. Our value is **0.076**, close to zero. So DSS carries almost no information about utility beyond block depth.

### Top-k comparison against random

**In simple words:** take the k blocks with the highest DSS (k = 1, 3, 5) and check whether their utility is better than k blocks picked at random. DSS's picks were not better than random.

---

# Important numbers to memorise

| Item | Value |
|---|---:|
| Prithvi backbone parameters | 303,886,336 |
| Transformer blocks | 24 |
| Block numbering | L0 to L23 |
| Potsdam tiles | 38 |
| Vaihingen tiles | 33 |
| Vaihingen training tiles | 20 |
| Vaihingen train/probe tiles | 5, included in the 20 |
| Vaihingen validation tiles | 5 |
| Locked test tiles | 8 |
| Segmentation classes | 6 |
| Potsdam ground resolution | Approximately 5 cm |
| Vaihingen ground resolution | Approximately 9 cm |
| LoRA rank | 8 |
| LoRA projections | Q and V |
| LoRA parameters per block | 32,768 |
| Decoder parameters | 2,766,726 |
| K = 1 trainable parameters | 2,799,494 |
| Full fine-tuning trainable parameters | Approximately 306.7M |
| K = 1 relative parameter count | Approximately 0.91% |
| Phase 2D runs | 75 |
| Pilot runs | 12 |
| Oracle runs | 63 |
| Random seeds | 3 |
| Training steps per run | 2,000 |
| Best mean utility block | L16 |
| L16 mean utility | +0.0372 |
| L0 mean utility | -0.0073 |
| L23 mean utility | +0.0146 |
| DSS-utility Spearman correlation | 0.420 |
| Late-layer utility correlation | 0.422 |
| DSS partial correlation controlling for depth | 0.076 |
| DSS-depth ranking correlation | Approximately 0.94 |
| Test tiles opened in Phase 2D | 0 of 8 |
| K = 0 mIoU (seeds 1000 / 2000 / 3000) | 0.5264 / 0.5194 / 0.5084 |
| K = 0 mean mIoU | Approximately 0.518 |
| Best K = 1 mIoU | L16, 0.5553 |
| Worst K = 1 mIoU | L0, 0.5108 |
| K = 2 DSS top-2 (L23, L19) mIoU | 0.5520 (one seed) |
| K = 2 Late (L23, L22) mIoU | 0.5442 (one seed) |
| K = 2 Lowest DSS (L0, L3) mIoU | 0.5294 (one seed) |
| K = 2 Early (L0, L1) mIoU | 0.5258 (one seed) |
| DSS null baseline | 40 shuffles, 8 vs 8 Potsdam tiles |

---

# Difficult questions the panel may ask

## 1. If DSS failed, what is the contribution of your project?

Our contribution is an implemented and experimentally evaluated investigation of whether label-free layer-wise representation discrepancy predicts adaptation utility. The results show that, in this configuration, the signal largely followed depth and did not outperform random selection. Identifying that limitation is a valid research finding.

## 2. Why should we trust the negative result?

We evaluated all 24 transformer blocks independently, used three seeds, compared each run against a same-seed baseline, checked checkpoint integrity and kept the test set untouched. However, the result is still limited to one backbone, one dataset pair and five validation tiles.

## 3. Why did you not train on Potsdam and test on Vaihingen?

That would be a different experimental setup. Our current protocol uses Potsdam images to establish the source representation reference and labelled Vaihingen data for target-supervised segmentation training. We should not describe the current experiment as a source-trained segmentation transfer evaluation.

## 4. Does a high DSS mean a layer is confused?

Not necessarily. It means the layer's target representations differ more from the source reference. It does not directly measure confusion, prediction error or adaptation benefit.

## 5. Why does DSS follow depth?

The exact mechanism is not established. The observed rankings are strongly associated with transformer depth. We need further experiments to determine why this happens and whether a depth-adjusted signal can add useful information.

## 6. Why not simply select L16?

L16 was the best mean utility block in this experiment, but the finding is exploratory. Selecting it as a general rule without independent validation would overfit our current observations.

## 7. What is the difference between a feature and a prediction?

A feature is an internal numerical representation produced by the model. A prediction is the model's output for the task. In our case, the decoder converts features into six-class segmentation predictions.

## 8. Why do you need a decoder if Prithvi is already pretrained?

Prithvi provides general geospatial representations. Our task requires pixel-level predictions for six specific segmentation classes. The decoder learns how to convert the backbone features into those class predictions.

## 9. Why is the decoder trainable while the backbone is frozen?

The decoder needs to learn the specific segmentation task. Freezing the backbone allows us to preserve its pretrained representations while adapting only the selected LoRA parameters and the task-specific decoder.

## 10. What would make the next phase successful?

A selection signal that performs better than meaningful baselines, remains useful after controlling for depth, and is validated on independent data. It should also provide a measurable parameter or computational advantage without unacceptable segmentation-quality loss.

---

# Final advice for presenting

1. Do not memorise every sentence. Understand the explanation and speak naturally.
2. Start each slide by explaining the problem or purpose before discussing technical details.
3. Point to the relevant part of the slide as you explain it.
4. Do not call aerial imagery satellite imagery.
5. Never say that high DSS means high adaptation utility.
6. Do not claim that L16 is universally the best block.
7. Do not claim that the method is more efficient than full fine-tuning until the required comparisons are completed.
8. Never describe the current experiment as unsupervised segmentation training.
9. Be clear that the eight test tiles were never opened.
10. If you do not know an answer, state what your experiments establish and what still needs testing.

**The one sentence you should remember above everything else:**

"We measured how much the model's internal representations differ between Potsdam and Vaihingen, then tested whether the blocks showing larger differences actually benefited more from adaptation. In our experiments, that assumption was not supported."
