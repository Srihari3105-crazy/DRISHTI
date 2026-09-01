"""DoctorProfile — links User to registration number and hospital."""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from core.database import Base


class DoctorProfile(Base):
    __tablename__ = "doctor_profiles"

    user_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    reg_no = Column(String(30), unique=True, nullable=True, index=True)
    specialization = Column(String(50), default="Ophthalmology")
    hospital_id = Column(String(36), ForeignKey("hospitals.id"), nullable=True)
    hospital_name = Column(String(200), nullable=True)
    hospital_location = Column(String(200), nullable=True)
    floor_number = Column(String(50), nullable=True)
    room_number = Column(String(50), nullable=True)
    max_pending = Column(Integer, default=10)  # max referrals before full
    verified_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    user = relationship("User", backref="doctor_profile")
    hospital = relationship("Hospital", backref="doctors")

    def __repr__(self):
        return f"<DoctorProfile reg={self.reg_no} hospital={self.hospital_name}>"

