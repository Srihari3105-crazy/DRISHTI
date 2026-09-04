"""
DRISHTI-LENS — Retinal Structure Segmentation
===============================================
Implements genuine fundus image segmentation algorithms to replace all
hardcoded RLE strings and random lesion outputs.

Algorithms used:
  Optic Disc:      Bright-region detection on red channel + morphological refinement
  Vessels:         Green-channel inversion + top-hat + Frangi-like vesselness
  Microaneurysms:  Top-hat transform + blob detection on green channel
  Exudates:        Bright-lesion detection after optic disc exclusion
  Hemorrhages:     Dark-lesion detection on green channel
  Neovascularization: Fine vessel network near disc (heuristic proximity score)
  Fovea:           Geometric estimation relative to optic disc

IMPORTANT DISCLAIMERS:
  - All algorithms are prototype-grade implementations using classical CV techniques.
  - NO deep-learning segmentation model is bundled (models/ directory is empty).
  - Performance has NOT been measured against a clinical ground-truth dataset.
  - Dice, IoU, sensitivity, specificity metrics are NOT reported here — see
    backend/validation/ for that pipeline once a labeled dataset is available.
  - Results must be reviewed by an ophthalmologist before clinical use.
  - Do NOT interpret output counts as clinically validated lesion counts.
"""
from __future__ import annotations
import numpy as np
import logging
from dataclasses import dataclass, field
from typing import Optional, Tuple, List

logger = logging.getLogger(__name__)


# ─── Output structures ─────────────────────────────────────────────────────────

@dataclass
class OpticDiscResult:
    mask: Optional[np.ndarray]        # Binary mask (H x W), uint8, 255 = disc
    center_xy: Optional[Tuple[int, int]]
    radius_px: Optional[int]
    confidence: float                 # Heuristic 0–1; NOT a calibrated probability
    method: str = "bright_region_morphological"
    validated: bool = False           # True only if validated against GT dataset


@dataclass
class FoveaResult:
    center_xy: Optional[Tuple[int, int]]
    confidence: float
    method: str = "geometric_estimate_from_OD"
    validated: bool = False
    note: str = "Geometric estimate only — requires deep learning model for clinical use"


@dataclass
class VesselResult:
    mask: Optional[np.ndarray]        # Binary vessel mask (H x W), uint8
    probability_map: Optional[np.ndarray]  # Float32 probability per pixel
    method: str = "green_channel_tophat_threshold"
    dice: Optional[float] = None      # Populated only if GT mask provided
    iou: Optional[float] = None
    validated: bool = False


@dataclass
class LesionResult:
    """Generic lesion detection result."""
    lesion_type: str                  # 'MA' | 'EX' | 'HE' | 'NV'
    mask: Optional[np.ndarray]        # Binary mask (H x W)
    candidate_count: int
    confidence: float                 # Heuristic score 0–1
    bounding_boxes: List[Tuple]       # [(x, y, w, h), ...]
    method: str
    validated: bool = False
    disclaimer: str = (
        "Prototype algorithm — not clinically validated. "
        "Counts do not represent ground-truth lesion counts."
    )


@dataclass
class SegmentationResult:
    """Aggregate segmentation output for one fundus image."""
    optic_disc: OpticDiscResult
    fovea: FoveaResult
    vessels: VesselResult
    microaneurysms: LesionResult
    exudates: LesionResult
    hemorrhages: LesionResult
    neovascularization: LesionResult
    image_shape: Tuple[int, int]      # (H, W)
    error: str = ""
    validated: bool = False


# ─── Helper utilities ──────────────────────────────────────────────────────────

def _require_cv2():
    try:
        import cv2
        return cv2
    except ImportError:
        raise RuntimeError(
            "opencv-python-headless is required. "
            "Install with: pip install opencv-python-headless"
        )


def _empty_lesion(lesion_type: str, shape: tuple) -> LesionResult:
    return LesionResult(
        lesion_type=lesion_type,
        mask=np.zeros(shape, dtype=np.uint8),
        candidate_count=0,
        confidence=0.0,
        bounding_boxes=[],
        method="not_run",
        validated=False,
    )


# ─── Optic Disc ────────────────────────────────────────────────────────────────

def detect_optic_disc(rgb: np.ndarray) -> OpticDiscResult:
    """
    Localise optic disc using bright-region detection on the red channel.

    The optic disc is typically the brightest large circular region.
    Steps:
      1. Extract red channel (OD appears bright in red).
      2. Gaussian blur to suppress noise.
      3. Threshold to keep top-5% brightest pixels.
      4. Morphological closing to fill gaps.
      5. Find largest contour → fit enclosing circle.

    This is a rule-based approach. Accuracy degrades with poor image quality
    or severe DR (bright exudates can confuse detection).
    """
    cv2 = _require_cv2()
    h, w = rgb.shape[:2]

    red = rgb[:, :, 0]
    blurred = cv2.GaussianBlur(red, (15, 15), 0)

    # Threshold at 95th percentile of non-black pixels
    non_black = blurred[blurred > 10]
    if len(non_black) == 0:
        return OpticDiscResult(mask=None, center_xy=None, radius_px=None, confidence=0.0)

    thresh_val = int(np.percentile(non_black, 92))
    _, binary = cv2.threshold(blurred, thresh_val, 255, cv2.THRESH_BINARY)

    # Morphological closing
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25))
    closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    filled = cv2.morphologyEx(closed, cv2.MORPH_DILATE, kernel, iterations=2)

    contours, _ = cv2.findContours(filled, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return OpticDiscResult(mask=None, center_xy=None, radius_px=None, confidence=0.1)

    # Pick largest contour by area
    largest = max(contours, key=cv2.contourArea)
    (cx, cy), radius = cv2.minEnclosingCircle(largest)
    cx, cy, radius = int(cx), int(cy), int(radius)

    # Build mask
    disc_mask = np.zeros((h, w), dtype=np.uint8)
    cv2.circle(disc_mask, (cx, cy), radius, 255, -1)

    # Heuristic confidence: expected OD size is ~1/7 of image width
    expected_r = w / 14
    size_ratio = min(radius, expected_r) / max(radius, expected_r)
    confidence = float(np.clip(size_ratio * 0.8, 0.0, 0.85))  # cap at 0.85 — not a calibrated prob

    return OpticDiscResult(
        mask=disc_mask,
        center_xy=(cx, cy),
        radius_px=radius,
        confidence=confidence,
        method="red_channel_bright_region_morphological",
        validated=False,
    )


# ─── Fovea ─────────────────────────────────────────────────────────────────────

def estimate_fovea(rgb: np.ndarray, od_result: OpticDiscResult) -> FoveaResult:
    """
    Estimate fovea location geometrically relative to the optic disc.

    The fovea is typically located ~2.5 optic disc diameters (OD) temporal
    (nasal-to-temporal direction) from the OD center, and slightly inferior.

    This is a geometric estimate ONLY. It will be incorrect for:
      - Low-quality or off-centre images
      - Images where OD was not detected
      - Unusual retinal anatomy

    A deep learning approach (e.g., landmark detection network) is required
    for reliable clinical fovea localisation.
    """
    if od_result.center_xy is None or od_result.radius_px is None:
        h, w = rgb.shape[:2]
        # Fall back to image centre estimate
        return FoveaResult(
            center_xy=(w // 2, h // 2),
            confidence=0.1,
            method="image_centre_fallback_no_OD_detected",
            validated=False,
            note="OD not detected — fovea location is approximate image centre only"
        )

    cx, cy = od_result.center_xy
    r = od_result.radius_px
    od_diameter = 2 * r

    # Assume temporal (right) side — valid for right eye (OD)
    # For left eye, the fovea is on the other side; eye laterality not yet implemented
    fovea_x = cx + int(2.5 * od_diameter)
    fovea_y = cy + int(0.05 * od_diameter)  # slightly inferior

    # Clamp to image bounds
    h, w = rgb.shape[:2]
    fovea_x = int(np.clip(fovea_x, 0, w - 1))
    fovea_y = int(np.clip(fovea_y, 0, h - 1))

    return FoveaResult(
        center_xy=(fovea_x, fovea_y),
        confidence=0.4,  # Low: geometric estimate only
        method="geometric_2.5_OD_diameters_temporal",
        validated=False,
        note="Geometric estimate only. Eye laterality not implemented. Not for clinical use."
    )


# ─── Vessel Segmentation ───────────────────────────────────────────────────────

def segment_vessels(rgb: np.ndarray) -> VesselResult:
    """
    Segment retinal vessels using green channel + morphological top-hat transform.

    Method:
      1. Extract green channel (vessels show highest contrast there).
      2. Apply CLAHE for local contrast enhancement.
      3. Morphological black top-hat to detect dark thin structures (vessels).
      4. Threshold with Otsu's method.
      5. Remove small blobs below minimum vessel size.

    This is a simplified matched-filter-inspired approach. Production systems
    use U-Net or similar segmentation networks for better performance.

    Dice and IoU are NOT reported here — see validation pipeline.
    """
    cv2 = _require_cv2()
    h, w = rgb.shape[:2]

    green = rgb[:, :, 1]
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    green_eq = clahe.apply(green)

    # Black top-hat: isolates dark structures (vessels) on bright background
    kernel_line = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    top_hat = cv2.morphologyEx(green_eq, cv2.MORPH_BLACKHAT, kernel_line)

    # Otsu threshold
    _, vessel_mask = cv2.threshold(top_hat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Remove very small components (noise)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(vessel_mask, connectivity=8)
    min_vessel_pixels = 20
    clean_mask = np.zeros_like(vessel_mask)
    for lbl in range(1, num_labels):
        if stats[lbl, cv2.CC_STAT_AREA] >= min_vessel_pixels:
            clean_mask[labels == lbl] = 255

    prob_map = top_hat.astype(np.float32) / 255.0

    return VesselResult(
        mask=clean_mask,
        probability_map=prob_map,
        method="green_channel_CLAHE_blackhat_otsu",
        validated=False,
    )


# ─── Microaneurysms ─────────────────────────────────────────────────────────────

def detect_microaneurysms(rgb: np.ndarray, od_mask: Optional[np.ndarray] = None) -> LesionResult:
    """
    Detect microaneurysm candidates using top-hat transform + blob detection.

    Method:
      1. Green channel CLAHE.
      2. Black top-hat with small structuring element (~5px) isolates small dark blobs.
      3. Threshold + connected components to find candidate blobs.
      4. Filter by size (3–20 pixels diameter = MA candidate range).
      5. Exclude optic disc region if mask provided.

    MAs are the smallest lesions (~10–100 µm in vivo). At typical fundus camera
    resolution (2–4µm/pixel), they appear as 3–15 pixel dark dots.
    Sub-pixel localisation is not implemented in this prototype.

    NOTE: This will produce false positives in images with noise or artefacts.
    Clinical-grade MA detection requires deep learning (e.g., DIARETDB1 trained model).
    """
    cv2 = _require_cv2()
    h, w = rgb.shape[:2]
    shape = (h, w)

    green = rgb[:, :, 1]
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    green_eq = clahe.apply(green)

    # Small structuring element for MAs
    se_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    top_hat = cv2.morphologyEx(green_eq, cv2.MORPH_BLACKHAT, se_small)

    # Threshold at ~95th percentile of top-hat response
    thresh_val = int(np.percentile(top_hat, 95))
    if thresh_val < 5:
        thresh_val = 5
    _, binary = cv2.threshold(top_hat, thresh_val, 255, cv2.THRESH_BINARY)

    # Exclude OD region
    if od_mask is not None:
        dilated_od = cv2.dilate(od_mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (20, 20)))
        binary[dilated_od > 0] = 0

    # Filter blobs by size
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)
    ma_mask = np.zeros(shape, dtype=np.uint8)
    bboxes = []
    for lbl in range(1, num_labels):
        area = stats[lbl, cv2.CC_STAT_AREA]
        if 3 <= area <= 120:  # approximate MA size range at typical resolution
            ma_mask[labels == lbl] = 255
            x = stats[lbl, cv2.CC_STAT_LEFT]
            y = stats[lbl, cv2.CC_STAT_TOP]
            bw = stats[lbl, cv2.CC_STAT_WIDTH]
            bh = stats[lbl, cv2.CC_STAT_HEIGHT]
            bboxes.append((x, y, bw, bh))

    candidate_count = len(bboxes)
    confidence = float(np.clip(min(candidate_count, 20) / 20.0 * 0.6, 0.0, 0.6))

    return LesionResult(
        lesion_type="MA",
        mask=ma_mask,
        candidate_count=candidate_count,
        confidence=confidence,
        bounding_boxes=bboxes,
        method="green_channel_CLAHE_blackhat_blob_filter",
        validated=False,
    )


# ─── Exudates ──────────────────────────────────────────────────────────────────

def detect_exudates(rgb: np.ndarray, od_mask: Optional[np.ndarray] = None) -> LesionResult:
    """
    Detect hard exudate candidates (bright lesions) on fundus image.

    Exudates appear as bright yellowish deposits. Detected by finding bright
    regions after excluding the optic disc.

    Method:
      1. Luminance channel from LAB.
      2. Top-hat (white) with medium structuring element isolates bright regions.
      3. Threshold + connected components.
      4. Exclude OD region.
      5. Filter by minimum size.
    """
    cv2 = _require_cv2()
    h, w = rgb.shape[:2]
    shape = (h, w)

    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    l_ch = lab[:, :, 0]

    se = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    top_hat = cv2.morphologyEx(l_ch, cv2.MORPH_TOPHAT, se)

    thresh_val = int(np.percentile(top_hat[top_hat > 0], 80)) if np.any(top_hat > 0) else 30
    _, binary = cv2.threshold(top_hat, max(thresh_val, 15), 255, cv2.THRESH_BINARY)

    if od_mask is not None:
        dilated_od = cv2.dilate(od_mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (30, 30)))
        binary[dilated_od > 0] = 0

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    ex_mask = np.zeros(shape, dtype=np.uint8)
    bboxes = []
    for lbl in range(1, num_labels):
        area = stats[lbl, cv2.CC_STAT_AREA]
        if area >= 10:
            ex_mask[labels == lbl] = 255
            bboxes.append((
                stats[lbl, cv2.CC_STAT_LEFT], stats[lbl, cv2.CC_STAT_TOP],
                stats[lbl, cv2.CC_STAT_WIDTH], stats[lbl, cv2.CC_STAT_HEIGHT]
            ))

    return LesionResult(
        lesion_type="EX",
        mask=ex_mask,
        candidate_count=len(bboxes),
        confidence=float(np.clip(len(bboxes) / 15.0 * 0.5, 0, 0.5)),
        bounding_boxes=bboxes,
        method="LAB_luminance_tophat_bright_region",
        validated=False,
    )


# ─── Hemorrhages ───────────────────────────────────────────────────────────────

def detect_hemorrhages(rgb: np.ndarray, od_mask: Optional[np.ndarray] = None,
                       vessel_mask: Optional[np.ndarray] = None) -> LesionResult:
    """
    Detect hemorrhage candidates (dark red blobs larger than MAs).

    Hemorrhages appear as dark, irregular blobs on the green channel.
    Distinguished from MAs by larger size (>120 pixels area).
    Vessels are excluded if a vessel mask is provided.
    """
    cv2 = _require_cv2()
    h, w = rgb.shape[:2]
    shape = (h, w)

    green = rgb[:, :, 1]
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    green_eq = clahe.apply(green)

    se = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
    top_hat = cv2.morphologyEx(green_eq, cv2.MORPH_BLACKHAT, se)

    thresh_val = int(np.percentile(top_hat, 96)) if np.any(top_hat > 0) else 20
    _, binary = cv2.threshold(top_hat, max(thresh_val, 10), 255, cv2.THRESH_BINARY)

    if od_mask is not None:
        dilated_od = cv2.dilate(od_mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (20, 20)))
        binary[dilated_od > 0] = 0
    if vessel_mask is not None:
        # Dilate vessel mask slightly to exclude vessel-adjacent artefacts
        dil_v = cv2.dilate(vessel_mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
        binary[dil_v > 0] = 0

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    he_mask = np.zeros(shape, dtype=np.uint8)
    bboxes = []
    for lbl in range(1, num_labels):
        area = stats[lbl, cv2.CC_STAT_AREA]
        if 50 <= area <= 5000:  # hemorrhages larger than MAs, smaller than huge patches
            he_mask[labels == lbl] = 255
            bboxes.append((
                stats[lbl, cv2.CC_STAT_LEFT], stats[lbl, cv2.CC_STAT_TOP],
                stats[lbl, cv2.CC_STAT_WIDTH], stats[lbl, cv2.CC_STAT_HEIGHT]
            ))

    return LesionResult(
        lesion_type="HE",
        mask=he_mask,
        candidate_count=len(bboxes),
        confidence=float(np.clip(len(bboxes) / 10.0 * 0.55, 0, 0.55)),
        bounding_boxes=bboxes,
        method="green_channel_blackhat_large_blob",
        validated=False,
    )


# ─── Neovascularization ────────────────────────────────────────────────────────

def detect_neovascularization(rgb: np.ndarray, od_result: OpticDiscResult,
                               vessel_mask: Optional[np.ndarray] = None) -> LesionResult:
    """
    Heuristic neovascularization (NV) candidate detection.

    NV appears as a fine network of new vessels near the optic disc or along
    major arcades. This prototype estimates NV by detecting dense vessel
    networks in the peripapilar zone (within 2 OD diameters of disc).

    This is a heuristic score, NOT a trained NV detector. It will produce
    false positives in images with tortuous normal vessels or artefacts.
    """
    cv2 = _require_cv2()
    h, w = rgb.shape[:2]
    shape = (h, w)

    empty = _empty_lesion("NV", shape)
    empty.method = "peripapilar_vessel_density_heuristic"

    if od_result.center_xy is None or vessel_mask is None:
        empty.disclaimer += " (Requires OD detection and vessel mask — not computed)"
        return empty

    cx, cy = od_result.center_xy
    r = od_result.radius_px or (min(h, w) // 10)

    # Region of interest: 0.5–2.5 OD diameters from disc centre
    roi_outer = int(2.5 * 2 * r)
    roi_inner = int(0.5 * 2 * r)

    Y, X = np.ogrid[:h, :w]
    dist = np.sqrt((X - cx)**2 + (Y - cy)**2)
    roi_mask = ((dist > roi_inner) & (dist < roi_outer)).astype(np.uint8) * 255

    # Vessel density in ROI
    vessels_in_roi = np.logical_and(vessel_mask > 0, roi_mask > 0)
    roi_area = np.sum(roi_mask > 0)
    if roi_area == 0:
        return empty

    vessel_density = float(np.sum(vessels_in_roi) / roi_area)

    # Heuristic: vessel density > 15% in peripapilar zone suggests NV candidate
    NV_DENSITY_THRESHOLD = 0.15
    nv_candidate = vessel_density > NV_DENSITY_THRESHOLD

    nv_mask = np.zeros(shape, dtype=np.uint8)
    if nv_candidate:
        nv_mask = cv2.bitwise_and(vessel_mask, roi_mask)

    return LesionResult(
        lesion_type="NV",
        mask=nv_mask,
        candidate_count=1 if nv_candidate else 0,
        confidence=float(np.clip(vessel_density / NV_DENSITY_THRESHOLD * 0.4, 0, 0.4)),
        bounding_boxes=[(cx - roi_outer, cy - roi_outer, 2 * roi_outer, 2 * roi_outer)]
        if nv_candidate else [],
        method="peripapilar_vessel_density_heuristic",
        validated=False,
        disclaimer=(
            "Heuristic peripapilar vessel density score. "
            "NOT a trained neovascularization detector. "
            "High false-positive rate — ophthalmologist review required."
        )
    )


# ─── Full segmentation pipeline ────────────────────────────────────────────────

def run_segmentation(image_rgb: np.ndarray) -> SegmentationResult:
    """
    Run the full retinal segmentation pipeline on a fundus image.

    Args:
        image_rgb: uint8 numpy array (H, W, 3), RGB.

    Returns:
        SegmentationResult with all structure and lesion outputs.
        All results carry validated=False until benchmarked against GT dataset.
    """
    h, w = image_rgb.shape[:2]
    shape = (h, w)

    try:
        # 1. Optic disc
        od = detect_optic_disc(image_rgb)

        # 2. Fovea
        fovea = estimate_fovea(image_rgb, od)

        # 3. Vessels
        vessels = segment_vessels(image_rgb)

        # 4. Lesions (in dependency order: MA → EX → HE → NV)
        ma = detect_microaneurysms(image_rgb, od_mask=od.mask)
        ex = detect_exudates(image_rgb, od_mask=od.mask)
        he = detect_hemorrhages(image_rgb, od_mask=od.mask, vessel_mask=vessels.mask)
        nv = detect_neovascularization(image_rgb, od, vessel_mask=vessels.mask)

        return SegmentationResult(
            optic_disc=od,
            fovea=fovea,
            vessels=vessels,
            microaneurysms=ma,
            exudates=ex,
            hemorrhages=he,
            neovascularization=nv,
            image_shape=(h, w),
            validated=False,
        )

    except Exception as exc:
        logger.error(f"Segmentation pipeline failed: {exc}", exc_info=True)
        return SegmentationResult(
            optic_disc=OpticDiscResult(None, None, None, 0.0),
            fovea=FoveaResult(None, 0.0),
            vessels=VesselResult(None, None),
            microaneurysms=_empty_lesion("MA", shape),
            exudates=_empty_lesion("EX", shape),
            hemorrhages=_empty_lesion("HE", shape),
            neovascularization=_empty_lesion("NV", shape),
            image_shape=(h, w),
            error=str(exc),
            validated=False,
        )


def run_segmentation_from_bytes(image_bytes: bytes) -> SegmentationResult:
    """Convenience: decode bytes and run segmentation."""
    try:
        import cv2
        nparr = np.frombuffer(image_bytes, np.uint8)
        bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        return run_segmentation(rgb)
    except Exception as exc:
        logger.error(f"Failed to decode image for segmentation: {exc}")
        h, w = 256, 256
        return SegmentationResult(
            optic_disc=OpticDiscResult(None, None, None, 0.0),
            fovea=FoveaResult(None, 0.0),
            vessels=VesselResult(None, None),
            microaneurysms=_empty_lesion("MA", (h, w)),
            exudates=_empty_lesion("EX", (h, w)),
            hemorrhages=_empty_lesion("HE", (h, w)),
            neovascularization=_empty_lesion("NV", (h, w)),
            image_shape=(h, w),
            error=str(exc),
        )
