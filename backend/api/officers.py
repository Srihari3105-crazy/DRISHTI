"""
Officers API — dashboard stats + hospital listing.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case
from core.database import get_db
from core.security import require_roles
from models.referral import Referral, ReferralState
from models.screening import ScreeningEvent
from models.patient import Patient
from models.hospital import Hospital
from schemas.dashboard import OfficerDashboard

router = APIRouter(prefix="/officers", tags=["Officers"])


@router.get("/dashboard", response_model=OfficerDashboard)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(require_roles("officer", "admin")),
):
    """
    Officer dashboard stats — scoped to their jurisdiction.
    Returns: total_referred, assigned, scheduled, visited, closed, closure_rate, avg_days_to_close.
    """
    district_id = auth.get("district_id")

    # Base query with patient join for district filtering
    base_query = (
        select(Referral)
        .join(ScreeningEvent, Referral.screening_event_id == ScreeningEvent.id)
        .join(Patient, ScreeningEvent.patient_id == Patient.id)
    )

    if district_id:
        base_query = base_query.where(Patient.district_id == district_id)

    # Count by state
    state_counts_query = (
        select(
            Referral.state,
            func.count(Referral.id).label("count"),
        )
        .join(ScreeningEvent, Referral.screening_event_id == ScreeningEvent.id)
        .join(Patient, ScreeningEvent.patient_id == Patient.id)
    )

    if district_id:
        state_counts_query = state_counts_query.where(Patient.district_id == district_id)

    state_counts_query = state_counts_query.group_by(Referral.state)
    result = await db.execute(state_counts_query)
    state_counts = {row.state.value: row.count for row in result.all()}

    total = sum(state_counts.values())
    closed = state_counts.get("closed", 0)
    closure_rate = (closed / total * 100) if total > 0 else 0.0

    # Average days to close
    avg_days_query = (
        select(
            func.avg(
                func.extract("epoch", Referral.closed_at - Referral.created_at) / 86400
            )
        )
        .join(ScreeningEvent, Referral.screening_event_id == ScreeningEvent.id)
        .join(Patient, ScreeningEvent.patient_id == Patient.id)
        .where(Referral.state == ReferralState.CLOSED)
    )

    if district_id:
        avg_days_query = avg_days_query.where(Patient.district_id == district_id)

    avg_result = await db.execute(avg_days_query)
    avg_days = avg_result.scalar() or 0.0

    # By block breakdown
    block_query = (
        select(
            Patient.block_id,
            Referral.state,
            func.count(Referral.id).label("count"),
        )
        .join(ScreeningEvent, Referral.screening_event_id == ScreeningEvent.id)
        .join(Patient, ScreeningEvent.patient_id == Patient.id)
    )

    if district_id:
        block_query = block_query.where(Patient.district_id == district_id)

    block_query = block_query.group_by(Patient.block_id, Referral.state)
    block_result = await db.execute(block_query)

    by_block = {}
    for row in block_result.all():
        if row.block_id not in by_block:
            by_block[row.block_id] = {}
        by_block[row.block_id][row.state.value] = row.count

    # By severity breakdown
    severity_query = (
        select(
            ScreeningEvent.severity_level,
            func.count(Referral.id).label("count"),
        )
        .join(ScreeningEvent, Referral.screening_event_id == ScreeningEvent.id)
        .join(Patient, ScreeningEvent.patient_id == Patient.id)
    )

    if district_id:
        severity_query = severity_query.where(Patient.district_id == district_id)

    severity_query = severity_query.group_by(ScreeningEvent.severity_level)
    severity_result = await db.execute(severity_query)
    by_severity = {row.severity_level: row.count for row in severity_result.all()}

    return OfficerDashboard(
        total_referred=total,
        assigned=state_counts.get("assigned", 0),
        scheduled=state_counts.get("scheduled", 0) + state_counts.get("reminders_active", 0),
        visited=state_counts.get("visited", 0),
        closed=closed,
        closure_rate=round(closure_rate, 1),
        avg_days_to_close=round(avg_days, 1),
        by_block=by_block,
        by_severity=by_severity,
    )


@router.get("/hospitals", response_model=list[dict])
async def list_hospitals(
    district_id: str = Query(None),
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(require_roles("officer", "doctor", "admin")),
):
    """List hospitals, optionally filtered by district."""
    query = select(Hospital).where(Hospital.is_active == True)
    if district_id:
        query = query.where(Hospital.district_id == district_id)

    result = await db.execute(query)
    hospitals = result.scalars().all()

    return [
        {
            "id": h.id,
            "name": h.name,
            "address": h.address,
            "latitude": h.latitude,
            "longitude": h.longitude,
            "district_id": h.district_id,
            "phone": h.phone,
            "facility_type": h.facility_type,
        }
        for h in hospitals
    ]
