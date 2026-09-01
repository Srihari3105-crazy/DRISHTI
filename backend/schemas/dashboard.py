"""Dashboard schemas for officer statistics."""
from pydantic import BaseModel
from typing import Optional


class OfficerDashboard(BaseModel):
    total_referred: int = 0
    assigned: int = 0
    scheduled: int = 0
    visited: int = 0
    closed: int = 0
    closure_rate: float = 0.0  # percentage
    avg_days_to_close: float = 0.0
    by_block: dict[str, dict[str, int]] = {}  # {block_id: {state: count}}
    by_severity: dict[int, int] = {}  # {severity_level: count}


class DoctorDashboardStats(BaseModel):
    total_assigned: int = 0
    pending: int = 0
    scheduled: int = 0
    visited: int = 0
    avg_days_to_schedule: float = 0.0
