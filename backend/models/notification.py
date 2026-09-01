"""NotificationLog — tracks every reminder (mock or real)."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from core.database import Base


class NotificationLog(Base):
    __tablename__ = "notification_log"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    referral_id = Column(String(36), ForeignKey("referrals.id"), nullable=False, index=True)
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False)
    channel = Column(String(20), nullable=False)  # whatsapp, sms, ivr, email, mock
    template_key = Column(String(50), nullable=False)  # schedule_confirm, reminder_48h, reminder_2h, missed_24h, thank_you
    status = Column(String(20), default="pending")  # pending, sent, delivered, failed, cancelled
    scheduled_for = Column(DateTime, nullable=True)  # when this notification should fire
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    cost_paise = Column(Integer, default=0)
    meta = Column(JSON, nullable=True)  # provider_msg_id, error, etc.
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    referral = relationship("Referral", backref="notifications")
    patient = relationship("Patient", backref="notifications")

    def __repr__(self):
        return f"<Notification {self.template_key} via {self.channel} → {self.status}>"
