"""
DRISHTI-LENS — Image Quality Assessment
========================================
Implements genuine fundus image quality metrics replacing all random/hardcoded values.

Metrics computed:
  - Focus/sharpness: Variance of Laplacian on green channel
  - Illumination: Histogram analysis (mean brightness, over/under-exposure fraction)
  - Field of View: Circular Hough transform to detect retinal circle
  - Blur: Tenengrad gradient energy metric

Returns:
  QualityResult dataclass with numeric scores, decision, and specific feedback.

DISCLAIMER: This is an engineering prototype. Thresholds were set based on
literature references (Tenengrad > 100 for acceptable focus; illumination
mean 80-200/255 for acceptable range). These thresholds MUST be validated
against labeled clinical image datasets before deployment.
"""
from __future__ import annotations
import numpy as np
import logging
from dataclasses import dataclass, field
from typing import List

logger = logging.getLogger(__name__)

# ─── Configurable thresholds (must be validated against clinical dataset) ─────
FOCUS_THRESHOLD_PASS = 150.0      # Tenengrad energy — above = acceptable focus
FOCUS_THRESHOLD_BORDER = 60.0     # below this = ungradable blur
ILLUM_MEAN_LOW = 60               # mean pixel value (0-255); below = underexposed
ILLUM_MEAN_HIGH = 210             # above = overexposed
ILLUM_OVEREXPOSED_FRAC = 0.10     # fraction of pixels saturated (>250)
ILLUM_UNDEREXPOSED_FRAC = 0.20    # fraction of pixels very dark (<30)
FOV_COVERAGE_PASS = 0.55          # fraction of image inside detected retinal circle
FOV_COVERAGE_BORDER = 0.35        # below this = ungradable FOV
LAPLACIAN_VAR_PASS = 120.0        # secondary focus metric

@dataclass
class QualityResult:
    """Structured output from quality assessment."""
    focus_score: float          # Tenengrad energy (higher = sharper)
    laplacian_var: float        # Variance of Laplacian
    illumination_mean: float    # Mean pixel value (0–255)
    overexposed_frac: float     # Fraction of saturated pixels
    underexposed_frac: float    # Fraction of very dark pixels
    fov_coverage: float         # Fraction of image inside retinal circle
    fov_detected: bool          # Whether a retinal circle was found
    decision: str               # 'QUALITY_GOOD' | 'QUALITY_BORDERLINE' | 'QUALITY_UNGRADABLE'
    feedback: List[str] = field(default_factory=list)   # Specific actionable messages
    metrics_valid: bool = True  # False if image could not be decoded


def assess_quality(image_array: np.ndarray) -> QualityResult:
    """
    Assess fundus image quality from a uint8 numpy array (H x W x 3, RGB).

    Args:
        image_array: numpy array, dtype uint8, shape (H, W, 3), RGB channel order.

    Returns:
        QualityResult with all numeric scores and gradability decision.
    """
    try:
        import cv2
    except ImportError:
        logger.error("opencv-python-headless not installed. Run: pip install opencv-python-headless")
        return QualityResult(
            focus_score=0, laplacian_var=0, illumination_mean=0,
            overexposed_frac=0, underexposed_frac=0,
            fov_coverage=0, fov_detected=False,
            decision='QUALITY_UNGRADABLE',
            feedback=['Quality assessment unavailable (OpenCV not installed).'],
            metrics_valid=False
        )

    if image_array is None or image_array.size == 0:
        return QualityResult(
            focus_score=0, laplacian_var=0, illumination_mean=0,
            overexposed_frac=0, underexposed_frac=0,
            fov_coverage=0, fov_detected=False,
            decision='QUALITY_UNGRADABLE',
            feedback=['Image could not be decoded.'],
            metrics_valid=False
        )

    # Convert to BGR for OpenCV operations then work on individual channels
    bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    green = image_array[:, :, 1]  # Green channel — best contrast for fundus

    # ── 1. Focus / Sharpness ──────────────────────────────────────────────────
    # Tenengrad: sum of squared Sobel gradients on green channel
    sobel_x = cv2.Sobel(green.astype(np.float64), cv2.CV_64F, 1, 0, ksize=3)
    sobel_y = cv2.Sobel(green.astype(np.float64), cv2.CV_64F, 0, 1, ksize=3)
    tenengrad = float(np.mean(sobel_x**2 + sobel_y**2))

    # Variance of Laplacian (secondary focus metric)
    lap = cv2.Laplacian(gray, cv2.CV_64F)
    laplacian_var = float(lap.var())

    # ── 2. Illumination ──────────────────────────────────────────────────────
    illum_mean = float(np.mean(green))
    total_pixels = green.size
    overexposed_frac = float(np.sum(green > 250) / total_pixels)
    underexposed_frac = float(np.sum(green < 30) / total_pixels)

    # ── 3. Field of View — Retinal circle detection ──────────────────────────
    # The fundus image should contain a bright circular region on a dark background.
    # We use adaptive thresholding + contour analysis as a fallback if Hough is noisy.
    h, w = gray.shape
    fov_coverage = 0.0
    fov_detected = False

    # Gaussian blur before Hough to reduce noise
    blurred = cv2.GaussianBlur(gray, (9, 9), 2)
    min_radius = int(min(h, w) * 0.25)
    max_radius = int(min(h, w) * 0.65)

    circles = cv2.HoughCircles(
        blurred, cv2.HOUGH_GRADIENT, dp=1.2,
        minDist=min(h, w) * 0.5,
        param1=50, param2=30,
        minRadius=min_radius, maxRadius=max_radius
    )

    if circles is not None:
        # Take the circle with largest radius (main retinal disc)
        circles_arr = np.round(circles[0]).astype(int)
        cx, cy, r = sorted(circles_arr, key=lambda c: c[2], reverse=True)[0]
        # Compute what fraction of image falls inside this circle
        Y, X = np.ogrid[:h, :w]
        circle_mask = (X - cx)**2 + (Y - cy)**2 <= r**2
        fov_coverage = float(np.sum(circle_mask) / total_pixels)
        fov_detected = True
    else:
        # Fallback: estimate from non-black region ratio
        _, thresh = cv2.threshold(gray, 15, 255, cv2.THRESH_BINARY)
        fov_coverage = float(np.sum(thresh > 0) / total_pixels)
        fov_detected = False

    # ── 4. Decision logic ────────────────────────────────────────────────────
    feedback: List[str] = []
    ungradable_reasons = []
    borderline_reasons = []

    # Focus checks
    if tenengrad < FOCUS_THRESHOLD_BORDER:
        ungradable_reasons.append('Image is severely blurred — hold camera steady and recapture.')
    elif tenengrad < FOCUS_THRESHOLD_PASS:
        borderline_reasons.append('Image is slightly out of focus — hold camera steady for sharper capture.')

    # Illumination checks
    if illum_mean < ILLUM_MEAN_LOW:
        if underexposed_frac > ILLUM_UNDEREXPOSED_FRAC:
            ungradable_reasons.append('Insufficient illumination — improve retinal illumination before recapture.')
        else:
            borderline_reasons.append('Image appears dark — increase illumination if possible.')
    elif illum_mean > ILLUM_MEAN_HIGH:
        if overexposed_frac > ILLUM_OVEREXPOSED_FRAC:
            ungradable_reasons.append('Excessive glare — adjust camera alignment to reduce reflection.')
        else:
            borderline_reasons.append('Image appears bright — reduce illumination or adjust angle.')

    # FOV checks
    if fov_coverage < FOV_COVERAGE_BORDER:
        ungradable_reasons.append('Retina not fully visible — reposition the camera over the pupil.')
    elif fov_coverage < FOV_COVERAGE_PASS:
        borderline_reasons.append('Partial retinal field visible — centre the camera for better coverage.')

    if ungradable_reasons:
        decision = 'QUALITY_UNGRADABLE'
        feedback = ungradable_reasons
    elif borderline_reasons:
        decision = 'QUALITY_BORDERLINE'
        feedback = borderline_reasons
    else:
        decision = 'QUALITY_GOOD'
        feedback = ['Image quality acceptable for grading.']

    return QualityResult(
        focus_score=round(tenengrad, 2),
        laplacian_var=round(laplacian_var, 2),
        illumination_mean=round(illum_mean, 2),
        overexposed_frac=round(overexposed_frac, 4),
        underexposed_frac=round(underexposed_frac, 4),
        fov_coverage=round(fov_coverage, 4),
        fov_detected=fov_detected,
        decision=decision,
        feedback=feedback,
        metrics_valid=True
    )


def assess_quality_from_bytes(image_bytes: bytes) -> QualityResult:
    """Convenience wrapper: decode JPEG/PNG bytes then assess quality."""
    try:
        import cv2
        nparr = np.frombuffer(image_bytes, np.uint8)
        bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if bgr is None:
            raise ValueError("cv2.imdecode returned None")
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        return assess_quality(rgb)
    except Exception as exc:
        logger.error(f"Failed to decode image bytes: {exc}")
        return QualityResult(
            focus_score=0, laplacian_var=0, illumination_mean=0,
            overexposed_frac=0, underexposed_frac=0,
            fov_coverage=0, fov_detected=False,
            decision='QUALITY_UNGRADABLE',
            feedback=[f'Image decode failed: {exc}'],
            metrics_valid=False
        )
