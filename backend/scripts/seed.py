"""
DRISHTI-LENS Seed Script
Populates database with demo data: hospitals, doctors, officers, patients, screenings, referrals.
Run: python scripts/seed.py
"""
import asyncio
import csv
import uuid
import random
import sys
import os

# Force UTF-8 output on Windows (avoids emoji encode errors on CP1252)
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


from datetime import datetime, timedelta, timezone

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from core.database import engine, AsyncSessionLocal, Base
from core.security import hash_password
from core.config import settings
from models.user import User, UserRole
from models.patient import Patient
from models.hospital import Hospital
from models.doctor import DoctorProfile
from models.officer import OfficerJurisdiction
from models.screening import ScreeningEvent
from models.referral import Referral, ReferralState
from models.notification import NotificationLog

# Seed constants
DEFAULT_PASSWORD = "drishti123"
DISTRICT_ID = "DIST01"
BLOCKS = ["BLK01", "BLK02"]

INDIAN_FIRST_NAMES_M = ["Rajesh", "Amit", "Suresh", "Vinod", "Prakash", "Mohan", "Ramesh", "Dinesh", "Mahesh", "Ganesh",
                        "Anil", "Vikas", "Sanjay", "Ravi", "Deepak", "Ashok", "Manoj", "Rakesh", "Mukesh", "Naresh"]
INDIAN_FIRST_NAMES_F = ["Sunita", "Priya", "Kavita", "Anita", "Geeta", "Sita", "Radha", "Meena", "Lata", "Rekha",
                        "Kamla", "Savita", "Asha", "Usha", "Nisha", "Poonam", "Seema", "Neha", "Rani", "Mala"]
INDIAN_LAST_NAMES = ["Kumar", "Sharma", "Verma", "Meena", "Singh", "Gupta", "Joshi", "Choudhary", "Yadav", "Patel",
                     "Agarwal", "Jain", "Rajput", "Saini", "Malav"]

SEVERITY_LABELS = {0: "No DR", 1: "Mild NPDR", 2: "Moderate NPDR", 3: "Severe NPDR", 4: "PDR"}

# Realistic ICDR rule traces for each severity level
RULE_TRACES = {
    0: [{"rule_id": "ICDR-0", "met": True, "description": "No abnormalities detected", "zones": []}],
    1: [
        {"rule_id": "ICDR-1.1", "met": True, "description": "Microaneurysms only", "zones": ["zone_1"]},
        {"rule_id": "ICDR-1.2", "met": False, "description": "Hard exudates present", "zones": []},
    ],
    2: [
        {"rule_id": "ICDR-2.1", "met": True, "description": "More than just microaneurysms", "zones": ["zone_1", "zone_2"]},
        {"rule_id": "ICDR-2.2", "met": True, "description": "Hard exudates present", "zones": ["zone_2"]},
        {"rule_id": "ICDR-2.3", "met": False, "description": "Cotton wool spots present", "zones": []},
        {"rule_id": "ICDR-3.1", "met": False, "description": "Venous beading in 2+ quadrants", "zones": []},
    ],
    3: [
        {"rule_id": "ICDR-3.1", "met": True, "description": "Venous beading in 2+ quadrants", "zones": ["zone_1", "zone_3"]},
        {"rule_id": "ICDR-3.2", "met": True, "description": "IRMA in 1+ quadrant", "zones": ["zone_2"]},
        {"rule_id": "ICDR-3.3", "met": True, "description": ">20 intraretinal hemorrhages in 4 quadrants", "zones": ["zone_1", "zone_2", "zone_3", "zone_4"]},
    ],
    4: [
        {"rule_id": "ICDR-4.1", "met": True, "description": "Neovascularization detected", "zones": ["zone_1", "zone_2"]},
        {"rule_id": "ICDR-4.2", "met": True, "description": "Vitreous/preretinal hemorrhage", "zones": ["zone_1"]},
    ],
}


async def seed_hospitals(db):
    """Seed hospitals from CSV."""
    print("📍 Seeding hospitals...")
    csv_path = settings.HOSPITAL_CSV_PATH
    hospitals = []

    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            hospital = Hospital(
                id=row["id"],
                name=row["name"],
                address=row["address"],
                latitude=float(row["latitude"]),
                longitude=float(row["longitude"]),
                district_id=row["district_id"],
                state_id=row["state_id"],
                phone=row["phone"],
                facility_type=row["facility_type"],
            )
            hospitals.append(hospital)

    # Upsert
    for h in hospitals:
        existing = await db.execute(select(Hospital).where(Hospital.id == h.id))
        if not existing.scalar_one_or_none():
            db.add(h)

    await db.flush()
    print(f"  ✓ {len(hospitals)} hospitals seeded")
    return hospitals


async def seed_operator(db):
    """Create a default operator user."""
    print("👤 Seeding operator user...")
    existing = await db.execute(select(User).where(User.phone == "+919999000001"))
    if existing.scalar_one_or_none():
        print("  ⊘ Operator already exists")
        result = await db.execute(select(User).where(User.phone == "+919999000001"))
        return result.scalar_one()

    operator = User(
        id="OP001",
        phone="+919999000001",
        name="Village Health Worker",
        password_hash=hash_password(DEFAULT_PASSWORD),
        role=UserRole.OPERATOR,
        district_id=DISTRICT_ID,
        block_id="BLK01",
        is_verified=True,
    )
    db.add(operator)
    await db.flush()
    print("  ✓ Operator created (phone: +919999000001, password: drishti123)")
    return operator


async def seed_doctors(db):
    """Seed doctors from CSV."""
    print("🩺 Seeding doctors...")
    csv_path = settings.DOCTOR_CSV_PATH
    doctors = []

    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing = await db.execute(select(User).where(User.phone == row["phone"]))
            if existing.scalar_one_or_none():
                continue

            user = User(
                id=row["id"],
                phone=row["phone"],
                name=row["name"],
                password_hash=hash_password(DEFAULT_PASSWORD),
                role=UserRole.DOCTOR,
                district_id=DISTRICT_ID,
                is_verified=True,
            )
            db.add(user)
            await db.flush()

            profile = DoctorProfile(
                user_id=user.id,
                reg_no=row["reg_no"],
                specialization=row.get("specialization", "Ophthalmology"),
                hospital_id=row["hospital_id"],
                verified_at=datetime.now(timezone.utc),
            )
            db.add(profile)
            doctors.append(user)

    await db.flush()
    print(f"  ✓ {len(doctors)} doctors seeded (password: drishti123)")
    return doctors


async def seed_officers(db):
    """Seed officers from CSV."""
    print("🏛️ Seeding officers...")
    csv_path = settings.OFFICER_CSV_PATH
    officers = []

    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing = await db.execute(select(User).where(User.phone == row["phone"]))
            if existing.scalar_one_or_none():
                continue

            user = User(
                id=row["id"],
                phone=row["phone"],
                name=row["name"],
                password_hash=hash_password(DEFAULT_PASSWORD),
                role=UserRole.OFFICER,
                district_id=row["district_id"],
                block_id=row["block_id"],
                is_verified=True,
            )
            db.add(user)
            await db.flush()

            jurisdiction = OfficerJurisdiction(
                officer_id=user.id,
                level=row.get("level", "block"),
                location_id=row["block_id"],
            )
            db.add(jurisdiction)
            officers.append(user)

    await db.flush()
    print(f"  ✓ {len(officers)} officers seeded (password: drishti123)")
    return officers


async def seed_admin(db):
    """Create a system admin user."""
    print("🔑 Seeding admin user...")
    existing = await db.execute(select(User).where(User.phone == "+919999000000"))
    if existing.scalar_one_or_none():
        print("  ⊘ Admin already exists")
        return

    admin = User(
        id="ADMIN001",
        phone="+919999000000",
        name="System Administrator",
        password_hash=hash_password("admin123"),
        role=UserRole.ADMIN,
        district_id=DISTRICT_ID,
        is_verified=True,
    )
    db.add(admin)
    await db.flush()
    print("  ✓ Admin created (phone: +919999000000, password: admin123)")


async def seed_patients(db, operator_id: str):
    """Generate 50 demo patients."""
    print("🧑‍🤝‍🧑 Seeding 50 demo patients...")
    patients = []

    for i in range(50):
        gender = random.choice(["M", "F"])
        if gender == "M":
            first_name = random.choice(INDIAN_FIRST_NAMES_M)
        else:
            first_name = random.choice(INDIAN_FIRST_NAMES_F)
        last_name = random.choice(INDIAN_LAST_NAMES)

        patient = Patient(
            id=str(uuid.uuid4()),
            local_id=f"LOC-{uuid.uuid4().hex[:8].upper()}",
            name=f"{first_name} {last_name}",
            age=random.randint(35, 75),
            gender=gender,
            mobile=f"+91{random.randint(7000000000, 9999999999)}",
            mobile_verified=random.choice([True, True, True, False]),  # 75% verified
            district_id=DISTRICT_ID,
            block_id=random.choice(BLOCKS),
            diabetes_type=random.choice(["Type1", "Type2", "Type2", "Type2"]),  # Type2 is more common
            diabetes_duration_years=random.randint(1, 20),
            hba1c=round(random.uniform(5.5, 12.0), 1),
            created_by=operator_id,
        )
        patients.append(patient)

    db.add_all(patients)
    await db.flush()
    print(f"  ✓ {len(patients)} patients seeded")
    return patients


async def seed_screenings_and_referrals(db, patients, operator_id):
    """Create 20 demo screenings with mix of grades, auto-refer severe ones."""
    print("📸 Seeding 20 demo screenings + referrals...")

    # Severity distribution: 5x Grade0, 5x Grade1, 4x Grade2, 4x Grade3, 2x Grade4
    severity_distribution = [0]*5 + [1]*5 + [2]*4 + [3]*4 + [4]*2
    random.shuffle(severity_distribution)

    selected_patients = random.sample(patients, min(20, len(patients)))
    screenings = []
    referrals = []

    for i, (patient, severity) in enumerate(zip(selected_patients, severity_distribution)):
        image_hash = uuid.uuid4().hex + uuid.uuid4().hex[:32]  # fake 64-char SHA-256
        eye = random.choice(["OD", "OS"])
        quality_score = round(random.uniform(0.85, 0.98), 2)
        efs_score = round(random.uniform(0.65, 0.95), 2)
        dme_risk = round(random.uniform(0.0, 0.8), 2) if severity >= 2 else round(random.uniform(0.0, 0.2), 2)

        screening = ScreeningEvent(
            id=str(uuid.uuid4()),
            patient_id=patient.id,
            operator_id=operator_id,
            eye=eye,
            image_hash=image_hash,
            quality_score=quality_score,
            quality_defects=[],
            lesion_masks_rle=_generate_mock_lesion_rle(severity),
            severity_level=severity,
            dme_risk=dme_risk,
            rule_trace=RULE_TRACES[severity],
            efs_score=efs_score,
            captured_at=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 14)),
            synced_at=datetime.now(timezone.utc),
        )
        screenings.append(screening)
        db.add(screening)
        await db.flush()

        # Auto-refer for severity >= 2
        if severity >= 2:
            referral = Referral(
                id=str(uuid.uuid4()),
                screening_event_id=screening.id,
                referral_code=f"DRS-{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6))}",
                state=ReferralState.QUEUED,
            )
            referrals.append(referral)
            db.add(referral)

    await db.flush()
    print(f"  ✓ {len(screenings)} screenings created")
    print(f"  ✓ {len(referrals)} referrals auto-created (severity ≥ 2)")
    return screenings, referrals


def _generate_mock_lesion_rle(severity: int) -> dict:
    """Generate mock RLE-encoded lesion masks for demo."""
    lesion_types = {
        0: {},
        1: {"MA": "10 5 20 3 50 2"},
        2: {"MA": "10 5 20 3 50 2", "HE": "100 10 200 8", "EX": "150 6"},
        3: {"MA": "10 5 20 3", "HE": "100 15 200 12", "EX": "150 8", "CWS": "300 5", "IRMA": "400 3"},
        4: {"MA": "10 5", "HE": "100 20 200 15", "EX": "150 10", "CWS": "300 8", "VB": "350 5", "IRMA": "400 4", "NV": "500 10"},
    }
    return lesion_types.get(severity, {})


async def seed_mock_notifications(db, referrals):
    """Create mock notification logs for some referrals."""
    print("🔔 Seeding mock notification logs...")
    count = 0

    for referral in referrals[:10]:
        # Get patient_id from screening
        result = await db.execute(
            select(ScreeningEvent.patient_id).where(ScreeningEvent.id == referral.screening_event_id)
        )
        patient_id = result.scalar_one_or_none()
        if not patient_id:
            continue

        scheduled_at = datetime.now(timezone.utc) + timedelta(days=3)
        templates = [
            ("schedule_confirm", 0, "sent"),
            ("reminder_48h", -48, "pending"),
            ("reminder_2h", -2, "pending"),
            ("missed_24h", 24, "pending"),
        ]

        for template_key, offset_hours, status in templates:
            fire_at = scheduled_at + timedelta(hours=offset_hours)
            notification = NotificationLog(
                id=str(uuid.uuid4()),
                referral_id=referral.id,
                patient_id=patient_id,
                channel="mock",
                template_key=template_key,
                status=status,
                scheduled_for=fire_at,
                sent_at=datetime.now(timezone.utc) if status == "sent" else None,
                delivered_at=datetime.now(timezone.utc) if status == "sent" else None,
                cost_paise=0,
                meta={"engine": "mock_seed"},
            )
            db.add(notification)
            count += 1

    await db.flush()
    print(f"  ✓ {count} mock notification logs created")


async def main():
    """Run the full seed process."""
    print("\n" + "=" * 60)
    print("  DRISHTI-LENS — Database Seed Script")
    print("=" * 60 + "\n")

    # Create all tables
    async with engine.begin() as conn:
        from models import user, patient, screening, referral, hospital, doctor, notification, officer  # noqa
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        try:
            await seed_hospitals(db)
            operator = await seed_operator(db)
            await seed_doctors(db)
            await seed_officers(db)
            await seed_admin(db)
            patients = await seed_patients(db, operator.id)
            screenings, referrals = await seed_screenings_and_referrals(db, patients, operator.id)
            await seed_mock_notifications(db, referrals)

            await db.commit()

            print("\n" + "=" * 60)
            print("  ✅ Seed complete! Login credentials:")
            print("  ─────────────────────────────────────")
            print("  Admin:    +919999000000 / admin123")
            print("  Operator: +919999000001 / drishti123")
            print("  Officer:  +919876540001 / drishti123")
            print("  Doctor:   +919876543001 / drishti123")
            print("=" * 60 + "\n")

        except Exception as e:
            await db.rollback()
            print(f"\n❌ Seed failed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
