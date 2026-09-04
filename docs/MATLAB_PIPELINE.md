# DRISHTI-LENS — MATLAB Medical Image Processing & Screening Pipeline

**SIH 2026 Problem Statement Compliance Document**

---

## 1. System Architecture Overview

The DRISHTI-LENS MATLAB subsystem (`matlab/`) implements a complete medical image processing workflow for automated Diabetic Retinopathy (DR) screening.

```
                  ┌───────────────────────────────┐
                  │      Input Fundus Image       │
                  └──────────────┬────────────────┘
                                 │
                                 ▼
                  ┌───────────────────────────────┐
                  │ 1. Image Quality Assessment   │
                  │  - Tenengrad Focus Energy     │
                  │  - Illumination Histogram     │
                  │  - Circular Hough FOV Mask    │
                  └──────────────┬────────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 │                               │
       [QUALITY_BORDERLINE]              [QUALITY_GOOD]
                 │                               │
                 ▼                               │
  ┌─────────────────────────────┐                │
  │ 2. Adaptive Enhancement     │                │
  │  - LAB CLAHE Equalization   │                │
  │  - Gaussian Vignette Norm   │                │
  │  - Bilateral Edge Denoising │                │
  └──────────────┬──────────────┘                │
                 │                               │
                 └───────────────┬───────────────┘
                                 │
                                 ▼
                  ┌───────────────────────────────┐
                  │ 3. Anatomical Localisation    │
                  │  - Optic Disc (Red channel)   │
                  │  - Fovea Centralis (Geometry) │
                  │  - Blood Vessels (Bottom-hat) │
                  └──────────────┬────────────────┘
                                 │
                                 ▼
                  ┌───────────────────────────────┐
                  │ 4. Retinal Lesion Detection   │
                  │  - Microaneurysms (Small TH)  │
                  │  - Hard Exudates (Top-hat)    │
                  │  - Hemorrhages (Green TH)     │
                  │  - Neovascularization (Density│
                  └──────────────┬────────────────┘
                                 │
                                 ▼
                  ┌───────────────────────────────┐
                  │ 5. ICDR 0-4 Diagnostic Grade  │
                  │  - Rule-Based / DL Classifier │
                  │  - Referable Status (>= 2)    │
                  │  - Confidence Calibration     │
                  └──────────────┬────────────────┘
                                 │
                                 ▼
                  ┌───────────────────────────────┐
                  │ 6. Explainability & Reporting │
                  │  - Lesion Evidence Narrative  │
                  │  - Annotated Landmark Overlay │
                  │  - Grad-CAM Heatmap Activation│
                  │  - Structured Clinical Report │
                  └───────────────────────────────┘
```

---

## 2. Component Reference

### 2.1 Quality Gate (`matlab/quality/`)
- `focus_score.m`: Computes $\sum (G_x^2 + G_y^2)$ using Sobel filters on the green channel. Threshold $\ge 150.0$ for optimal focus.
- `illumination_score.m`: Analyzes mean brightness and saturation fractions ($>250$ glare, $<30$ underexposed).
- `field_of_view_check.m`: Two-stage circular Hough transform (`imfindcircles`) verifying retinal boundary visibility $\ge 55\%$.
- `gradability_decision.m`: Triage logic emitting `QUALITY_GOOD`, `QUALITY_BORDERLINE`, or `QUALITY_UNGRADABLE`.

### 2.2 Adaptive Preprocessing (`matlab/preprocessing/`)
- `clahe_enhancement.m`: Local contrast equalization in LAB space on luminance ($L \in [0, 1]$), avoiding color distortions.
- `illumination_normalization.m`: Division by Gaussian-blurred background model ($\sigma = 60$) to eliminate non-uniform vignetting.
- `denoising.m`: Non-destructive bilateral filtering preserving microaneurysm boundaries while suppressing camera sensor noise.

### 2.3 Segmentation Subsystem (`matlab/segmentation/`)
- `optic_disc.m`: Morphological closing and area-filtering on 92nd-percentile thresholded red channel.
- `fovea.m`: Geometric localization approximately 2.5 disc diameters temporal to optic disc center.
- `vessels.m`: Morphological bottom-hat transform (`imbothat`) extracting retinal vascular tree.
- `microaneurysms.m`: Small structuring element ($r=3$) morphological filtering with optic disc dilation exclusion.
- `exudates.m`: Top-hat bright lesion detection with optic nerve head masking.
- `hemorrhages.m`: Intraretinal dark lesion extraction with vessel and disc subtraction.
- `neovascularization.m`: Peripapillary anomalous vessel density assessment.

### 2.4 Diagnostic Grading & Calibration (`matlab/grading/`)
- `icdr_classifier.m`: Multi-tier clinical rule mapping lesion evidence to ICDR levels 0 to 4.
- `referable_dr.m`: Clinical classification: Level $\ge 2$ or DME risk $\ge 30\%$ triggers ophthalmologist referral.
- `confidence_calibration.m`: Post-hoc temperature scaling ($T$) adjusting raw softmax probabilities to true posterior likelihoods.

### 2.5 Explainability & Validation (`matlab/explainability/`, `matlab/validation/`)
- `annotated_output.m`: Multi-layer color-coded overlay (vessels: cyan, hemorrhages: red, exudates: yellow, optic disc: green, fovea: amber).
- `evaluate_model.m`: Empirical evaluation runner calculating sensitivity, specificity, ROC-AUC, and confusion matrix on held-out test splits.
