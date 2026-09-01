"""
Referrals API — the core of the referral loop.
List (role-scoped), assign, auto-assign, schedule, visit, retake.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from core.database import get_db
from core.security import require_roles
from models.referral import Referral, ReferralState
from models.screening import ScreeningEvent
from models.patient import Patient
from models.user import User
from models.hospital import Hospital
from models.notification import NotificationLog
from schemas.referral import (
    ReferralResponse, PaginatedReferrals,
    AssignRequest, ScheduleRequest, VisitRequest, RetakeRequest, AutoAssignResponse,
)
from services import referral_service

router = APIRouter(prefix="/referrals", tags=["Referrals"])


def _build_referral_response(referral, patient=None, screening=None, doctor_name=None, hospital_name=None) -> ReferralResponse:
    """Helper to build a ReferralResponse with nested data."""
    return ReferralResponse(
        id=referral.id,
        referral_code=referral.referral_code,
        state=referral.state.value,
        screening_event_id=referral.screening_event_id,
        assigned_doctor_id=referral.assigned_doctor_id,
        assigned_officer_id=referral.assigned_officer_id,
        hospital_id=referral.hospital_id,
        scheduled_at=referral.scheduled_at,
        appointment_token=referral.appointment_token,
        visit_notes=referral.visit_notes,
        retake_reason=referral.retake_reason,
        closure_reason=referral.closure_reason,
        created_at=referral.created_at,
        closed_at=referral.closed_at,
        patient_name=patient.name if patient else None,
        patient_age=patient.age if patient else None,
        patient_mobile=patient.mobile if patient else None,
        doctor_name=doctor_name,
        hospital_name=hospital_name,
        severity_level=screening.severity_level if screening else None,
        efs_score=screening.efs_score if screening else None,
        eye=screening.eye if screening else None,
    )


@router.get("", response_model=PaginatedReferrals)
async def list_referrals(
    state: str = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(require_roles("operator", "doctor", "officer", "admin")),
):
    """
    List referrals — role-scoped:
    - Doctor: only their assigned referrals
    - Officer: only referrals in their jurisdiction
    - Admin: all referrals
    """
    query = (
        select(Referral, ScreeningEvent, Patient)
        .join(ScreeningEvent, Referral.screening_event_id == ScreeningEvent.id)
        .join(Patient, ScreeningEvent.patient_id == Patient.id)
    )

    # Role-based filtering
    if auth["role"] == "doctor":
        query = query.where(Referral.assigned_doctor_id == auth["user_id"])
    elif auth["role"] == "officer":
        if auth.get("district_id"):
            query = query.where(Patient.district_id == auth["district_id"])

    if state:
        try:
            state_enum = ReferralState(state)
            query = query.where(Referral.state == state_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid state: {state}")

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Paginate
    query = query.order_by(Referral.created_at.desc())
    query = query.offset((page - 1) * size).limit(size)

    result = await db.execute(query)
    rows = result.all()

    items = []
    for referral, screening, patient in rows:
        # Get doctor name
        doctor_name = None
        if referral.assigned_doctor_id:
            doc_result = await db.execute(select(User.name).where(User.id == referral.assigned_doctor_id))
            doctor_name = doc_result.scalar_one_or_none()

        # Get hospital name
        hospital_name = None
        if referral.hospital_id:
            hosp_result = await db.execute(select(Hospital.name).where(Hospital.id == referral.hospital_id))
            hospital_name = hosp_result.scalar_one_or_none()

        items.append(_build_referral_response(referral, patient, screening, doctor_name, hospital_name))

    return PaginatedReferrals(items=items, total=total, page=page, size=size)


@router.get("/{referral_id}", response_model=ReferralResponse)
async def get_referral(
    referral_id: str,
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(require_roles("operator", "doctor", "officer", "admin")),
):
    """Get a specific referral with full details."""
    result = await db.execute(
        select(Referral, ScreeningEvent, Patient)
        .join(ScreeningEvent, Referral.screening_event_id == ScreeningEvent.id)
        .join(Patient, ScreeningEvent.patient_id == Patient.id)
        .where(Referral.id == referral_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Referral not found")

    referral, screening, patient = row

    doctor_name = None
    if referral.assigned_doctor_id:
        doc_result = await db.execute(select(User.name).where(User.id == referral.assigned_doctor_id))
        doctor_name = doc_result.scalar_one_or_none()

    hospital_name = None
    if referral.hospital_id:
        hosp_result = await db.execute(select(Hospital.name).where(Hospital.id == referral.hospital_id))
        hospital_name = hosp_result.scalar_one_or_none()

    return _build_referral_response(referral, patient, screening, doctor_name, hospital_name)


@router.get("/{referral_id}/notifications", response_model=list[dict])
async def get_referral_notifications(
    referral_id: str,
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(require_roles("doctor", "officer", "admin")),
):
    """Get notification/reminder log for a referral."""
    result = await db.execute(
        select(NotificationLog)
        .where(NotificationLog.referral_id == referral_id)
        .order_by(NotificationLog.scheduled_for)
    )
    notifications = result.scalars().all()

    return [
        {
            "id": n.id,
            "channel": n.channel,
            "template_key": n.template_key,
            "status": n.status,
            "scheduled_for": n.scheduled_for.isoformat() if n.scheduled_for else None,
            "sent_at": n.sent_at.isoformat() if n.sent_at else None,
            "delivered_at": n.delivered_at.isoformat() if n.delivered_at else None,
            "message": n.meta.get("message", "") if n.meta else "",
        }
        for n in notifications
    ]


@router.post("/{referral_id}/assign", response_model=ReferralResponse)
async def assign_referral(
    referral_id: str,
    request: AssignRequest,
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(require_roles("officer", "admin")),
):
    """Officer assigns a referral to a specific doctor."""
    result = await db.execute(select(Referral).where(Referral.id == referral_id))
    referral = result.scalar_one_or_none()
    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")

    try:
        referral = await referral_service.assign_referral(db, referral, request.doctor_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return await get_referral(referral_id, db, auth)


@router.post("/auto-assign", response_model=AutoAssignResponse)
async def auto_assign(
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(require_roles("officer", "admin")),
):
    """Bulk auto-assign queued referrals in officer's jurisdiction."""
    district_id = auth.get("district_id")
    result = await referral_service.auto_assign_referrals(db, district_id=district_id)
    return AutoAssignResponse(**result)


@router.post("/{referral_id}/schedule", response_model=ReferralResponse)
async def schedule_appointment(
    referral_id: str,
    request: ScheduleRequest,
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(require_roles("doctor", "admin")),
):
    """Doctor schedules an appointment."""
    result = await db.execute(select(Referral).where(Referral.id == referral_id))
    referral = result.scalar_one_or_none()
    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")

    # Verify this doctor is assigned
    if auth["role"] == "doctor" and referral.assigned_doctor_id != auth["user_id"]:
        raise HTTPException(status_code=403, detail="Not assigned to this referral")

    try:
        referral = await referral_service.schedule_appointment(
            db, referral, request.scheduled_at, request.hospital_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return await get_referral(referral_id, db, auth)


@router.post("/{referral_id}/visit", response_model=ReferralResponse)
async def mark_visited(
    referral_id: str,
    request: VisitRequest,
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(require_roles("doctor", "admin")),
):
    """Doctor marks patient as visited → closes referral."""
    result = await db.execute(select(Referral).where(Referral.id == referral_id))
    referral = result.scalar_one_or_none()
    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")

    if auth["role"] == "doctor" and referral.assigned_doctor_id != auth["user_id"]:
        raise HTTPException(status_code=403, detail="Not assigned to this referral")

    try:
        referral = await referral_service.mark_visited(db, referral, request.notes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return await get_referral(referral_id, db, auth)


@router.post("/{referral_id}/retake", response_model=ReferralResponse)
async def request_retake(
    referral_id: str,
    request: RetakeRequest,
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(require_roles("doctor", "admin")),
):
    """Doctor requests a retake of the fundus image."""
    result = await db.execute(select(Referral).where(Referral.id == referral_id))
    referral = result.scalar_one_or_none()
    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")

    try:
        referral = await referral_service.request_retake(db, referral, request.reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return await get_referral(referral_id, db, auth)
