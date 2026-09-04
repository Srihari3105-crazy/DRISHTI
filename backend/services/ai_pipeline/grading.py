"""
DRISHTI-LENS — DR Grading (ICDR 0-4 Classification)
=====================================================
Implements rule-based ICDR grading from segmentation lesion counts as a
functional prototype, replacing the random severity = random.nextInt(5).

Architecture:
  This module provides TWO grading paths:

  Path A — Rule-based (always available):
    Maps detected lesion counts to ICDR criteria per the international scale.
    Produces deterministic output from segmentation results.
    This is a prototype — clinical validation has NOT been performed.

  Path B — Deep Learning (requires model file):
    Loads a pre-trained EfficientNet-B4 checkpoint via torchvision.
    If no checkpoint is available, falls back to Path A automatically.
    Fine-tuning on APTOS 2019 is performed by backend/validation/train.py.

ICDR Scale:
  0 = No DR         — no lesions
  1 = Mild NPDR     — microaneurysms only
  2 = Moderate NPDR — more than MAs but less than severe
  3 = Severe NPDR   — 4-2-1 rule: >20 IH in 4 quadrants OR VB in 2+ quad OR IRMA in 1+ quad
  4 = PDR           — neovascularization present

Referable DR = Level >= 2

DISCLAIMER:
  - Rule-based grading is deterministic but NOT clinically validated.
  - DL model accuracy has NOT been measured on a held-out test set.
  - Sensitivity and specificity are UNKNOWN until validation/evaluate_model.py runs.
  - Do NOT use outputs for clinical decisions without ophthalmologist review.
"""
from __future__ import annotations
import logging
import os
import numpy as np
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# Path to trained model checkpoint (populated after training)
MODEL_CHECKPOINT = os.environ.get(
    "DR_MODEL_CHECKPOINT",
    os.path.join(os.path.dirname(__file__), "..", "..", "assets", "models", "dr_efficientnet_b4.pth")
)

ICDR_LABELS = {
    0: "No DR",
    1: "Mild NPDR",
    2: "Moderate NPDR",
    3: "Severe NPDR",
    4: "Proliferative DR",
}

INPUT_SIZE = 512   # resize input to this before model inference


@dataclass
class GradingResult:
    severity_level: int          # 0–4
    severity_name: str           # ICDR label
    referable: bool              # True if level >= 2
    confidence: float            # Raw model/rule score [0,1] — NOT calibrated
    calibrated_confidence: Optional[float]  # After calibration (None if uncalibrated)
    method: str                  # 'rule_based' | 'dl_model'
    dme_risk: float              # Diabetic Macular Edema risk [0,1]
    efs_score: float             # Eye Finding Score composite [0,1]
    rule_trace: list             # [{rule_id, met, description, zones}]
    model_available: bool        # Whether DL model was loaded
    validated: bool = False      # True only once validation pipeline reports metrics
    disclaimer: str = (
        "AI-ASSISTED SCREENING — Ophthalmologist review required. "
        "Accuracy not clinically validated."
    )


# ─── Rule-based grading ────────────────────────────────────────────────────────

def _grade_rule_based(seg) -> GradingResult:
    """
    Map segmentation lesion counts to ICDR severity using clinical criteria.

    Parameters derived from:
      - ICDR severity scale (Wilkinson et al., Ophthalmology 2003)
      - Approximate lesion count thresholds from literature

    This is NOT a trained model. It maps detected candidate counts to ICDR
    criteria. It will be inaccurate when segmentation is inaccurate.
    """
    ma_count = seg.microaneurysms.candidate_count
    ex_count = seg.exudates.candidate_count
    he_count = seg.hemorrhages.candidate_count
    nv_count = seg.neovascularization.candidate_count

    rule_trace = []

    # Level 4: PDR — neovascularization
    if nv_count > 0:
        level = 4
        rule_trace = [
            {"rule_id": "ICDR-4.1", "met": True,
             "description": f"Neovascularization candidates detected ({nv_count})",
             "zones": ["peripapilar"]},
            {"rule_id": "ICDR-4.2", "met": he_count > 5,
             "description": f"Hemorrhage burden elevated ({he_count} candidates)",
             "zones": ["zone_1"] if he_count > 5 else []},
        ]
        confidence = float(np.clip(seg.neovascularization.confidence * 1.2, 0.3, 0.85))
        dme_risk = float(np.clip(0.4 + ex_count / 20.0, 0.4, 0.95))

    # Level 3: Severe NPDR — 4-2-1 rule approximation
    elif he_count >= 10 or (he_count >= 5 and ex_count >= 5):
        level = 3
        rule_trace = [
            {"rule_id": "ICDR-3.1", "met": True,
             "description": f"Extensive hemorrhages ({he_count} candidates, ICDR 4-2-1 rule approximation)",
             "zones": ["zone_1", "zone_2", "zone_3", "zone_4"]},
            {"rule_id": "ICDR-3.2", "met": ex_count >= 5,
             "description": f"Hard exudates present ({ex_count} regions)",
             "zones": ["zone_2"] if ex_count >= 5 else []},
            {"rule_id": "ICDR-3.3", "met": ma_count >= 5,
             "description": f"Microaneurysm burden ({ma_count} candidates)",
             "zones": ["zone_1"]},
        ]
        confidence = float(np.clip(0.45 + he_count / 30.0, 0.45, 0.75))
        dme_risk = float(np.clip(0.3 + ex_count / 25.0, 0.3, 0.85))

    # Level 2: Moderate NPDR
    elif (ma_count >= 3 and (ex_count >= 2 or he_count >= 2)) or he_count >= 3:
        level = 2
        rule_trace = [
            {"rule_id": "ICDR-2.1", "met": True,
             "description": "More than microaneurysms only",
             "zones": ["zone_1", "zone_2"]},
            {"rule_id": "ICDR-2.2", "met": ex_count >= 2,
             "description": f"Hard exudates present ({ex_count} regions)",
             "zones": ["zone_2"] if ex_count >= 2 else []},
            {"rule_id": "ICDR-2.3", "met": he_count >= 3,
             "description": f"Hemorrhages detected ({he_count} candidates)",
             "zones": ["zone_1"] if he_count >= 3 else []},
        ]
        confidence = float(np.clip(0.4 + ma_count / 20.0 + ex_count / 15.0, 0.4, 0.70))
        dme_risk = float(np.clip(0.2 + ex_count / 20.0, 0.15, 0.65))

    # Level 1: Mild NPDR — microaneurysms only
    elif ma_count >= 1:
        level = 1
        rule_trace = [
            {"rule_id": "ICDR-1.1", "met": True,
             "description": f"Microaneurysm candidates only ({ma_count} detected)",
             "zones": ["zone_1"]},
            {"rule_id": "ICDR-1.2", "met": False,
             "description": "No hard exudates detected",
             "zones": []},
        ]
        confidence = float(np.clip(0.35 + ma_count / 15.0, 0.35, 0.60))
        dme_risk = float(np.clip(0.05 + ma_count / 30.0, 0.05, 0.25))

    # Level 0: No DR
    else:
        level = 0
        rule_trace = [
            {"rule_id": "ICDR-0", "met": True,
             "description": "No lesion candidates detected",
             "zones": []},
        ]
        confidence = float(np.clip(0.5 + (5 - ma_count) / 10.0, 0.50, 0.75))
        dme_risk = 0.05

    # EFS score: composite of lesion burden (NOT clinically validated)
    efs_score = float(np.clip(
        1.0 - (ma_count / 30.0 + ex_count / 25.0 + he_count / 20.0 + nv_count * 0.3),
        0.05, 0.95
    ))

    return GradingResult(
        severity_level=level,
        severity_name=ICDR_LABELS[level],
        referable=level >= 2,
        confidence=confidence,
        calibrated_confidence=None,  # populated by calibration module
        method="rule_based_lesion_count_ICDR",
        dme_risk=dme_risk,
        efs_score=efs_score,
        rule_trace=rule_trace,
        model_available=False,
        validated=False,
    )


# ─── Deep Learning grading (optional) ─────────────────────────────────────────

def _load_dl_model():
    """
    Load EfficientNet-B4 DR classifier if checkpoint exists.
    Returns (model, device) or (None, None).
    """
    if not os.path.exists(MODEL_CHECKPOINT):
        logger.info(f"No DL model checkpoint at {MODEL_CHECKPOINT}. Using rule-based grading.")
        return None, None

    try:
        import torch
        import torchvision.models as models
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = models.efficientnet_b4(weights=None)
        # Replace classifier head for 5-class ICDR
        import torch.nn as nn
        model.classifier[1] = nn.Linear(model.classifier[1].in_features, 5)
        state = torch.load(MODEL_CHECKPOINT, map_location=device)
        model.load_state_dict(state)
        model.eval()
        model.to(device)
        logger.info(f"DL model loaded from {MODEL_CHECKPOINT} on {device}")
        return model, device
    except Exception as exc:
        logger.warning(f"Failed to load DL model: {exc}. Falling back to rule-based.")
        return None, None


_cached_model = None
_cached_device = None
_model_load_attempted = False


def _get_dl_model():
    global _cached_model, _cached_device, _model_load_attempted
    if not _model_load_attempted:
        _cached_model, _cached_device = _load_dl_model()
        _model_load_attempted = True
    return _cached_model, _cached_device


def _grade_dl(image_rgb: np.ndarray, model, device) -> GradingResult:
    """Run DL model inference on fundus image."""
    try:
        import torch
        import torchvision.transforms as T
        from PIL import Image

        transform = T.Compose([
            T.Resize((INPUT_SIZE, INPUT_SIZE)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        pil_img = Image.fromarray(image_rgb)
        tensor = transform(pil_img).unsqueeze(0).to(device)

        with torch.no_grad():
            logits = model(tensor)
            probs = torch.softmax(logits, dim=1).squeeze().cpu().numpy()

        level = int(np.argmax(probs))
        confidence = float(probs[level])
        dme_risk = float(np.clip(probs[2] + probs[3] * 1.5 + probs[4] * 2.0, 0.0, 1.0) / 3.5)
        efs_score = float(1.0 - (level / 4.0) * 0.7)

        rule_trace = [{
            "rule_id": f"DL-ICDR-{level}",
            "met": True,
            "description": f"Deep learning classifier: {ICDR_LABELS[level]} (prob={confidence:.3f})",
            "zones": []
        }]
        # Add class probabilities to trace
        for i, p in enumerate(probs):
            rule_trace.append({
                "rule_id": f"DL-class-{i}",
                "met": i == level,
                "description": f"{ICDR_LABELS[i]}: {p:.3f}",
                "zones": []
            })

        return GradingResult(
            severity_level=level,
            severity_name=ICDR_LABELS[level],
            referable=level >= 2,
            confidence=confidence,
            calibrated_confidence=None,
            method="efficientnet_b4_dl_classifier",
            dme_risk=dme_risk,
            efs_score=efs_score,
            rule_trace=rule_trace,
            model_available=True,
            validated=False,
        )
    except Exception as exc:
        logger.error(f"DL grading failed: {exc}", exc_info=True)
        raise


# ─── Public API ────────────────────────────────────────────────────────────────

def grade_image(image_rgb: np.ndarray, seg_result=None) -> GradingResult:
    """
    Grade a fundus image for DR severity.

    Attempts DL model first; falls back to rule-based grading using seg_result.

    Args:
        image_rgb:  uint8 numpy array (H, W, 3), RGB.
        seg_result: SegmentationResult from segmentation.py (used for rule-based).

    Returns:
        GradingResult. confidence is raw and NOT calibrated until calibration.py runs.
    """
    model, device = _get_dl_model()

    if model is not None:
        try:
            return _grade_dl(image_rgb, model, device)
        except Exception:
            logger.warning("DL inference failed, falling back to rule-based grading")

    # Rule-based fallback (requires segmentation result)
    if seg_result is not None:
        return _grade_rule_based(seg_result)

    # No segmentation and no model — return unknown with clear flag
    logger.warning("No model and no segmentation result — returning UNGRADED")
    return GradingResult(
        severity_level=-1,
        severity_name="UNGRADED",
        referable=False,
        confidence=0.0,
        calibrated_confidence=None,
        method="none_available",
        dme_risk=0.0,
        efs_score=0.0,
        rule_trace=[{"rule_id": "ERROR", "met": False,
                     "description": "Grading unavailable: no model and no segmentation", "zones": []}],
        model_available=False,
        validated=False,
        disclaimer="GRADING FAILED — no model checkpoint and no segmentation result provided.",
    )
