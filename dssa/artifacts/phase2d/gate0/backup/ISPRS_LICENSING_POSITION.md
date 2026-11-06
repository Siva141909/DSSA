# ISPRS licensing position for the DSSA backup (2026-11-02)

Project working position for a private backup. This is not legal advice.

## Sources read
1. ISPRS Test Project on Urban Classification and 3D Building Reconstruction,
   section 2.1.5 "Conditions of Use":
   https://www2.isprs.org/media/komfssn5/complexscenes_revision_v4.pdf
   (linked from the ISPRS benchmark page as the terms of use).
2. ISPRS benchmark, Vaihingen, Potsdam and 2D semantic labeling pages,
   https://www.isprs.org/resources/datasets/benchmarks/UrbanSemLab/
3. Secondary only: README of microsoft/data-centric-satellite-segmentation.

## What the terms say
Vaihingen (source 1, verbatim):
- "The data must not be used for other than research purposes. Any other use is prohibited."
- "The data must not be distributed to third parties. Any person interested in the data may obtain them via ISPRS WG III/4."
- Papers based on the data must cite Cramer 2010 and carry the stated DGPF
  acknowledgement, and DGPF should be informed of such papers.

Potsdam: no explicit licence or redistribution clause was found on the ISPRS
pages read. The page thanks BSF Swissphoto for providing the data free of charge.
Source 3 treats it as research-only and not for redistribution, by analogy with
similar ISPRS datasets. That is an inference, not an ISPRS statement.

All pages read: participants "shall use all data with ground truth for training
... or internal evaluation of their method". Footer: "2026 (c) ISPRS. All Rights
Reserved."

Derived checkpoints and trained models: none of these sources addresses them.
No explicit permission or prohibition was found. The data-request form itself
was not retrieved.

## Project position
- The five Phase 2C checkpoints hold decoder and LoRA weights trained with
  Vaihingen imagery and labels. They contain no imagery or label rasters as
  stored files, but they are derived from the data and their status is unresolved.
- Potsdam labels were not used in training. Potsdam imagery was used only for
  radiometric fitting and DSS.
- A private release on the research owner's own account, with no collaborators,
  is treated as the project's own off-site storage for research use, not as
  distribution of the data to a third party. GitHub is a storage provider here;
  no ISPRS imagery or labels are given to it.
- Excluded from the backup: all imagery, all labels, the ISPRS archives, and
  features_pre.npz (derived feature vectors).
- The assets must stay private. Making them public, or adding collaborators,
  needs a fresh review. Seek ISPRS WG/DGPF guidance before any public release of
  weights.
- Any paper must carry the Vaihingen citation and acknowledgement and notify DGPF.

## Unresolved
Whether trained weights count as distribution of the data. Whether Potsdam has
written terms in the data-request form. These do not block a private backup under
the position above; they do block public weight release.
