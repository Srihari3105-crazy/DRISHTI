"""
Doctors API — self-registration with CSV-based RegNo verification.
"""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.database import get_db
from core.security import hash_password, require_roles, get_current_user
from models.user import User, UserRole
from models.doctor import DoctorProfile
from models.hospital import Hospital
from schemas.doctor import DoctorRegisterRequest, DoctorRegisterResponse
from services.doctor_verify_service import verify_registration

router = APIRouter(prefix="/doctors", tags=["Doctors"])


@router.post("/register", response_model=DoctorRegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_doctor(
    request: DoctorRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Doctor self-registration:
    1. Check RegNo against seeded CSV
    2. Verify hospital exists
    3. Create user + doctor profile
    """
    # Step 1: Verify registration number against CSV
    csv_match = verify_registration(request.reg_no)
    if not csv_match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration number '{request.reg_no}' not found in the medical council registry. "
                   "Please check the number and try again.",
        )

    # Step 2: Check for duplicate phone
    result = await db.execute(select(User).where(User.phone == request.phone))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this phone number already exists",
        )

    # Check for duplicate RegNo
    result = await db.execute(select(DoctorProfile).where(DoctorProfile.reg_no == request.reg_no.strip().upper()))
    existing_doc = result.scalar_one_or_none()
    if existing_doc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A doctor with this registration number already exists",
        )

    # Step 3: Verify hospital exists
    result = await db.execute(select(Hospital).where(Hospital.id == request.hospital_id))
    hospital = result.scalar_one_or_none()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")

    # Step 4: Create user
    user = User(
        id=str(uuid.uuid4()),
        phone=request.phone,
        name=request.name,
        password_hash=hash_password(request.password),
        role=UserRole.DOCTOR,
        district_id=hospital.district_id,
        is_verified=True,  # Auto-verified via CSV match
    )
    db.add(user)
    await db.flush()

    # Step 5: Create doctor profile
    doctor_profile = DoctorProfile(
        user_id=user.id,
        reg_no=request.reg_no.strip().upper(),
        hospital_id=request.hospital_id,
        verified_at=datetime.now(timezone.utc),
    )
    db.add(doctor_profile)
    await db.flush()

    return DoctorRegisterResponse(
        id=user.id,
        phone=user.phone,
        name=user.name,
        role="doctor",
        reg_no=doctor_profile.reg_no,
        hospital_name=hospital.name,
        verified=True,
        message=f"Registration verified against {csv_match.get('council', 'Medical Council')}. Welcome, Dr. {user.name}!",
    )


@router.get("", response_model=list[dict])
async def list_doctors(
    district_id: str = None,
    db: AsyncSession = Depends(get_db),
    auth: dict = Depends(require_roles("officer", "admin")),
):
    """List all registered doctors (for officer assignment dropdown)."""
    query = (
        select(User, DoctorProfile, Hospital)
        .join(DoctorProfile, User.id == DoctorProfile.user_id)
        .join(Hospital, DoctorProfile.hospital_id == Hospital.id)
        .where(DoctorProfile.is_active == True)
    )

    if district_id:
        query = query.where(Hospital.district_id == district_id)

    result = await db.execute(query)
    rows = result.all()

    return [
        {
            "id": user.id,
            "name": user.name,
            "phone": user.phone,
            "reg_no": profile.reg_no,
            "hospital_name": hospital.name,
            "hospital_id": hospital.id,
            "specialization": profile.specialization,
        }
        for user, profile, hospital in rows
    ]
