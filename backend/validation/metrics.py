"""
DRISHTI-LENS — Clinical Validation Metrics
===========================================
Computes all required clinical validation metrics for the DR pipeline.

Metrics:
  - Sensitivity (recall for referable DR: level >= 2)
  - Specificity
  - Precision
  - F1-score
  - ROC-AUC
  - PR-AUC
  - Confusion matrix
  - Per-class accuracy
  - Brier score (from calibration module)
  - Expected Calibration Error (from calibration module)
  - Dice coefficient (for binary segmentation masks)
  - IoU (Jaccard index) for segmentation

IMPORTANT:
  - Metrics are computed from actual model predictions on a held-out test set.
  - Targets: Sensitivity > 90%, Specificity > 85% for referable DR (level >= 2).
  - If targets are NOT met, the actual numbers are reported honestly.
  - No results are fabricated.
"""
from __future__ import annotations
import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class BinaryMetrics:
    """Metrics for referable DR binary classification (positive = level >= 2)."""
    threshold: float
    sensitivity: float       # Recall for referable
    specificity: float
    precision: float
    f1_score: float
    roc_auc: float
    pr_auc: float
    confusion_matrix: np.ndarray   # [[TN, FP], [FN, TP]]
    n_positive: int          # True referable cases
    n_negative: int          # True non-referable cases
    meets_sensitivity_target: bool   # > 90%
    meets_specificity_target: bool   # > 85%
    note: str = ""


@dataclass
class MulticlassMetrics:
    """Per-class and macro metrics for ICDR 0–4 grading."""
    accuracy: float
    macro_f1: float
    per_class_sensitivity: List[float]   # one per ICDR level
    per_class_specificity: List[float]
    confusion_matrix: np.ndarray
    n_samples: int
    note: str = ""


@dataclass
class SegmentationMetrics:
    """Dice and IoU for binary segmentation masks."""
    dice: float
    iou: float
    sensitivity: float
    specificity: float
    n_images: int
    lesion_type: str
    note: str = "Computed only when ground-truth masks are available"


def compute_binary_metrics(
    y_true: np.ndarray,    # True ICDR labels (0–4)
    y_prob: np.ndarray,    # Predicted probabilities (N x 5)
    threshold: float = 0.5,
) -> BinaryMetrics:
    """
    Compute binary classification metrics for referable DR.

    Positive = ICDR level >= 2 (referable)
    Negative = ICDR level < 2

    Args:
        y_true:    1D int array of true ICDR levels (0–4).
        y_prob:    2D float array of class probabilities (N x 5).
        threshold: Decision threshold on P(referable) = sum(P(level>=2)).

    Returns:
        BinaryMetrics dataclass with all computed values.
    """
    from sklearn.metrics import roc_auc_score, precision_recall_curve, auc

    y_true_binary = (y_true >= 2).astype(int)  # 1 = referable
    p_referable = y_prob[:, 2:].sum(axis=1)    # P(level >= 2)
    y_pred_binary = (p_referable >= threshold).astype(int)

    TP = int(((y_pred_binary == 1) & (y_true_binary == 1)).sum())
    FP = int(((y_pred_binary == 1) & (y_true_binary == 0)).sum())
    FN = int(((y_pred_binary == 0) & (y_true_binary == 1)).sum())
    TN = int(((y_pred_binary == 0) & (y_true_binary == 0)).sum())

    sensitivity = TP / max(TP + FN, 1)
    specificity = TN / max(TN + FP, 1)
    precision = TP / max(TP + FP, 1)
    f1 = (2 * precision * sensitivity) / max(precision + sensitivity, 1e-9)

    try:
        roc_auc = float(roc_auc_score(y_true_binary, p_referable))
    except ValueError:
        roc_auc = float("nan")

    try:
        prec_curve, rec_curve, _ = precision_recall_curve(y_true_binary, p_referable)
        pr_auc = float(auc(rec_curve, prec_curve))
    except ValueError:
        pr_auc = float("nan")

    cm = np.array([[TN, FP], [FN, TP]])

    return BinaryMetrics(
        threshold=threshold,
        sensitivity=round(sensitivity, 4),
        specificity=round(specificity, 4),
        precision=round(precision, 4),
        f1_score=round(f1, 4),
        roc_auc=round(roc_auc, 4),
        pr_auc=round(pr_auc, 4),
        confusion_matrix=cm,
        n_positive=int(y_true_binary.sum()),
        n_negative=int((1 - y_true_binary).sum()),
        meets_sensitivity_target=sensitivity > 0.90,
        meets_specificity_target=specificity > 0.85,
        note=(
            f"Threshold={threshold}. "
            f"Sensitivity {'MEETS' if sensitivity > 0.90 else 'DOES NOT MEET'} >90% target. "
            f"Specificity {'MEETS' if specificity > 0.85 else 'DOES NOT MEET'} >85% target."
        )
    )


def find_optimal_threshold(y_true: np.ndarray, y_prob: np.ndarray,
                            target_sensitivity: float = 0.90) -> float:
    """
    Find the lowest threshold achieving at least target_sensitivity.
    Used to find the operating point for referable DR.

    Returns threshold value (float between 0 and 1).
    """
    from sklearn.metrics import roc_curve
    y_true_binary = (y_true >= 2).astype(int)
    p_referable = y_prob[:, 2:].sum(axis=1)

    fpr, tpr, thresholds = roc_curve(y_true_binary, p_referable)
    # Find thresholds where sensitivity (tpr) >= target
    valid = thresholds[tpr >= target_sensitivity]
    if len(valid) == 0:
        return 0.5  # fallback
    # Return the highest (most specific) threshold meeting sensitivity target
    return float(valid[-1])


def compute_multiclass_metrics(
    y_true: np.ndarray,    # True ICDR labels (0–4)
    y_pred: np.ndarray,    # Predicted ICDR labels (0–4)
) -> MulticlassMetrics:
    """Compute per-class and macro-averaged metrics for 5-class ICDR grading."""
    from sklearn.metrics import confusion_matrix, f1_score, accuracy_score

    acc = float(accuracy_score(y_true, y_pred))
    macro_f1 = float(f1_score(y_true, y_pred, average='macro', zero_division=0))
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1, 2, 3, 4])

    per_class_sens = []
    per_class_spec = []
    n_classes = 5
    for c in range(n_classes):
        tp = cm[c, c]
        fn = cm[c, :].sum() - tp
        fp = cm[:, c].sum() - tp
        tn = cm.sum() - tp - fn - fp
        sens = tp / max(tp + fn, 1)
        spec = tn / max(tn + fp, 1)
        per_class_sens.append(round(float(sens), 4))
        per_class_spec.append(round(float(spec), 4))

    return MulticlassMetrics(
        accuracy=round(acc, 4),
        macro_f1=round(macro_f1, 4),
        per_class_sensitivity=per_class_sens,
        per_class_specificity=per_class_spec,
        confusion_matrix=cm,
        n_samples=len(y_true),
    )


def compute_dice(pred_mask: np.ndarray, gt_mask: np.ndarray, eps: float = 1e-7) -> float:
    """
    Compute Dice coefficient between binary prediction and ground-truth masks.
    Both masks must be binary (0 or 1), same shape.
    """
    pred = (pred_mask > 0).astype(float)
    gt = (gt_mask > 0).astype(float)
    intersection = (pred * gt).sum()
    return float((2 * intersection + eps) / (pred.sum() + gt.sum() + eps))


def compute_iou(pred_mask: np.ndarray, gt_mask: np.ndarray, eps: float = 1e-7) -> float:
    """Compute Intersection over Union (Jaccard index)."""
    pred = (pred_mask > 0).astype(float)
    gt = (gt_mask > 0).astype(float)
    intersection = (pred * gt).sum()
    union = pred.sum() + gt.sum() - intersection
    return float((intersection + eps) / (union + eps))


def compute_segmentation_metrics(
    pred_masks: List[np.ndarray],
    gt_masks: List[np.ndarray],
    lesion_type: str,
) -> SegmentationMetrics:
    """
    Compute Dice and IoU averaged over a set of image masks.

    Args:
        pred_masks: List of binary predicted masks (one per image).
        gt_masks:   List of binary ground-truth masks (one per image).
        lesion_type: Name for reporting.

    Returns:
        SegmentationMetrics with mean Dice and IoU.
    """
    if not pred_masks or len(pred_masks) != len(gt_masks):
        return SegmentationMetrics(
            dice=float("nan"), iou=float("nan"),
            sensitivity=float("nan"), specificity=float("nan"),
            n_images=0, lesion_type=lesion_type,
            note="No masks provided or length mismatch"
        )

    dice_vals, iou_vals, sens_vals, spec_vals = [], [], [], []
    for pred, gt in zip(pred_masks, gt_masks):
        dice_vals.append(compute_dice(pred, gt))
        iou_vals.append(compute_iou(pred, gt))
        pred_b = (pred > 0).astype(float).ravel()
        gt_b = (gt > 0).astype(float).ravel()
        tp = (pred_b * gt_b).sum()
        fn = ((1 - pred_b) * gt_b).sum()
        fp = (pred_b * (1 - gt_b)).sum()
        tn = ((1 - pred_b) * (1 - gt_b)).sum()
        sens_vals.append(tp / max(tp + fn, 1))
        spec_vals.append(tn / max(tn + fp, 1))

    return SegmentationMetrics(
        dice=round(float(np.mean(dice_vals)), 4),
        iou=round(float(np.mean(iou_vals)), 4),
        sensitivity=round(float(np.mean(sens_vals)), 4),
        specificity=round(float(np.mean(spec_vals)), 4),
        n_images=len(pred_masks),
        lesion_type=lesion_type,
    )
