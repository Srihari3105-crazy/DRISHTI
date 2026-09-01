"""
Auth API — login, register, and token refresh.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from core.database import get_db
from core.security import verify_password, hash_password, create_access_token, create_refresh_token, decode_token
from models.user import User, UserRole
from schemas.auth import LoginRequest, SignupRequest, TokenResponse, UserPublic

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user with phone + password → access + refresh tokens."""
    result = await db.execute(select(User).where(User.phone == request.phone))
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone number or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    token_data = {
        "sub": user.id,
        "role": user.role.value,
        "name": user.name,
        "district_id": user.district_id,
        "block_id": user.block_id,
    }

    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        user=UserPublic(
            id=user.id,
            phone=user.phone,
            name=user.name,
            role=user.role.value,
            district_id=user.district_id,
            block_id=user.block_id,
            is_verified=user.is_verified,
        ),
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: SignupRequest, db: AsyncSession = Depends(get_db)):
    """Self-registration for doctors, officers, operators.
    - Only one admin account is allowed system-wide.
    - Patients register through the mobile app.
    """
    # Block patient role via web signup
    if request.role == "patient":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patients must register through the mobile app.",
        )

    # Singleton guard: only one admin allowed
    if request.role == "admin":
        count_result = await db.execute(
            select(func.count()).select_from(User).where(User.role == UserRole.ADMIN)
        )
        if count_result.scalar() >= 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An admin account already exists. Only one admin is permitted.",
            )

    # Check phone not already registered
    existing = await db.execute(select(User).where(User.phone == request.phone))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This phone number is already registered.",
        )

    # Check email not already registered if provided
    if request.email:
        existing_email = await db.execute(select(User).where(User.email == request.email.strip().lower()))
        if existing_email.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This email address is already registered.",
            )

    import uuid
    user = User(
        id=str(uuid.uuid4()),
        phone=request.phone,
        email=request.email.strip().lower() if request.email else None,
        name=request.name,
        password_hash=hash_password(request.password),
        role=UserRole(request.role),
        district_id=request.district_id,
        block_id=request.block_id,
        is_verified=False,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token_data = {
        "sub": user.id,
        "role": user.role.value,
        "name": user.name,
        "email": user.email,
        "district_id": user.district_id,
        "block_id": user.block_id,
    }

    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        user=UserPublic(
            id=user.id,
            phone=user.phone,
            email=user.email,
            name=user.name,
            role=user.role.value,
            district_id=user.district_id,
            block_id=user.block_id,
            is_verified=user.is_verified,
        ),
    )


@router.post("/refresh", response_model=dict)
async def refresh_token(refresh_token: str, db: AsyncSession = Depends(get_db)):

    """Refresh an access token using a valid refresh token."""
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    token_data = {
        "sub": user.id,
        "role": user.role.value,
        "name": user.name,
        "district_id": user.district_id,
        "block_id": user.block_id,
    }

    return {
        "access_token": create_access_token(token_data),
        "token_type": "bearer",
    }
