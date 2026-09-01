"""Auth schemas for login, register, token, and refresh."""
from pydantic import BaseModel, Field
from typing import Optional, Literal


class LoginRequest(BaseModel):
    phone: str = Field(..., pattern=r"^\+91\d{10}$", examples=["+919876543210"])
    password: str = Field(..., min_length=6)


class SignupRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: Optional[str] = Field(None, max_length=100)
    phone: str = Field(..., pattern=r"^\+91\d{10}$", examples=["+919876543210"])
    password: str = Field(..., min_length=6, max_length=72)
    role: Literal["doctor", "officer", "operator", "admin"]
    district_id: Optional[str] = None
    block_id: Optional[str] = None
    pincode: Optional[str] = None
    area: Optional[str] = None
    state: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserPublic"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserPublic(BaseModel):
    id: str
    phone: str
    email: Optional[str] = None
    name: str
    role: str
    district_id: Optional[str] = None
    block_id: Optional[str] = None
    is_verified: bool = False

    model_config = {"from_attributes": True}


# Rebuild to resolve forward ref
TokenResponse.model_rebuild()
