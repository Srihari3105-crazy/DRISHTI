"""
Screenings API — sync screening results from mobile app + real AI pipeline.
"""
import uuid
import os
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.database import get_db
from core.security import require_roles
from core.config import settings
from models.screening import ScreeningEvent
from models.patient import Patient
from schemas.screening import ScreeningEventCreate, ScreeningEventResponse
from services.referral_service import create_referral

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/screenings", tags=["Screenings"])


@router.post("", response_model=ScreeningEventResponse, status_code=status.HTTP_201_CREATED)
async def submit_screening(
    screening_data: ScreeningEventCreate,
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(require_roles("operator", "admin")),
):
    """
    Submit a screening result synced from the mobile app.
    Auto-creates a referral if severity >= 2 (moderate NPDR or worse).
    """
    # Verify patient exists
    result = await db.execute(
        select(Patient).where(Patient.id == screening_data.patient_id)
    )
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Check for duplicate (same patient + eye + image hash)
    result = await db.execute(
        select(ScreeningEvent).where(
            ScreeningEvent.patient_id == screening_data.patient_id,
            ScreeningEvent.image_hash == screening_data.image_hash,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Screening with this image hash already exists (ID: {existing.id})",
        )

    screening = ScreeningEvent(
        id=str(uuid.uuid4()),
        operator_id=auth["user_id"],
        patient_id=screening_data.patient_id,
        eye=screening_data.eye,
        image_hash=screening_data.image_hash,
        quality_score=screening_data.quality_score,
        quality_defects=screening_data.quality_defects,
        lesion_masks_rle=screening_data.lesion_masks_rle,
        severity_level=screening_data.severity_level,
        dme_risk=screening_data.dme_risk,
        rule_trace=screening_data.rule_trace,
        efs_score=screening_data.efs_score,
        captured_at=screening_data.captured_at or datetime.now(timezone.utc),
        synced_at=datetime.now(timezone.utc),
    )
    db.add(screening)
    await db.flush()

    # Auto-create referral for referable grades (severity >= 2)
    referral_id = None
    if screening_data.auto_refer and screening_data.severity_level >= 2:
        referral = await create_referral(db, screening.id)
        referral_id = referral.id

    response = ScreeningEventResponse(
        id=screening.id,
        patient_id=screening.patient_id,
        operator_id=screening.operator_id,
        eye=screening.eye,
        image_hash=screening.image_hash,
        quality_score=screening.quality_score,
        quality_defects=screening.quality_defects,
        lesion_masks_rle=screening.lesion_masks_rle,
        severity_level=screening.severity_level,
        dme_risk=screening.dme_risk,
        rule_trace=screening.rule_trace,
        efs_score=screening.efs_score,
        captured_at=screening.captured_at,
        synced_at=screening.synced_at,
        adjudication_status=screening.adjudication_status,
        referral_id=referral_id,
    )
    return response


@router.get("/{screening_id}", response_model=ScreeningEventResponse)
async def get_screening(
    screening_id: str,
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(require_roles("operator", "doctor", "officer", "admin")),
):
    """Get a specific screening event."""
    result = await db.execute(
        select(ScreeningEvent).where(ScreeningEvent.id == screening_id)
    )
    screening = result.scalar_one_or_none()
    if not screening:
        raise HTTPException(status_code=404, detail="Screening not found")

    # Check for associated referral
    from models.referral import Referral
    ref_result = await db.execute(
        select(Referral.id).where(Referral.screening_event_id == screening_id)
    )
    referral_id = ref_result.scalar_one_or_none()

    return ScreeningEventResponse(
        id=screening.id,
        patient_id=screening.patient_id,
        operator_id=screening.operator_id,
        eye=screening.eye,
        image_hash=screening.image_hash,
        image_path=screening.image_path,
        quality_score=screening.quality_score,
        quality_defects=screening.quality_defects,
        lesion_masks_rle=screening.lesion_masks_rle,
        severity_level=screening.severity_level,
        dme_risk=screening.dme_risk,
        rule_trace=screening.rule_trace,
        efs_score=screening.efs_score,
        captured_at=screening.captured_at,
        synced_at=screening.synced_at,
        adjudication_status=screening.adjudication_status,
        referral_id=referral_id,
    )


# ─── AI Pipeline Endpoint ─────────────────────────────────────────────────────

@router.post("/analyze", tags=["AI Pipeline"])
async def analyze_fundus_image(
    file: UploadFile = File(..., description="Fundus image JPEG or PNG"),
    patient_id: str = Form(...),
    eye: str = Form("OD", description="'OD' (right) or 'OS' (left)"),
    screening_id: str = Form(None, description="Screening ID for report naming (auto-generated if omitted)"),
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(require_roles("operator", "doctor", "admin")),
):
    """
    Run the complete AI DR screening pipeline on an uploaded fundus image.

    Pipeline: Quality Assessment → Enhancement (if borderline) → Segmentation
              → ICDR Grading → Grad-CAM → Confidence Calibration → Clinical Report

    Returns a structured JSON with all pipeline outputs.

    IMPORTANT: All AI outputs are prototypes. No clinical accuracy is claimed.
    Ophthalmologist review is required for all results.
    """
    if not file.content_type or file.content_type not in ("image/jpeg", "image/png", "image/jpg"):
        # Be lenient — attempt to process any uploaded file
        logger.warning(f"Unexpected content_type: {file.content_type} — attempting anyway")

    image_bytes = await file.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    if screening_id is None:
        screening_id = str(uuid.uuid4())

    upload_dir = getattr(settings, "UPLOAD_DIR", "./uploads")

    # Run pipeline
    try:
        from services.ai_pipeline.pipeline import run_pipeline
        result = run_pipeline(
            image_bytes=image_bytes,
            screening_id=screening_id,
            patient_id=patient_id,
            eye=eye,
            operator_name=f"User {auth.get('user_id', 'unknown')}",
            upload_dir=upload_dir,
        )
    except Exception as exc:
        logger.error(f"Pipeline execution error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(exc)}")

    # Build serialisable response (numpy arrays are not JSON-serialisable)
    response = {
        "pipeline_id": result.pipeline_id,
        "screening_id": screening_id,
        "patient_id": patient_id,
        "eye": eye,
        "processing_time_ms": result.processing_time_ms,

        "quality": {
            "decision": result.final_quality_decision,
            "feedback": result.quality_feedback,
            "focus_score": result.quality.focus_score if result.quality else None,
            "illumination_mean": result.quality.illumination_mean if result.quality else None,
            "fov_coverage": result.quality.fov_coverage if result.quality else None,
            "fov_detected": result.quality.fov_detected if result.quality else None,
        } if result.quality else {"decision": result.final_quality_decision, "feedback": result.quality_feedback},

        "enhancement_applied": result.enhancement_applied,

        "grading": {
            "severity_level": result.severity_level,
            "severity_name": result.severity_name,
            "referable": result.referable,
            "confidence_raw": result.confidence_raw,
            "calibrated_confidence": result.calibrated_confidence,
            "dme_risk": result.dme_risk,
            "efs_score": result.efs_score,
            "method": result.grading.method if result.grading else "not_run",
            "model_available": result.grading.model_available if result.grading else False,
            "validated": result.grading.validated if result.grading else False,
            "disclaimer": result.grading.disclaimer if result.grading else "",
            "rule_trace": result.rule_trace,
        } if result.grading else None,

        "lesion_summary": result.lesion_summary,

        "segmentation": {
            "optic_disc_detected": (result.segmentation.optic_disc.center_xy is not None
                                    if result.segmentation else False),
            "optic_disc_center": result.segmentation.optic_disc.center_xy if result.segmentation else None,
            "fovea_center": result.segmentation.fovea.center_xy if result.segmentation else None,
            "validated": False,
            "disclaimer": (
                "All segmentation outputs are prototype-grade classical CV algorithms. "
                "Not clinically validated."
            ),
        } if result.segmentation else None,

        "gradcam": {
            "available": result.gradcam_available,
            "overlay_b64": result.gradcam_b64,
            "predicted_class": result.gradcam.predicted_class if result.gradcam else None,
            "disclaimer": (
                result.gradcam.disclaimer if result.gradcam else
                "Grad-CAM unavailable — no trained model checkpoint. "
                "Provide assets/models/dr_efficientnet_b4.pth to enable."
            ),
        },

        "report_url": (
            f"/api/v1/screenings/{screening_id}/report"
            if result.report_path and os.path.exists(result.report_path)
            else None
        ),

        "error": result.error or None,

        "important_notice": (
            "AI-ASSISTED SCREENING PROTOTYPE — outputs are NOT clinically validated. "
            "Ophthalmologist review required before any clinical action."
        ),
    }

    return response


@router.get("/{screening_id}/report", response_class=HTMLResponse, tags=["AI Pipeline"])
async def get_screening_report(
    screening_id: str,
    auth: dict = Depends(require_roles("operator", "doctor", "officer", "admin")),
):
    """Download the HTML clinical report for a screening event."""
    upload_dir = getattr(settings, "UPLOAD_DIR", "./uploads")
    report_path = os.path.join(upload_dir, "reports", f"{screening_id}.html")
    if not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail="Report not found for this screening ID")
    with open(report_path, "r", encoding="utf-8") as f:
        html = f.read()
    return HTMLResponse(content=html)

