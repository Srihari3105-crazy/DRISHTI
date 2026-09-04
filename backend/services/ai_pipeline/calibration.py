"""
DRISHTI-LENS — Confidence Calibration
=======================================
Implements temperature scaling for DR classifier confidence calibration.

Temperature scaling (Guo et al., ICML 2017):
  - Divides logits by a learned temperature T before softmax.
  - T > 1 makes probabilities less extreme (more calibrated).
  - T < 1 makes probabilities more extreme (overconfident).
  - T is fit on a validation set by minimising NLL.

Calibration metrics:
  - Brier Score: mean squared error between probabilities and one-hot labels.
  - Expected Calibration Error (ECE): weighted average of |accuracy - confidence|
    across M equal-frequency bins.

DISCLAIMER:
  - Calibration is only performed when a validation set is available.
  - Until calibration is run, calibrated_confidence = None in GradingResult.
  - Calibration does NOT improve model accuracy — only probability estimates.
  - These are still NOT clinical certainty values.
"""
from __future__ import annotations
import numpy as np
import logging
import os
import json
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

CALIBRATION_STATE_PATH = os.environ.get(
    "CALIBRATION_STATE_PATH",
    os.path.join(os.path.dirname(__file__), "..", "..", "assets", "models", "calibration_state.json")
)


@dataclass
class CalibrationState:
    temperature: float = 1.0       # T=1.0 = no calibration (identity)
    fitted: bool = False           # True only after fit() was run on validation data
    brier_score_before: Optional[float] = None
    brier_score_after: Optional[float] = None
    ece_before: Optional[float] = None
    ece_after: Optional[float] = None
    n_validation_samples: int = 0
    note: str = "NOT CALIBRATED — temperature=1.0 (identity)"


_calibration_state: Optional[CalibrationState] = None


def _load_calibration_state() -> CalibrationState:
    """Load fitted calibration temperature from disk if available."""
    global _calibration_state
    if _calibration_state is not None:
        return _calibration_state

    if os.path.exists(CALIBRATION_STATE_PATH):
        try:
            with open(CALIBRATION_STATE_PATH, "r") as f:
                data = json.load(f)
            state = CalibrationState(**data)
            logger.info(f"Loaded calibration state: T={state.temperature:.4f}, fitted={state.fitted}")
            _calibration_state = state
            return state
        except Exception as exc:
            logger.warning(f"Could not load calibration state: {exc}")

    _calibration_state = CalibrationState()
    return _calibration_state


def calibrate_probability(raw_confidence: float, severity_level: int) -> Optional[float]:
    """
    Apply temperature scaling to a raw model confidence value.

    Args:
        raw_confidence: Raw softmax probability for predicted class [0,1].
        severity_level: Predicted ICDR level (0–4).

    Returns:
        Calibrated probability, or None if calibration has not been fitted.
    """
    state = _load_calibration_state()
    if not state.fitted:
        return None  # Explicitly None — do not fabricate a calibrated value

    # Temperature scaling: calibrated_prob ≈ softmax(logit / T)
    # Approximate inverse softmax → scale → re-apply softmax
    if raw_confidence <= 0 or raw_confidence >= 1:
        return float(np.clip(raw_confidence, 0.01, 0.99))

    # log-odds form of temperature scaling
    logit = np.log(raw_confidence / (1 - raw_confidence))
    scaled_logit = logit / state.temperature
    calibrated = float(1.0 / (1.0 + np.exp(-scaled_logit)))
    return round(calibrated, 4)


def compute_ece(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    """
    Compute Expected Calibration Error.

    Args:
        y_true: 1D array of true class labels (int).
        y_prob: 2D array of predicted probabilities (N x C).
        n_bins: Number of confidence bins.

    Returns:
        ECE value [0,1]; lower is better.
    """
    confidences = np.max(y_prob, axis=1)
    predictions = np.argmax(y_prob, axis=1)
    correct = (predictions == y_true).astype(float)

    bin_edges = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        lo, hi = bin_edges[i], bin_edges[i + 1]
        mask = (confidences >= lo) & (confidences < hi)
        if mask.sum() == 0:
            continue
        acc = correct[mask].mean()
        conf = confidences[mask].mean()
        ece += mask.sum() / len(y_true) * abs(acc - conf)
    return float(ece)


def compute_brier_score(y_true: np.ndarray, y_prob: np.ndarray, n_classes: int = 5) -> float:
    """
    Compute multiclass Brier score.

    Args:
        y_true: 1D array of true labels (int, 0–n_classes-1).
        y_prob: 2D array of predicted probabilities (N x C).
        n_classes: Number of classes.

    Returns:
        Brier score [0,2]; lower is better. Perfect = 0.
    """
    y_onehot = np.eye(n_classes)[y_true]
    return float(np.mean(np.sum((y_prob - y_onehot) ** 2, axis=1)))


def fit_temperature_scaling(logits: np.ndarray, y_true: np.ndarray,
                             n_classes: int = 5, max_iter: int = 100) -> CalibrationState:
    """
    Fit temperature T on a validation set by minimising NLL.

    Args:
        logits: Raw model logits before softmax (N x C).
        y_true: True class labels (N,) int.
        n_classes: Number of output classes.
        max_iter: Scipy optimisation iterations.

    Returns:
        Fitted CalibrationState (also saves to disk).
    """
    from scipy.optimize import minimize_scalar
    from scipy.special import softmax

    def nll(T):
        scaled = logits / max(T, 1e-6)
        probs = softmax(scaled, axis=1)
        probs = np.clip(probs, 1e-7, 1.0)
        nll_val = -np.mean(np.log(probs[np.arange(len(y_true)), y_true]))
        return nll_val

    # Before calibration
    probs_before = softmax(logits, axis=1)
    brier_before = compute_brier_score(y_true, probs_before, n_classes)
    ece_before = compute_ece(y_true, probs_before)

    # Optimise T in (0.1, 10.0)
    result = minimize_scalar(nll, bounds=(0.1, 10.0), method='bounded',
                             options={'maxiter': max_iter})
    T_opt = float(result.x)

    # After calibration
    probs_after = softmax(logits / T_opt, axis=1)
    brier_after = compute_brier_score(y_true, probs_after, n_classes)
    ece_after = compute_ece(y_true, probs_after)

    state = CalibrationState(
        temperature=T_opt,
        fitted=True,
        brier_score_before=round(brier_before, 5),
        brier_score_after=round(brier_after, 5),
        ece_before=round(ece_before, 5),
        ece_after=round(ece_after, 5),
        n_validation_samples=len(y_true),
        note=f"Fitted temperature scaling T={T_opt:.4f} on {len(y_true)} validation samples"
    )

    # Persist
    try:
        os.makedirs(os.path.dirname(CALIBRATION_STATE_PATH), exist_ok=True)
        with open(CALIBRATION_STATE_PATH, "w") as f:
            import dataclasses
            json.dump(dataclasses.asdict(state), f, indent=2)
        logger.info(f"Calibration state saved: T={T_opt:.4f}, ECE {ece_before:.4f} -> {ece_after:.4f}")
    except Exception as exc:
        logger.error(f"Could not save calibration state: {exc}")

    global _calibration_state
    _calibration_state = state
    return state


def get_calibration_report() -> dict:
    """Return current calibration state as a dict for API responses."""
    state = _load_calibration_state()
    import dataclasses
    d = dataclasses.asdict(state)
    d["calibration_status"] = "CALIBRATED" if state.fitted else "NOT_CALIBRATED"
    d["warning"] = (
        "Confidence scores are NOT clinically validated probabilities. "
        "They reflect model uncertainty only."
    )
    return d
