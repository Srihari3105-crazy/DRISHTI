# DRISHTI-LENS — Clinical Validation Framework & Benchmark Results

## 1. Executive Summary & Clinical Intent
DRISHTI-LENS is built to provide rural and primary healthcare centres (PHCs) with an offline-first diagnostic screening ecosystem for Diabetic Retinopathy (DR). The clinical benchmark requirements set forth by international ophthalmology screening standards and SIH 2026 problem statements specify:
- **Referable DR Sensitivity:** Target > 90% (minimising false negatives to ensure no sight-threatening patient is missed)
- **Referable DR Specificity:** Target > 85% (minimising false positives to avoid overburdening tertiary ophthalmic referral centers)
- **Gradability Gate:** Automated quality verification prior to clinical grading
- **Explainability:** Lesion-level traceability and Grad-CAM spatial heatmaps for doctor adjudication

> [!IMPORTANT]
> **Anti-Fabrication Notice (Clinical Integrity)**  
> In compliance with strict engineering ethics, no clinical accuracy scores, ROC curves, or sensitivity figures have been fabricated. Until a local download of the full APTOS 2019 / DDR dataset is processed through `backend/validation/evaluate_model.py` or MATLAB's `evaluate_model.m`, numbers are presented as benchmark methodology and evaluation targets rather than fictitious claims.

---

## 2. Evaluation Methodology & Metric Definitions

### 2.1 Referable DR Definition
Referable DR is defined strictly according to the International Clinical Diabetic Retinopathy (ICDR) scale:
- **Non-Referable (Class 0):** ICDR Level 0 (No DR) and ICDR Level 1 (Mild NPDR with isolated microaneurysms).
- **Referable (Class 1):** ICDR Level 2 (Moderate NPDR), Level 3 (Severe NPDR), Level 4 (Proliferative DR), or presence of Diabetic Macular Edema (DME) risk.

### 2.2 Mathematical Metrics
Given True Positives ($TP$), False Positives ($FP$), True Negatives ($TN$), and False Negatives ($FN$):
- **Sensitivity (Recall):**
  $$\text{Sensitivity} = \frac{TP}{TP + FN}$$
- **Specificity:**
  $$\text{Specificity} = \frac{TN}{TN + FP}$$
- **Receiver Operating Characteristic — Area Under Curve (ROC-AUC):**  
  Integral of the True Positive Rate against False Positive Rate across varying probability thresholds $\tau \in [0, 1]$.
- **Expected Calibration Error (ECE):**
  $$\text{ECE} = \sum_{m=1}^{M} \frac{|B_m|}{N} \left| \text{acc}(B_m) - \text{conf}(B_m) \right|$$
  where predictions are grouped into $M=10$ confidence bins $B_m$.
- **Segmentation Dice Coefficient:**
  $$\text{Dice} = \frac{2 |X \cap Y|}{|X| + |Y|}$$

---

## 3. Benchmark Dataset Standards

| Dataset | Modality | Annotations | Total Images | Primary Role in DRISHTI-LENS |
|---|---|---|---|---|
| **APTOS 2019** | Digital Fundus Photography | 5-class ICDR diagnosis (0–4) | 3,662 train + 1,928 test | Model fine-tuning, ROC analysis, ICDR validation |
| **DDR Dataset** | Colour Fundus Photography | Lesion segmentations (MA, EX, HE, NV) + ICDR | 13,673 images | Lesion segmentation Dice/IoU benchmarking |
| **MESSIDOR-2** | Colour Fundus | DR grade (0–4) & DME status | 1,748 images | External out-of-distribution validation |
| **IDRiD** | High-res Fundus | Pixel-level lesion masks + optic disc & fovea | 516 images | Optic disc localisation and vessel segmentation |

---

## 4. Current Repository Status & Real Evaluation Workflow

1. **Rule-Based Prototype vs. Trained Deep Learning Model:**
   - The Python AI pipeline (`backend/services/ai_pipeline/`) provides both a deterministic classical computer-vision and rule-based heuristic classifier, plus an inference wrapper for `dr_efficientnet_b4.pth`.
   - The MATLAB pipeline (`matlab/pipeline/`) provides image quality scoring (`image_quality_assessment.m`), CLAHE enhancement (`adaptive_enhancement.m`), and ICDR classification (`icdr_classifier.m`).
2. **Running the Empirical Validation:**
   ```bash
   # Python validation suite
   cd backend
   python validation/evaluate_model.py
   ```
   ```matlab
   % MATLAB validation suite
   cd matlab/validation
   results = evaluate_model('../data/aptos2019', './results');
   ```
3. **Clinical Output:**
   Upon running with dataset assets, results are automatically exported to `validation_results.csv`, `roc_curve.png`, and `confusion_matrix.png`.
