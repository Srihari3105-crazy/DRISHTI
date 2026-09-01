"""
DRISHTI-LENS Event Bus
In-process async event bus for MVP. NATS adapter can be added later.
"""
import asyncio
from typing import Callable, Any
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class EventBus:
    """Simple in-process pub/sub event bus using asyncio."""

    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: Callable):
        """Register a handler for an event type."""
        self._subscribers[event_type].append(handler)
        logger.info(f"Subscribed {handler.__name__} to '{event_type}'")

    async def publish(self, event_type: str, data: dict[str, Any]):
        """Publish an event to all subscribers. Non-blocking — fires and forgets."""
        handlers = self._subscribers.get(event_type, [])
        logger.info(f"Publishing '{event_type}' to {len(handlers)} handlers: {data.get('referral_id', 'N/A')}")
        for handler in handlers:
            try:
                asyncio.create_task(handler(data))
            except Exception as e:
                logger.error(f"Error in handler {handler.__name__} for '{event_type}': {e}")

    def clear(self):
        """Remove all subscriptions."""
        self._subscribers.clear()


# Singleton event bus
event_bus = EventBus()


# Event type constants
class Events:
    REFERRAL_CREATED = "referral.created"
    REFERRAL_ASSIGNED = "referral.assigned"
    APPOINTMENT_SCHEDULED = "appointment.scheduled"
    VISIT_VERIFIED = "visit.verified"
    RETAKE_REQUESTED = "retake.requested"
