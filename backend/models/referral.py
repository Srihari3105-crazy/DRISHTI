"""Referral model with state machine enum."""
import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from core.database import Base


class ReferralState(str, enum.Enum):
    QUEUED = "queued"
    ASSIGNED = "assigned"
    SCHEDULED = "scheduled"
    REMINDERS_ACTIVE = "reminders_active"
    VISITED = "visited"
    CLOSED = "closed"


# Valid state transitions
VALID_TRANSITIONS = {
    ReferralState.QUEUED: [ReferralState.ASSIGNED],
    ReferralState.ASSIGNED: [ReferralState.SCHEDULED, ReferralState.QUEUED],  # QUEUED for reassign
    ReferralState.SCHEDULED: [ReferralState.REMINDERS_ACTIVE, ReferralState.ASSIGNED],  # back to ASSIGNED for reschedule
    ReferralState.REMINDERS_ACTIVE: [ReferralState.VISITED, ReferralState.SCHEDULED],
    ReferralState.VISITED: [ReferralState.CLOSED],
    ReferralState.CLOSED: [],  # terminal state
}


def can_transition(current: ReferralState, target: ReferralState) -> bool:
    return target in VALID_TRANSITIONS.get(current, [])


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    screening_event_id = Column(String(36), ForeignKey("screening_events.id"), unique=True, nullable=False, index=True)
    referral_code = Column(String(12), unique=True, nullable=False, index=True)  # e.g., "DRS-7K9M2X"
    state = Column(SQLEnum(ReferralState), default=ReferralState.QUEUED, nullable=False, index=True)
    assigned_doctor_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    assigned_officer_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    hospital_id = Column(String(36), ForeignKey("hospitals.id"), nullable=True)
    scheduled_at = Column(DateTime, nullable=True)
    appointment_token = Column(String(20), unique=True, nullable=True)  # e.g., "DRS-7K9M2"
    visit_notes = Column(Text, nullable=True)
    retake_reason = Column(Text, nullable=True)
    closure_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    closed_at = Column(DateTime, nullable=True)

    screening_event = relationship("ScreeningEvent", backref="referral")
    doctor = relationship("User", foreign_keys=[assigned_doctor_id], backref="assigned_referrals")
    officer = relationship("User", foreign_keys=[assigned_officer_id])
    hospital = relationship("Hospital", backref="referrals")

    __table_args__ = (
        Index("ix_referral_state_created", "state", "created_at"),
    )

    def __repr__(self):
        return f"<Referral {self.referral_code} state={self.state.value}>"
