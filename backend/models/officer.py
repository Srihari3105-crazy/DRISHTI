"""OfficerJurisdiction — maps officers to their geographic scope."""
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base


class OfficerJurisdiction(Base):
    __tablename__ = "officer_jurisdiction"

    officer_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    level = Column(String(20), nullable=False, primary_key=True)  # block, district, state
    location_id = Column(String(10), nullable=False, primary_key=True)

    officer = relationship("User", backref="jurisdictions")

    def __repr__(self):
        return f"<Jurisdiction officer={self.officer_id[:8]} {self.level}={self.location_id}>"
