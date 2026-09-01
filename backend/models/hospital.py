"""Hospital master — seeded from CSV."""
import uuid
from sqlalchemy import Column, String, Float, Boolean, Text
from core.database import Base


class Hospital(Base):
    __tablename__ = "hospitals"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    address = Column(Text, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    district_id = Column(String(10), nullable=False, index=True)
    state_id = Column(String(10), nullable=False, default="RJ")
    phone = Column(String(15), nullable=True)
    facility_type = Column(String(20), nullable=False)  # DH, CHC, PHC, VC
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<Hospital {self.name} ({self.facility_type})>"
