"""
DRISHTI-LENS — Adaptive Image Enhancement
==========================================
Applies real image enhancement for borderline-quality fundus images.

Pipeline:
    Input (borderline) -> CLAHE -> Illumination Normalization -> Denoising -> Re-assess

CLAHE:
    Applied to the L channel of LAB colour space using OpenCV adapthisteq equivalent.
    Clip limit and tile size chosen to avoid amplifying sensor noise in dark regions.

Illumination Normalization:
    Divides each channel by a large-kernel Gaussian-blurred version (background
    estimation). Removes uneven vignetting common in portable fundus cameras.
    Preserves local contrast including small lesions.

Denoising:
    cv2.fastNlMeansDenoisingColored (Non-Local Means) — preserves edge structure
    better than median filtering for medical images.
    Parameters set conservatively to avoid over-smoothing microaneurysms.

DISCLAIMER: Enhancement parameters (CLAHE clip, NLM h-value) are set to commonly
used values for fundus imagery. Optimal parameters should be tuned on a labelled
dataset with ground-truth quality scores.
"""
from __future__ import annotations
import numpy as np
import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EnhancementResult:
    """Output from adaptive enhancement pipeline."""
    original_rgb: np.ndarray          # Original image (H x W x 3, uint8, RGB)
    enhanced_rgb: np.ndarray          # Enhanced image (H x W x 3, uint8, RGB)
    clahe_applied: bool
    illum_norm_applied: bool
    denoising_applied: bool
    saved_intermediate_paths: list    # Paths of saved debug images (if save_dir provided)
    error: str = ""


def apply_clahe(rgb: np.ndarray, clip_limit: float = 2.0, tile_size: int = 8) -> np.ndarray:
    """
    Apply CLAHE to the L channel of the LAB colour space.

    Args:
        rgb:        Input image, uint8, (H, W, 3), RGB.
        clip_limit: CLAHE clip limit (contrast enhancement cap). Default 2.0
                    prevents excessive noise amplification.
        tile_size:  Grid tile size in pixels. Smaller = more local adaptation.

    Returns:
        CLAHE-enhanced image, uint8, (H, W, 3), RGB.
    """
    import cv2
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile_size, tile_size))
    l_enhanced = clahe.apply(l_channel)

    lab_enhanced = cv2.merge([l_enhanced, a_channel, b_channel])
    bgr_enhanced = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)
    return cv2.cvtColor(bgr_enhanced, cv2.COLOR_BGR2RGB)


def apply_illumination_normalization(rgb: np.ndarray, sigma: float = 60.0) -> np.ndarray:
    """
    Correct uneven illumination via background estimation and subtraction.

    Method:
        1. Estimate background with a large Gaussian blur (sigma~60px covers
           typical vignetting / illumination gradients without removing lesion signal).
        2. Divide each channel by background; multiply by global mean to preserve
           overall brightness scale.

    Args:
        rgb:   Input image, uint8, (H, W, 3), RGB.
        sigma: Gaussian sigma for background estimation. Larger values remove
               lower-frequency illumination gradients only.

    Returns:
        Illumination-normalised image, uint8, (H, W, 3), RGB.
    """
    import cv2
    img_f = rgb.astype(np.float64) + 1.0  # avoid divide-by-zero

    # Kernel size must be odd; ~6*sigma covers 99.7% of Gaussian
    k = int(6 * sigma) | 1  # bitwise OR 1 ensures odd
    k = max(k, 3)

    background = cv2.GaussianBlur(img_f, (k, k), sigma)
    global_mean = np.mean(img_f)

    normalised = (img_f / background) * global_mean
    normalised = np.clip(normalised, 0, 255).astype(np.uint8)
    return normalised


def apply_denoising(rgb: np.ndarray, h: float = 6, template_window: int = 7,
                    search_window: int = 21) -> np.ndarray:
    """
    Apply Non-Local Means denoising (colour).

    Conservative parameters to avoid over-smoothing microaneurysms:
        h=6 (luminance filter strength; lower = less smoothing)
        template_window=7, search_window=21

    Args:
        rgb:             Input image, uint8, (H, W, 3), RGB.
        h:               Filter strength. Higher removes more noise but risks
                         blurring small lesions. Keep <= 8 for fundus images.
        template_window: Patch size for comparison (odd). Default 7.
        search_window:   Search area size (odd). Default 21.

    Returns:
        Denoised image, uint8, (H, W, 3), RGB.
    """
    import cv2
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    denoised_bgr = cv2.fastNlMeansDenoisingColored(
        bgr,
        None,
        h=h,
        hColor=h,
        templateWindowSize=template_window,
        searchWindowSize=search_window,
    )
    return cv2.cvtColor(denoised_bgr, cv2.COLOR_BGR2RGB)


def enhance(image_rgb: np.ndarray, save_dir: str = None) -> EnhancementResult:
    """
    Full adaptive enhancement pipeline.

    Applied sequence:
        CLAHE -> Illumination Normalization -> NLM Denoising

    Args:
        image_rgb: Input image, uint8 numpy array (H, W, 3), RGB.
        save_dir:  If provided, saves intermediate images here for debugging.

    Returns:
        EnhancementResult with original + enhanced images and applied flags.
    """
    try:
        import cv2
    except ImportError:
        return EnhancementResult(
            original_rgb=image_rgb, enhanced_rgb=image_rgb,
            clahe_applied=False, illum_norm_applied=False, denoising_applied=False,
            saved_intermediate_paths=[],
            error="OpenCV not installed — enhancement skipped."
        )

    saved_paths = []
    original = image_rgb.copy()
    img = image_rgb.copy()

    try:
        # Step 1: CLAHE
        img = apply_clahe(img)
        clahe_ok = True
        if save_dir:
            p = os.path.join(save_dir, "step1_clahe.jpg")
            cv2.imwrite(p, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
            saved_paths.append(p)

        # Step 2: Illumination normalization
        img = apply_illumination_normalization(img)
        illum_ok = True
        if save_dir:
            p = os.path.join(save_dir, "step2_illum_norm.jpg")
            cv2.imwrite(p, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
            saved_paths.append(p)

        # Step 3: Denoising
        img = apply_denoising(img)
        denoise_ok = True
        if save_dir:
            p = os.path.join(save_dir, "step3_denoised.jpg")
            cv2.imwrite(p, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
            saved_paths.append(p)

        return EnhancementResult(
            original_rgb=original,
            enhanced_rgb=img,
            clahe_applied=clahe_ok,
            illum_norm_applied=illum_ok,
            denoising_applied=denoise_ok,
            saved_intermediate_paths=saved_paths,
        )

    except Exception as exc:
        logger.error(f"Enhancement failed: {exc}")
        return EnhancementResult(
            original_rgb=original, enhanced_rgb=original,
            clahe_applied=False, illum_norm_applied=False, denoising_applied=False,
            saved_intermediate_paths=saved_paths,
            error=str(exc)
        )


def enhance_from_bytes(image_bytes: bytes, save_dir: str = None) -> EnhancementResult:
    """Convenience wrapper: decode bytes then enhance."""
    try:
        import cv2
        nparr = np.frombuffer(image_bytes, np.uint8)
        bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        return enhance(rgb, save_dir=save_dir)
    except Exception as exc:
        logger.error(f"Failed to decode image for enhancement: {exc}")
        dummy = np.zeros((256, 256, 3), dtype=np.uint8)
        return EnhancementResult(
            original_rgb=dummy, enhanced_rgb=dummy,
            clahe_applied=False, illum_norm_applied=False, denoising_applied=False,
            saved_intermediate_paths=[], error=str(exc)
        )
