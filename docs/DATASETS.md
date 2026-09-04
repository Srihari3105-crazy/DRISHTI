# DRISHTI-LENS — Clinical Datasets & Data Preparation Guide

This document details the open-source clinical ophthalmological datasets used for training, validating, and testing the DRISHTI-LENS AI and MATLAB screening pipelines.

---

## 1. Primary Dataset: APTOS 2019 Blindness Detection

- **Source:** Kaggle / Asia Pacific Tele-Ophthalmology Society (APTOS)
- **License:** Community Data License Agreement — Permissive, Version 1.0 (Commercial & academic use permitted)
- **Modality:** Color Fundus Photography captured under field conditions in India
- **Ground Truth Labels:** 
  - `0`: No Diabetic Retinopathy
  - `1`: Mild NPDR
  - `2`: Moderate NPDR (Referable)
  - `3`: Severe NPDR (Referable)
  - `4`: Proliferative DR (Referable)
- **Class Distribution:**
  - Class 0: ~1,805 images (49.3%)
  - Class 1: ~370 images (10.1%)
  - Class 2: ~999 images (27.3%)
  - Class 3: ~193 images (5.3%)
  - Class 4: ~295 images (8.0%)

### Download & Placement Instructions
1. Install the Kaggle CLI:
   ```bash
   pip install kaggle
   ```
2. Configure credentials in `~/.kaggle/kaggle.json`.
3. Download and extract the dataset into the repository:
   ```bash
   kaggle competitions download -c aptos2019-blindness-detection
   unzip aptos2019-blindness-detection.zip -d backend/validation/data/aptos2019/
   ```
4. Verify directory layout:
   ```
   backend/validation/data/aptos2019/
   ├── train_images/
   │   ├── 000c1434d8d7.png
   │   └── ... (3662 images)
   └── train.csv
   ```

---

## 2. Segmentation Benchmarks: IDRiD & DDR Datasets

For validating the sub-pixel lesion detectors (Microaneurysms, Exudates, Hemorrhages) and anatomical structures (Optic Disc, Fovea, Vessels):

- **Indian Diabetic Retinopathy Image Dataset (IDRiD):**
  - **Source:** IEEE Dataport (DOI: 10.21227/H25W98)
  - **Modality:** Kowa VX-10alpha digital fundus camera, 50-degree field of view
  - **Relevance:** Specifically collected from eye clinics in India, mirroring the target demographic of DRISHTI-LENS.
  - **Ground Truth Masks:** Pixel-level binary masks for Microaneurysms, Haemorrhages, Hard Exudates, Soft Exudates, and Optic Disc boundaries.

- **DDR Dataset:**
  - **Source:** TMI 2020 / Multicentre Retinal Image Database
  - **Size:** 13,673 fundus images with 1,151 expert pixel-level lesion segmentations.

---

## 3. Data Preprocessing & Integrity Invariants

All images fed to the DRISHTI-LENS pipeline undergo standardized transformations:
1. **Circular Masking:** Automatic background noise removal via circular Hough transform / FOV boundary detection.
2. **Aspect Ratio Preservation:** Padded resizing to 512x512 pixels.
3. **Contrast Normalization:** Lab color-space CLAHE (ClipLimit = 2.0, GridSize = 8x8) applied only on the luminance channel.
4. **Data Privacy & De-identification:** Stripped of all EXIF headers and identifiable demographic metadata prior to ingestion.
