"""ScreeningEvent model — one per eye per capture session."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from core.database import Base


class ScreeningEvent(Base):
    __tablename__ = "screening_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False, index=True)
    operator_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    eye = Column(String(3), nullable=False)  # "OD" or "OS"
    image_path = Column(String(500), nullable=True)  # server-side path after sync
    image_hash = Column(String(64), nullable=False)  # SHA-256 of JPEG
    quality_score = Column(Float, nullable=False)
    quality_defects = Column(JSON, nullable=True)  # ["defocus", "glare", ...]
    lesion_masks_rle = Column(JSON, nullable=True)  # {lesion_type: RLE_string}
    severity_level = Column(Integer, nullable=False)  # 0-4 ICDR
    dme_risk = Column(Float, nullable=True)
    rule_trace = Column(JSON, nullable=False)  # [{"rule_id": "ICDR-3.2", "met": true, "zones": [...]}]
    efs_score = Column(Float, nullable=False)  # 0.0-1.0
    captured_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    synced_at = Column(DateTime, nullable=True)
    adjudication_status = Column(String(20), default="pending")  # pending/confirmed/downgraded/upgraded/retake
    gradcam_path = Column(String(500), nullable=True)
    report_path = Column(String(500), nullable=True)
    quality_decision = Column(String(30), nullable=True)
    enhancement_applied = Column(String(10), nullable=True)

    patient = relationship("Patient", backref="screenings")
    operator = relationship("User", backref="screenings_done")

    def __repr__(self):
        return f"<Screening {self.id[:8]} eye={self.eye} severity={self.severity_level}>"
