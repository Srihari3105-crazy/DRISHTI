"""
Patients API — register, list, OTP verify.
"""
import uuid
import random
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from core.database import get_db
from core.security import require_roles
from models.patient import Patient
from schemas.patient import PatientCreate, PatientResponse, OTPSendRequest, OTPVerifyRequest, OTPResponse

router = APIRouter(prefix="/patients", tags=["Patients"])

# In-memory OTP store for MVP (replace with Redis in production)
_otp_store: dict[str, str] = {}


@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def register_patient(
    patient_data: PatientCreate,
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(require_roles("operator", "admin")),
):
    """Register a new patient (operator only)."""
    # Check for duplicate mobile in same district
    result = await db.execute(
        select(Patient).where(Patient.mobile == patient_data.mobile)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Patient with mobile {patient_data.mobile} already exists (ID: {existing.id})",
        )

    patient = Patient(
        id=str(uuid.uuid4()),
        local_id=f"LOC-{uuid.uuid4().hex[:8].upper()}",
        created_by=auth["user_id"],
        **patient_data.model_dump(exclude_none=True),
    )
    db.add(patient)
    await db.flush()
    return patient


@router.get("", response_model=list[PatientResponse])
async def list_patients(
    district_id: str = Query(None),
    block_id: str = Query(None),
    search: str = Query(None, description="Search by name or mobile"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(require_roles("operator", "doctor", "officer", "admin")),
):
    """List patients with optional filters."""
    query = select(Patient)

    if district_id:
        query = query.where(Patient.district_id == district_id)
    if block_id:
        query = query.where(Patient.block_id == block_id)
    if search:
        query = query.where(
            Patient.name.ilike(f"%{search}%") | Patient.mobile.ilike(f"%{search}%")
        )

    query = query.order_by(Patient.created_at.desc())
    query = query.offset((page - 1) * size).limit(size)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(require_roles("operator", "doctor", "officer", "admin")),
):
    """Get a specific patient by ID."""
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.post("/{patient_id}/verify-mobile", response_model=OTPResponse)
async def send_otp(
    patient_id: str,
    request: OTPSendRequest,
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(require_roles("operator", "admin")),
):
    """Send OTP to patient mobile (mock for MVP — returns OTP in debug mode)."""
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    if patient.mobile != request.mobile:
        raise HTTPException(status_code=400, detail="Mobile number doesn't match patient record")

    # Generate 6-digit OTP
    otp = "".join([str(random.randint(0, 9)) for _ in range(6)])
    _otp_store[patient_id] = otp

    return OTPResponse(
        message="OTP sent to patient mobile (mock mode)",
        otp_sent=True,
        debug_otp=otp,  # Remove in production!
    )


@router.post("/{patient_id}/confirm-mobile", response_model=PatientResponse)
async def confirm_otp(
    patient_id: str,
    request: OTPVerifyRequest,
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(require_roles("operator", "admin")),
):
    """Verify OTP entered by operator (from patient's phone)."""
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    stored_otp = _otp_store.get(patient_id)
    if not stored_otp:
        raise HTTPException(status_code=400, detail="No OTP pending. Send OTP first.")

    if request.otp != stored_otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # Mark mobile as verified
    patient.mobile_verified = True
    _otp_store.pop(patient_id, None)

    await db.flush()
    return patient
