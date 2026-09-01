"""Referral schemas — CRUD, assign, schedule, visit, paginated list."""
from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime
from schemas.auth import UserPublic


class ReferralResponse(BaseModel):
    id: str
    referral_code: str
    state: str
    screening_event_id: str
    assigned_doctor_id: Optional[str] = None
    assigned_officer_id: Optional[str] = None
    hospital_id: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    appointment_token: Optional[str] = None
    visit_notes: Optional[str] = None
    retake_reason: Optional[str] = None
    closure_reason: Optional[str] = None
    created_at: datetime
    closed_at: Optional[datetime] = None

    # Nested objects (populated via joins)
    patient_name: Optional[str] = None
    patient_age: Optional[int] = None
    patient_mobile: Optional[str] = None
    doctor_name: Optional[str] = None
    hospital_name: Optional[str] = None
    severity_level: Optional[int] = None
    efs_score: Optional[float] = None
    eye: Optional[str] = None

    model_config = {"from_attributes": True}


class PaginatedReferrals(BaseModel):
    items: list[ReferralResponse]
    total: int
    page: int
    size: int


class AssignRequest(BaseModel):
    doctor_id: str


class ScheduleRequest(BaseModel):
    scheduled_at: datetime
    hospital_id: str


class VisitRequest(BaseModel):
    notes: Optional[str] = None


class RetakeRequest(BaseModel):
    reason: str = Field(..., min_length=5)


class AutoAssignResponse(BaseModel):
    assigned: int
    skipped: int
    details: list[dict[str, str]] = []  # [{referral_code, doctor_name}]
