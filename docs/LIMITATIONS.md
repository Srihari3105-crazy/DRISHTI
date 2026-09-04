# DRISHTI-LENS — Known Limitations & Clinical Boundary Conditions

In accordance with medical AI safety guidelines and transparent engineering ethics, this document enumerates the boundary conditions and operational limits of the current DRISHTI-LENS prototype.

---

## 1. Clinical Limitations & Diagnostic Boundary
1. **Screening, Not Definitive Diagnosis:**  
   DRISHTI-LENS is explicitly engineered as an **AI-assisted triage and referral recommendation system**. It does NOT replace comprehensive ophthalmological examination (slit-lamp biomicroscopy, optical coherence tomography [OCT], or fluorescein angiography).
2. **Prototype Algorithm Nature:**  
   The classical computer-vision segmentation algorithms (top-hat morphology, Matched filtering) are prototype implementations. While robust for standard contrast fundus images, severe cataracts, corneal opacities, or extreme vitreous hemorrhages can cause false-positive detections.
3. **Monocular 2D Fundus Photographs:**  
   The system assesses single-field non-mydriatic or mydriatic fundus images. Peripheral retinal lesions located beyond the 45-to-50 degree field of view are not captured.

---

## 2. Technical Limitations & Environmental Constraints
1. **Device Hardware Independence:**  
   Image quality metrics (Tenengrad, brightness histograms) have calibrated default thresholds ($150$ for sharpness, $60-210$ for illumination). Different camera optics (e.g., Remidio, Forus 3nethra, smartphone adapters) require per-device baseline calibration.
2. **Computational Load on Low-End Mobile Devices:**  
   Full deep learning inference with backpropagation (Grad-CAM) requires significant RAM (~300MB). On ultra-budget mobile hardware, offline mode falls back to rule-based triage and offloads heavy Grad-CAM rendering to the PHC hub server upon synchronization.
3. **Eye Laterality Heuristic:**  
   Foveal geometric estimation currently assumes standard temporal orientation. Future versions will incorporate an automatic anatomical landmark classifier to dynamically detect left eye (OS) vs. right eye (OD).
