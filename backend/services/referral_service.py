"""
Referral Service — state machine transitions, auto-assign, referral code generation.
"""
import uuid
import string
import random
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from models.referral import Referral, ReferralState, can_transition
from models.screening import ScreeningEvent
from models.doctor import DoctorProfile
from models.hospital import Hospital
from models.patient import Patient
from models.user import User
from core.events import event_bus, Events
import logging

logger = logging.getLogger(__name__)


def generate_referral_code() -> str:
    """Generate a human-readable referral code like DRS-7K9M2X."""
    chars = string.ascii_uppercase + string.digits
    suffix = "".join(random.choices(chars, k=6))
    return f"DRS-{suffix}"


def generate_appointment_token() -> str:
    """Generate appointment token like APT-7K9M2."""
    chars = string.ascii_uppercase + string.digits
    suffix = "".join(random.choices(chars, k=5))
    return f"APT-{suffix}"


async def create_referral(db: AsyncSession, screening_event_id: str, officer_id: str = None) -> Referral:
    """Create a new referral from a screening event."""
    # Verify screening exists and doesn't already have a referral
    result = await db.execute(
        select(Referral).where(Referral.screening_event_id == screening_event_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    referral = Referral(
        id=str(uuid.uuid4()),
        screening_event_id=screening_event_id,
        referral_code=generate_referral_code(),
        state=ReferralState.QUEUED,
        assigned_officer_id=officer_id,
    )
    db.add(referral)
    await db.flush()

    await event_bus.publish(Events.REFERRAL_CREATED, {
        "referral_id": referral.id,
        "referral_code": referral.referral_code,
        "screening_event_id": screening_event_id,
    })

    return referral


async def transition_state(db: AsyncSession, referral: Referral, new_state: ReferralState) -> Referral:
    """Validate and execute a state transition."""
    if not can_transition(referral.state, new_state):
        raise ValueError(
            f"Invalid transition: {referral.state.value} → {new_state.value}. "
            f"Valid targets: {[s.value for s in __import__('models.referral', fromlist=['VALID_TRANSITIONS']).VALID_TRANSITIONS.get(referral.state, [])]}"
        )
    referral.state = new_state
    referral.updated_at = datetime.now(timezone.utc)

    if new_state == ReferralState.CLOSED:
        referral.closed_at = datetime.now(timezone.utc)

    await db.flush()
    return referral


async def assign_referral(db: AsyncSession, referral: Referral, doctor_id: str) -> Referral:
    """Assign a referral to a specific doctor."""
    # Verify doctor exists and is active
    result = await db.execute(
        select(DoctorProfile).where(DoctorProfile.user_id == doctor_id, DoctorProfile.is_active == True)
    )
    doctor = result.scalar_one_or_none()
    if not doctor:
        raise ValueError(f"Doctor {doctor_id} not found or inactive")

    referral.assigned_doctor_id = doctor_id
    referral.hospital_id = doctor.hospital_id
    referral = await transition_state(db, referral, ReferralState.ASSIGNED)

    await event_bus.publish(Events.REFERRAL_ASSIGNED, {
        "referral_id": referral.id,
        "referral_code": referral.referral_code,
        "doctor_id": doctor_id,
    })

    return referral


async def auto_assign_referrals(db: AsyncSession, district_id: str = None, block_id: str = None) -> dict:
    """
    Auto-assign queued referrals to nearest doctor with <10 pending.
    Returns {assigned: int, skipped: int, details: [...]}
    """
    # Get queued referrals (optionally filtered by district)
    query = select(Referral).where(Referral.state == ReferralState.QUEUED)
    result = await db.execute(query)
    queued_referrals = result.scalars().all()

    if not queued_referrals:
        return {"assigned": 0, "skipped": 0, "details": []}

    # Get active doctors with their pending counts
    pending_count_subq = (
        select(func.count(Referral.id))
        .where(
            Referral.assigned_doctor_id == DoctorProfile.user_id,
            Referral.state.in_([ReferralState.ASSIGNED, ReferralState.SCHEDULED, ReferralState.REMINDERS_ACTIVE]),
        )
        .correlate(DoctorProfile)
        .scalar_subquery()
    )

    doctors_query = (
        select(DoctorProfile, pending_count_subq.label("pending_count"))
        .where(DoctorProfile.is_active == True)
    )

    if district_id:
        doctors_query = doctors_query.join(Hospital).where(Hospital.district_id == district_id)

    result = await db.execute(doctors_query)
    doctors = result.all()

    # Sort by pending count (ascending) — least loaded first
    available_doctors = [
        (dp, pc) for dp, pc in doctors if (pc or 0) < (dp.max_pending or 10)
    ]
    available_doctors.sort(key=lambda x: x[1] or 0)

    assigned = 0
    skipped = 0
    details = []

    doctor_idx = 0
    for referral in queued_referrals:
        if not available_doctors:
            skipped += len(queued_referrals) - assigned
            break

        # Round-robin among available doctors
        doctor_profile, current_pending = available_doctors[doctor_idx % len(available_doctors)]

        try:
            referral.assigned_doctor_id = doctor_profile.user_id
            referral.hospital_id = doctor_profile.hospital_id
            referral = await transition_state(db, referral, ReferralState.ASSIGNED)

            # Get doctor name for response
            doc_result = await db.execute(select(User.name).where(User.id == doctor_profile.user_id))
            doc_name = doc_result.scalar_one_or_none() or "Unknown"

            details.append({
                "referral_code": referral.referral_code,
                "doctor_name": doc_name,
            })
            assigned += 1
            doctor_idx += 1
        except ValueError:
            skipped += 1

    return {"assigned": assigned, "skipped": skipped, "details": details}


async def schedule_appointment(
    db: AsyncSession,
    referral: Referral,
    scheduled_at: datetime,
    hospital_id: str,
) -> Referral:
    """Doctor schedules an appointment for a referral."""
    referral.scheduled_at = scheduled_at
    referral.hospital_id = hospital_id
    referral.appointment_token = generate_appointment_token()
    referral = await transition_state(db, referral, ReferralState.SCHEDULED)

    # Move immediately to REMINDERS_ACTIVE
    referral = await transition_state(db, referral, ReferralState.REMINDERS_ACTIVE)

    await event_bus.publish(Events.APPOINTMENT_SCHEDULED, {
        "referral_id": referral.id,
        "referral_code": referral.referral_code,
        "scheduled_at": scheduled_at.isoformat(),
        "hospital_id": hospital_id,
        "appointment_token": referral.appointment_token,
    })

    return referral


async def mark_visited(db: AsyncSession, referral: Referral, notes: str = None) -> Referral:
    """Doctor marks patient as visited → close referral."""
    referral.visit_notes = notes
    referral = await transition_state(db, referral, ReferralState.VISITED)
    referral.closure_reason = "Patient visited hospital"
    referral = await transition_state(db, referral, ReferralState.CLOSED)

    await event_bus.publish(Events.VISIT_VERIFIED, {
        "referral_id": referral.id,
        "referral_code": referral.referral_code,
    })

    return referral


async def request_retake(db: AsyncSession, referral: Referral, reason: str) -> Referral:
    """Doctor requests a retake — reset to QUEUED."""
    referral.retake_reason = reason

    # Update associated screening
    result = await db.execute(
        select(ScreeningEvent).where(ScreeningEvent.id == referral.screening_event_id)
    )
    screening = result.scalar_one_or_none()
    if screening:
        screening.adjudication_status = "retake"

    # Reset referral state
    referral.state = ReferralState.QUEUED  # Direct reset, bypass normal transition
    referral.assigned_doctor_id = None
    referral.updated_at = datetime.now(timezone.utc)
    await db.flush()

    await event_bus.publish(Events.RETAKE_REQUESTED, {
        "referral_id": referral.id,
        "referral_code": referral.referral_code,
        "reason": reason,
    })

    return referral
