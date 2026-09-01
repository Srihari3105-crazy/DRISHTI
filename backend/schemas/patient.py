"""Patient schemas for registration and verification."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PatientCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    age: int = Field(..., ge=1, le=120)
    gender: str = Field(..., pattern=r"^(M|F|O)$")
    mobile: str = Field(..., pattern=r"^\+91\d{10}$")
    email: Optional[str] = None
    abha_id: Optional[str] = Field(None, pattern=r"^\d{14}$")
    local_id: Optional[str] = None
    district_id: str
    block_id: str
    phc_id: Optional[str] = None
    diabetes_type: Optional[str] = Field(None, pattern=r"^(Type1|Type2|Unknown)$")
    diabetes_duration_years: Optional[int] = Field(None, ge=0)
    hba1c: Optional[float] = Field(None, ge=3.0, le=15.0)


class PatientResponse(BaseModel):
    id: str
    abha_id: Optional[str] = None
    local_id: Optional[str] = None
    name: str
    age: int
    gender: str
    mobile: str
    mobile_verified: bool = False
    email: Optional[str] = None
    district_id: str
    block_id: str
    phc_id: Optional[str] = None
    diabetes_type: Optional[str] = None
    diabetes_duration_years: Optional[int] = None
    hba1c: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class OTPSendRequest(BaseModel):
    mobile: str = Field(..., pattern=r"^\+91\d{10}$")


class OTPVerifyRequest(BaseModel):
    otp: str = Field(..., pattern=r"^\d{6}$")


class OTPResponse(BaseModel):
    message: str
    otp_sent: bool = True
    # In dev/demo mode, include the OTP for convenience
    debug_otp: Optional[str] = None
