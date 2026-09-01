"""
Screenings API — sync screening results from mobile app.
"""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.database import get_db
from core.security import require_roles
from models.screening import ScreeningEvent
from models.patient import Patient
from schemas.screening import ScreeningEventCreate, ScreeningEventResponse
from services.referral_service import create_referral

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
