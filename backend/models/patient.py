"""Patient model — registered by operator in the field."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean
from core.database import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    abha_id = Column(String(14), unique=True, nullable=True, index=True)
    local_id = Column(String(50), unique=True, nullable=True, index=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(10), nullable=False)  # M, F, O
    mobile = Column(String(15), nullable=False)
    mobile_verified = Column(Boolean, default=False)
    email = Column(String(100), nullable=True)
    district_id = Column(String(10), nullable=False, index=True)
    block_id = Column(String(10), nullable=False, index=True)
    phc_id = Column(String(10), nullable=True)
    diabetes_type = Column(String(20), nullable=True)  # Type1, Type2, Unknown
    diabetes_duration_years = Column(Integer, nullable=True)
    hba1c = Column(Float, nullable=True)
    created_by = Column(String(36), nullable=True)  # operator user_id
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Patient {self.name} ({self.district_id}/{self.block_id})>"
