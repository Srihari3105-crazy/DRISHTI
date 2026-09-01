"""Screening event schemas for sync from mobile app."""
from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


class ScreeningEventCreate(BaseModel):
    patient_id: str
    eye: str = Field(..., pattern=r"^(OD|OS)$")
    image_hash: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    quality_score: float = Field(..., ge=0.0, le=1.0)
    quality_defects: Optional[list[str]] = None
    lesion_masks_rle: Optional[dict[str, str]] = None  # {lesion_type: RLE_string}
    severity_level: int = Field(..., ge=0, le=4)
    dme_risk: Optional[float] = Field(None, ge=0.0, le=1.0)
    rule_trace: list[dict[str, Any]]  # [{"rule_id": "ICDR-3.2", "met": true, ...}]
    efs_score: float = Field(..., ge=0.0, le=1.0)
    captured_at: Optional[datetime] = None
    # Whether to auto-create a referral for referable grades (severity >= 2)
    auto_refer: bool = True


class ScreeningEventResponse(BaseModel):
    id: str
    patient_id: str
    operator_id: str
    eye: str
    image_hash: str
    image_path: Optional[str] = None
    quality_score: float
    quality_defects: Optional[list[str]] = None
    lesion_masks_rle: Optional[dict[str, str]] = None
    severity_level: int
    dme_risk: Optional[float] = None
    rule_trace: list[dict[str, Any]]
    efs_score: float
    captured_at: datetime
    synced_at: Optional[datetime] = None
    adjudication_status: str = "pending"
    referral_id: Optional[str] = None  # populated if auto-referred

    model_config = {"from_attributes": True}
