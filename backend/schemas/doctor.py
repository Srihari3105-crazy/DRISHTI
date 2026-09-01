"""Doctor registration schema — RegNo match against CSV."""
from pydantic import BaseModel, Field
from typing import Optional


class DoctorRegisterRequest(BaseModel):
    phone: str = Field(..., pattern=r"^\+91\d{10}$")
    password: str = Field(..., min_length=6)
    name: str = Field(..., min_length=2, max_length=100)
    reg_no: str = Field(..., min_length=3, max_length=30)
    hospital_id: str


class DoctorRegisterResponse(BaseModel):
    id: str
    phone: str
    name: str
    role: str = "doctor"
    reg_no: str
    hospital_name: str
    verified: bool
    message: str
