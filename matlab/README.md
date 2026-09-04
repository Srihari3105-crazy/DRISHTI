# DRISHTI-LENS — MATLAB Medical Image Processing & Screening Pipeline

This directory contains the MATLAB implementation of the offline DR screening pipeline, built for **Smart India Hackathon (SIH) 2026**.

---

## 1. System Requirements & Toolbox Dependencies

- **MATLAB Version:** R2023b or later recommended.
- **Required Toolboxes:**
  - **Image Processing Toolbox:** `adapthisteq`, `rgb2lab`, `lab2rgb`, `imtophat`, `imbothat`, `imfill`, `imclose`, `imgaussfilt`, `fspecial`, `imfilter`.
  - **Computer Vision Toolbox:** `imfindcircles`, `imbilatfilt`.
  - **Statistics and Machine Learning Toolbox:** `perfcurve`, `prctile`.
  - **Deep Learning Toolbox:** `gradCAM`, `confusionchart` (optional for deep learning path).

---

## 2. Directory Architecture

```
matlab/
├── pipeline/                      # Main execution scripts
│   ├── dr_screening_pipeline.m    # Complete orchestrator
│   ├── image_quality_assessment.m # Tenengrad + Hough FOV + Illumination
│   ├── adaptive_enhancement.m     # CLAHE + Illumination norm + Denoising
│   ├── dr_grading.m               # Severity classifier wrapper
│   ├── explainability.m           # Narrative + Overlay generator
│   └── generate_report.m          # Clinical report exporter
├── quality/                       # Modular quality assessment metrics
│   ├── focus_score.m
│   ├── illumination_score.m
│   ├── field_of_view_check.m
│   ├── blur_detection.m
│   └── gradability_decision.m
├── preprocessing/                 # Enhancement transforms
│   ├── clahe_enhancement.m
│   ├── illumination_normalization.m
│   └── denoising.m
├── segmentation/                  # Anatomical & lesion detectors
│   ├── optic_disc.m
│   ├── fovea.m
│   ├── vessels.m
│   ├── microaneurysms.m
│   ├── exudates.m
│   ├── hemorrhages.m
│   └── neovascularization.m
├── grading/                       # ICDR classification & calibration
│   ├── icdr_classifier.m
│   ├── referable_dr.m
│   └── confidence_calibration.m
├── explainability/                # Visual verification tools
│   ├── gradcam.m
│   ├── lesion_evidence.m
│   └── annotated_output.m
├── validation/                    # Clinical validation suite
│   ├── evaluate_model.m
│   ├── sensitivity_specificity.m
│   ├── roc_analysis.m
│   ├── confusion_matrix.m
│   └── benchmark_comparison.m
└── data/                          # Dataset guides and splits
```

---

## 3. Quick Start & Execution

### Running Single-Image Screening
```matlab
% In MATLAB command window:
cd('c:/Users/dell/Downloads/DRISHTI-main/matlab/pipeline');
result = dr_screening_pipeline('path/to/fundus_image.jpg', './output');

% Inspect results:
disp(result.grading);
disp(result.quality);
```

### Running the Clinical Validation Suite
```matlab
cd('c:/Users/dell/Downloads/DRISHTI-main/matlab/validation');
results = evaluate_model('../data/aptos2019', './results');
```
