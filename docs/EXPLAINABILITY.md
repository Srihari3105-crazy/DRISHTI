# DRISHTI-LENS — Clinical Explainability & Visual Verification

**SIH 2026 Problem Statement Compliance Document**

---

## 1. Why Explainability is a Clinical Requirement
In medical computer vision—particularly for rural and remote screening—deep learning models operating as "black boxes" cannot be legally or ethically accepted for medical diagnosis. Ophthalmologists require verifiable visual justification to:
1. Confirm that model attention aligns with pathological retinal abnormalities rather than imaging artefacts (such as lens dust, eyelash shadows, or camera vignetting).
2. Triage urgency based on proximity of hard exudates and hemorrhages to the foveal avascular zone (DME risk).
3. Adjudicate borderline grades within the targeted **<30-second review window**.

---

## 2. Multi-Tier Explainability Architecture

```
                       ┌───────────────────────────────┐
                       │     Fundus Input Capture      │
                       └──────────────┬────────────────┘
                                      │
              ┌───────────────────────┴───────────────────────┐
              │                                               │
              ▼                                               ▼
┌───────────────────────────┐                   ┌───────────────────────────┐
│ 1. Anatomical Landmarks   │                   │ 2. Feature Activation     │
│  - Optic Disc Circle (Grn)│                   │  - PyTorch Hook on Conv   │
│  - Fovea Centralis (Amb)  │                   │  - Channel Gradients      │
│  - Vascular Tree (Cyan)   │                   │  - Normalized Heatmap     │
└─────────────┬─────────────┘                   └─────────────┬─────────────┘
              │                                               │
              ▼                                               ▼
┌───────────────────────────┐                   ┌───────────────────────────┐
│ 3. Lesion-Level Evidence  │                   │ 4. Clinical Evidence Map  │
│  - Microaneurysms (Red)   │                   │  - Grad-CAM Overlay       │
│  - Hard Exudates (Yellow) │                   │  - High-attention Bounding│
│  - Hemorrhages (Purple)   │                   │  - 40% JET Colormap Blend │
└─────────────┬─────────────┘                   └─────────────┬─────────────┘
              │                                               │
              └───────────────────────┬───────────────────────┘
                                      │
                                      ▼
                       ┌───────────────────────────────┐
                       │ 5. Human-in-the-Loop Review   │
                       │  - ICDR Rule Trace Checklist  │
                       │  - Doctor Adjudication Action │
                       │  - <30s Stopwatch Audit Log   │
                       └───────────────────────────────┘
```

### 2.1 Grad-CAM Implementation Details (`gradcam.py` & `gradcam.m`)
- **Target Layer:** Final convolutional depthwise separable block of the EfficientNet-B4 backbone (`features[-1][0]`).
- **Gradient Weights:** Global average pooling of backward gradients $\alpha_k^c = \frac{1}{Z} \sum_i \sum_j \frac{\partial y^c}{\partial A_{i,j}^k}$.
- **ReLu Rectification:** Ensures only features positively contributing to the predicted ICDR grade are rendered in the heatmap.
- **Color Mapping:** JET colormap overlay at 40% opacity on top of the original fundus image.

### 2.2 Symbolic ICDR Rule Tracing
Rather than merely returning an integer severity score, every screening generates a transparent checklist mapped to clinical guidelines (Wilkinson et al., 2003):
- `ICDR-1.1`: Microaneurysms only (Mild NPDR)
- `ICDR-2.1`: More than microaneurysms (Moderate NPDR)
- `ICDR-3.3`: >20 intraretinal hemorrhages in multiple quadrants (Severe NPDR)
- `ICDR-4.1`: Peripapillary / retinal neovascularization (Proliferative DR)
