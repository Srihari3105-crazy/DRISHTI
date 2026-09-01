"""
Export Service — NPCBVI HMIS Form 1 CSV generation.
"""
import io
import csv
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, extract
from models.referral import Referral, ReferralState
from models.screening import ScreeningEvent
from models.patient import Patient
from models.hospital import Hospital
from models.user import User
import logging

logger = logging.getLogger(__name__)

# NPCBVI Form 1 columns
HMIS_FORM1_COLUMNS = [
    "S.No",
    "Patient Name",
    "Age",
    "Gender",
    "District",
    "Block",
    "Mobile",
    "Screening Date",
    "Eye",
    "DR Grade (ICDR)",
    "DME Risk",
    "Referred To Hospital",
    "Referral Code",
    "Doctor Name",
    "Appointment Date",
    "Visit Status",
    "Visit Date",
    "Days to Closure",
    "EFS Score",
]


async def generate_hmis_form1(db: AsyncSession, year: int, month: int, district_id: str = None) -> str:
    """
    Generate NPCBVI Form 1 CSV for a given month.
    Returns CSV as a string.
    """
    # Build query
    query = (
        select(
            Referral,
            ScreeningEvent,
            Patient,
            Hospital,
        )
        .join(ScreeningEvent, Referral.screening_event_id == ScreeningEvent.id)
        .join(Patient, ScreeningEvent.patient_id == Patient.id)
        .outerjoin(Hospital, Referral.hospital_id == Hospital.id)
        .where(
            extract("year", Referral.created_at) == year,
            extract("month", Referral.created_at) == month,
        )
    )

    if district_id:
        query = query.where(Patient.district_id == district_id)

    query = query.order_by(Referral.created_at)

    result = await db.execute(query)
    rows = result.all()

    # Build CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(HMIS_FORM1_COLUMNS)

    severity_labels = {0: "No DR", 1: "Mild NPDR", 2: "Moderate NPDR", 3: "Severe NPDR", 4: "PDR"}

    for idx, (referral, screening, patient, hospital) in enumerate(rows, 1):
        # Get doctor name
        doctor_name = ""
        if referral.assigned_doctor_id:
            doc_result = await db.execute(
                select(User.name).where(User.id == referral.assigned_doctor_id)
            )
            doctor_name = doc_result.scalar_one_or_none() or ""

        # Calculate days to closure
        days_to_close = ""
        if referral.closed_at and referral.created_at:
            delta = referral.closed_at - referral.created_at
            days_to_close = delta.days

        visit_status = "Visited" if referral.state == ReferralState.CLOSED else referral.state.value.title()

        writer.writerow([
            idx,
            patient.name,
            patient.age,
            patient.gender,
            patient.district_id,
            patient.block_id,
            patient.mobile,
            screening.captured_at.strftime("%Y-%m-%d") if screening.captured_at else "",
            screening.eye,
            severity_labels.get(screening.severity_level, f"Grade {screening.severity_level}"),
            f"{screening.dme_risk:.2f}" if screening.dme_risk else "N/A",
            hospital.name if hospital else "",
            referral.referral_code,
            doctor_name,
            referral.scheduled_at.strftime("%Y-%m-%d %H:%M") if referral.scheduled_at else "",
            visit_status,
            referral.closed_at.strftime("%Y-%m-%d") if referral.closed_at else "",
            days_to_close,
            f"{screening.efs_score:.2f}",
        ])

    csv_content = output.getvalue()
    logger.info(f"Generated HMIS Form 1 CSV: {len(rows)} rows for {year}-{month:02d}")
    return csv_content
