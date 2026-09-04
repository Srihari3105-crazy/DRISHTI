"""
DRISHTI-LENS — Full AI Screening Pipeline Orchestrator
========================================================
Chains all AI pipeline modules in the correct order:

  Image bytes
      ↓
  Quality Assessment  (quality_assessment.py)
      ↓
  [If BORDERLINE] Enhancement  (enhancement.py)
      ↓
  Re-assess quality
      ↓
  [If UNGRADABLE] → Reject with feedback
      ↓
  Segmentation  (segmentation.py)
      ↓
  Grading  (grading.py)
      ↓
  Grad-CAM  (gradcam.py)
      ↓
  Calibration  (calibration.py)
      ↓
  Report  (report_generator.py)
      ↓
  Structured PipelineResult

All outputs are deterministic from image content.
No random values. No hardcoded outputs.
"""
from __future__ import annotations
import numpy as np
import logging
import os
import uuid
import time
from dataclasses import dataclass, field
from typing import Optional

from .quality_assessment import assess_quality, QualityResult
from .enhancement import enhance, EnhancementResult
from .segmentation import run_segmentation, SegmentationResult
from .grading import grade_image, GradingResult
from .gradcam import compute_gradcam, GradCAMResult
from .calibration import calibrate_probability
from .report_generator import generate_html_report

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Complete output from the full AI screening pipeline."""
    pipeline_id: str                        # Unique run ID
    quality: Optional[QualityResult]
    enhancement: Optional[EnhancementResult]
    enhancement_applied: bool
    quality_after_enhancement: Optional[QualityResult]
    final_quality_decision: str             # QUALITY_GOOD | QUALITY_BORDERLINE | QUALITY_UNGRADABLE
    quality_feedback: list

    segmentation: Optional[SegmentationResult]
    grading: Optional[GradingResult]
    gradcam: Optional[GradCAMResult]

    report_html: Optional[str]              # Full HTML report string
    report_path: Optional[str]             # Path where report was saved

    processing_time_ms: float              # Total pipeline wall time

    # Derived convenience fields (for API response)
    severity_level: int = -1
    severity_name: str = "UNGRADED"
    referable: bool = False
    confidence_raw: float = 0.0
    calibrated_confidence: Optional[float] = None
    dme_risk: float = 0.0
    efs_score: float = 0.0
    rule_trace: list = field(default_factory=list)
    lesion_summary: dict = field(default_factory=dict)
    gradcam_b64: Optional[str] = None
    gradcam_available: bool = False

    error: str = ""


def run_pipeline(
    image_bytes: bytes,
    screening_id: str,
    patient_id: str,
    eye: str = "OD",
    operator_name: str = "Unknown",
    upload_dir: str = None,
) -> PipelineResult:
    """
    Run the complete DR screening AI pipeline.

    Args:
        image_bytes:    Raw JPEG/PNG bytes of fundus image.
        screening_id:   ID of the screening event (used for report naming).
        patient_id:     Patient identifier.
        eye:            'OD' (right) or 'OS' (left).
        operator_name:  Name of field operator (for report).
        upload_dir:     Directory for saving reports and debug images.

    Returns:
        PipelineResult with all outputs filled.
    """
    t_start = time.perf_counter()
    pipeline_id = str(uuid.uuid4())[:8]

    try:
        import cv2
        nparr = np.frombuffer(image_bytes, np.uint8)
        bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if bgr is None:
            raise ValueError("cv2.imdecode returned None — image bytes may be corrupt")
        image_rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    except Exception as exc:
        return PipelineResult(
            pipeline_id=pipeline_id,
            quality=None, enhancement=None, enhancement_applied=False,
            quality_after_enhancement=None,
            final_quality_decision="QUALITY_UNGRADABLE",
            quality_feedback=[f"Image decode failed: {exc}"],
            segmentation=None, grading=None, gradcam=None,
            report_html=None, report_path=None,
            processing_time_ms=0.0,
            error=str(exc),
        )

    save_dir = None
    report_path = None
    if upload_dir:
        save_dir = os.path.join(upload_dir, "debug", screening_id)
        os.makedirs(save_dir, exist_ok=True)
        report_path = os.path.join(upload_dir, "reports", f"{screening_id}.html")
        os.makedirs(os.path.dirname(report_path), exist_ok=True)

    # ── Step 1: Initial quality assessment ──────────────────────────────────
    logger.info(f"[{pipeline_id}] Quality assessment...")
    quality = assess_quality(image_rgb)

    # ── Step 2: Enhancement (borderline only) ────────────────────────────────
    enhancement_applied = False
    enhancement_result = None
    quality_after = None
    working_image = image_rgb

    if quality.decision == "QUALITY_BORDERLINE":
        logger.info(f"[{pipeline_id}] Borderline quality — applying enhancement...")
        enhancement_result = enhance(image_rgb, save_dir=save_dir)
        if not enhancement_result.error:
            enhancement_applied = True
            working_image = enhancement_result.enhanced_rgb
            quality_after = assess_quality(working_image)
            logger.info(f"[{pipeline_id}] Quality after enhancement: {quality_after.decision}")
        else:
            logger.warning(f"[{pipeline_id}] Enhancement failed: {enhancement_result.error}")

    elif quality.decision == "QUALITY_GOOD":
        logger.info(f"[{pipeline_id}] Quality GOOD — no enhancement needed")

    # Final quality decision
    if quality_after is not None:
        final_decision = quality_after.decision
        final_feedback = quality_after.feedback
    else:
        final_decision = quality.decision
        final_feedback = quality.feedback

    # ── Step 3: Reject ungradable ────────────────────────────────────────────
    if final_decision == "QUALITY_UNGRADABLE":
        logger.info(f"[{pipeline_id}] Rejected: {final_feedback}")
        t_ms = (time.perf_counter() - t_start) * 1000
        return PipelineResult(
            pipeline_id=pipeline_id,
            quality=quality,
            enhancement=enhancement_result,
            enhancement_applied=enhancement_applied,
            quality_after_enhancement=quality_after,
            final_quality_decision="QUALITY_UNGRADABLE",
            quality_feedback=final_feedback,
            segmentation=None, grading=None, gradcam=None,
            report_html=None, report_path=None,
            processing_time_ms=round(t_ms, 1),
            error="Image ungradable — recapture required",
        )

    # ── Step 4: Segmentation ─────────────────────────────────────────────────
    logger.info(f"[{pipeline_id}] Running segmentation...")
    seg = run_segmentation(working_image)

    # ── Step 5: Grading ──────────────────────────────────────────────────────
    logger.info(f"[{pipeline_id}] Running grading (method: {'DL' if not seg.error else 'rule-based'})...")
    grading = grade_image(working_image, seg_result=seg)

    # ── Step 6: Calibration ───────────────────────────────────────────────────
    grading.calibrated_confidence = calibrate_probability(
        grading.confidence, grading.severity_level
    )

    # ── Step 7: Grad-CAM ─────────────────────────────────────────────────────
    logger.info(f"[{pipeline_id}] Computing Grad-CAM...")
    gradcam = compute_gradcam(working_image, target_class=max(0, grading.severity_level))

    # ── Step 8: Annotated image ───────────────────────────────────────────────
    annotated = _build_annotated_image(working_image, seg)

    # ── Step 9: Report ────────────────────────────────────────────────────────
    logger.info(f"[{pipeline_id}] Generating report...")
    report_html = generate_html_report(
        screening_id=screening_id,
        patient_id=patient_id,
        eye=eye,
        quality_result=quality_after or quality,
        enhancement_applied=enhancement_applied,
        grading_result=grading,
        seg_result=seg,
        gradcam_result=gradcam,
        original_image_rgb=image_rgb,
        enhanced_image_rgb=enhancement_result.enhanced_rgb if enhancement_applied else None,
        annotated_image_rgb=annotated,
        operator_name=operator_name,
        output_path=report_path,
    )

    # ── Lesion summary dict ───────────────────────────────────────────────────
    lesion_summary = {}
    if seg:
        for attr, key in [("microaneurysms","MA"), ("exudates","EX"),
                          ("hemorrhages","HE"), ("neovascularization","NV")]:
            lr = getattr(seg, attr, None)
            if lr and lr.candidate_count > 0:
                lesion_summary[key] = {
                    "count": lr.candidate_count,
                    "confidence": lr.confidence,
                    "validated": lr.validated,
                }

    t_ms = (time.perf_counter() - t_start) * 1000
    logger.info(f"[{pipeline_id}] Pipeline complete in {t_ms:.0f}ms")

    return PipelineResult(
        pipeline_id=pipeline_id,
        quality=quality,
        enhancement=enhancement_result,
        enhancement_applied=enhancement_applied,
        quality_after_enhancement=quality_after,
        final_quality_decision=final_decision,
        quality_feedback=final_feedback,
        segmentation=seg,
        grading=grading,
        gradcam=gradcam,
        report_html=report_html,
        report_path=report_path,
        processing_time_ms=round(t_ms, 1),
        severity_level=grading.severity_level,
        severity_name=grading.severity_name,
        referable=grading.referable,
        confidence_raw=grading.confidence,
        calibrated_confidence=grading.calibrated_confidence,
        dme_risk=grading.dme_risk,
        efs_score=grading.efs_score,
        rule_trace=grading.rule_trace,
        lesion_summary=lesion_summary,
        gradcam_b64=gradcam.overlay_b64 if gradcam.cam_available else None,
        gradcam_available=gradcam.cam_available,
    )


def _build_annotated_image(image_rgb: np.ndarray, seg: SegmentationResult) -> Optional[np.ndarray]:
    """Overlay lesion masks on original image for visual report."""
    try:
        import cv2
        annotated = image_rgb.copy()

        # Overlay each lesion mask with a distinct colour
        overlays = [
            (seg.microaneurysms, (255, 50, 50)),    # Red — MA
            (seg.exudates, (255, 220, 50)),          # Yellow — EX
            (seg.hemorrhages, (200, 50, 200)),       # Purple — HE
            (seg.vessels, (50, 150, 255)),           # Blue — vessels
        ]
        for result, colour in overlays:
            mask = getattr(result, "mask", None)
            if mask is None or not np.any(mask):
                continue
            colour_layer = np.zeros_like(annotated)
            colour_layer[mask > 0] = colour
            annotated = cv2.addWeighted(annotated, 1.0, colour_layer, 0.35, 0)

        # Draw OD circle
        od = seg.optic_disc
        if od.center_xy and od.radius_px:
            cv2.circle(annotated, od.center_xy, od.radius_px, (50, 255, 50), 2)

        # Draw fovea point
        fv = seg.fovea
        if fv.center_xy:
            cv2.circle(annotated, fv.center_xy, 8, (255, 200, 50), -1)

        return annotated
    except Exception as exc:
        logger.warning(f"Could not build annotated image: {exc}")
        return None
