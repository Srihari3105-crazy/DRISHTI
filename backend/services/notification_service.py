"""
Notification Service — Mock reminder engine for MVP.
Creates notification_log entries on appointment events.
"""
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from models.notification import NotificationLog
from models.referral import Referral
from models.screening import ScreeningEvent
from models.patient import Patient
from core.events import event_bus, Events
import logging

logger = logging.getLogger(__name__)


REMINDER_TEMPLATES = [
    {"template_key": "schedule_confirm", "offset_hours": 0, "channel": "mock"},
    {"template_key": "reminder_48h", "offset_hours": -48, "channel": "mock"},
    {"template_key": "reminder_2h", "offset_hours": -2, "channel": "mock"},
    {"template_key": "missed_24h", "offset_hours": 24, "channel": "mock"},
]


async def create_reminder_schedule(db: AsyncSession, referral_id: str, scheduled_at: datetime, patient_id: str):
    """
    Create 4 notification_log entries when an appointment is scheduled:
    1. Immediate schedule confirmation
    2. T-48h reminder
    3. T-2h reminder  
    4. T+24h missed appointment follow-up
    """
    notifications = []

    for template in REMINDER_TEMPLATES:
        offset = timedelta(hours=template["offset_hours"])
        fire_at = scheduled_at + offset if template["offset_hours"] != 0 else datetime.now(timezone.utc)

        notification = NotificationLog(
            id=str(uuid.uuid4()),
            referral_id=referral_id,
            patient_id=patient_id,
            channel=template["channel"],
            template_key=template["template_key"],
            status="sent" if template["offset_hours"] == 0 else "pending",
            scheduled_for=fire_at,
            sent_at=datetime.now(timezone.utc) if template["offset_hours"] == 0 else None,
            delivered_at=datetime.now(timezone.utc) if template["offset_hours"] == 0 else None,
            cost_paise=0,
            meta={"engine": "mock", "message": _get_template_message(template["template_key"])},
        )
        notifications.append(notification)

    db.add_all(notifications)
    await db.flush()

    logger.info(f"Created {len(notifications)} mock notifications for referral {referral_id}")
    return notifications


async def cancel_pending_reminders(db: AsyncSession, referral_id: str):
    """Cancel all pending reminders when patient visits (visit verified)."""
    result = await db.execute(
        update(NotificationLog)
        .where(
            NotificationLog.referral_id == referral_id,
            NotificationLog.status == "pending",
        )
        .values(status="cancelled")
        .returning(NotificationLog.id)
    )
    cancelled_ids = result.scalars().all()
    logger.info(f"Cancelled {len(cancelled_ids)} pending notifications for referral {referral_id}")
    return len(cancelled_ids)


async def create_thank_you_notification(db: AsyncSession, referral_id: str, patient_id: str):
    """Send thank-you notification after visit verification."""
    notification = NotificationLog(
        id=str(uuid.uuid4()),
        referral_id=referral_id,
        patient_id=patient_id,
        channel="mock",
        template_key="thank_you",
        status="sent",
        scheduled_for=datetime.now(timezone.utc),
        sent_at=datetime.now(timezone.utc),
        delivered_at=datetime.now(timezone.utc),
        cost_paise=0,
        meta={"engine": "mock", "message": _get_template_message("thank_you")},
    )
    db.add(notification)
    await db.flush()
    return notification


def _get_template_message(template_key: str) -> str:
    """Get human-readable message for each template."""
    messages = {
        "schedule_confirm": "Your eye check-up appointment has been scheduled. Please bring your referral code and ID.",
        "reminder_48h": "Reminder: Your eye check-up appointment is in 2 days. Don't forget to visit the hospital.",
        "reminder_2h": "Your eye check-up appointment is in 2 hours. Please head to the hospital now.",
        "missed_24h": "We noticed you may have missed your eye check-up appointment. Please contact the hospital to reschedule.",
        "thank_you": "Thank you for visiting the hospital for your eye check-up! Take care of your eyes. 🙏",
    }
    return messages.get(template_key, "DRISHTI-LENS notification")


# Event handlers — registered in main.py on startup
async def on_appointment_scheduled(data: dict):
    """Handle appointment.scheduled event."""
    from core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        try:
            referral_id = data["referral_id"]
            scheduled_at = datetime.fromisoformat(data["scheduled_at"])

            # Get patient_id from referral → screening → patient
            result = await db.execute(
                select(Referral).where(Referral.id == referral_id)
            )
            referral = result.scalar_one_or_none()
            if not referral:
                return

            result = await db.execute(
                select(ScreeningEvent.patient_id).where(ScreeningEvent.id == referral.screening_event_id)
            )
            patient_id = result.scalar_one_or_none()
            if not patient_id:
                return

            await create_reminder_schedule(db, referral_id, scheduled_at, patient_id)
            await db.commit()
        except Exception as e:
            logger.error(f"Error handling appointment.scheduled: {e}")
            await db.rollback()


async def on_visit_verified(data: dict):
    """Handle visit.verified event — cancel reminders + send thank you."""
    from core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        try:
            referral_id = data["referral_id"]

            # Cancel pending reminders
            await cancel_pending_reminders(db, referral_id)

            # Get patient_id
            result = await db.execute(
                select(Referral).where(Referral.id == referral_id)
            )
            referral = result.scalar_one_or_none()
            if not referral:
                return

            result = await db.execute(
                select(ScreeningEvent.patient_id).where(ScreeningEvent.id == referral.screening_event_id)
            )
            patient_id = result.scalar_one_or_none()
            if patient_id:
                await create_thank_you_notification(db, referral_id, patient_id)

            await db.commit()
        except Exception as e:
            logger.error(f"Error handling visit.verified: {e}")
            await db.rollback()
