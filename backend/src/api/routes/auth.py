"""Auth routes — register, login, Udyam lookup."""

import uuid
from datetime import timedelta

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from src.api.dependencies import DBSession
from src.core.security import create_access_token, hash_password, verify_password
from src.core.logging import log
from src.db.models.user import User, UserRole
from src.db.models.mse import MSE

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    udyam_number: str
    mobile: str
    password: str
    role: str = "mse"


class LoginRequest(BaseModel):
    mobile: str
    password: str


class UdyamLookupRequest(BaseModel):
    udyam_number: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: str


@router.post("/register", response_model=AuthResponse)
async def register(req: RegisterRequest, db: DBSession):
    """Register a new MSE user."""
    # Check if mobile already exists
    result = await db.execute(select(User).where(User.mobile == req.mobile))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Mobile number already registered",
        )

    user = User(
        id=uuid.uuid4(),
        role=req.role,
        mobile=req.mobile,
        hashed_password=hash_password(req.password),
        is_active=True,
    )
    db.add(user)
    await db.flush()

    # Create MSE profile if role is mse
    if req.role == "mse":
        mse = MSE(
            id=uuid.uuid4(),
            user_id=user.id,
            udyam_number=req.udyam_number.strip().upper() if req.udyam_number else None,
        )
        db.add(mse)

    await db.flush()

    token = create_access_token(
        data={"sub": str(user.id), "role": user.role},
        expires_delta=timedelta(hours=24),
    )

    log.info(f"Registered new user: {user.id} role={user.role}")
    return AuthResponse(
        access_token=token,
        user_id=str(user.id),
        role=user.role,
    )


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest, db: DBSession):
    """Login with mobile + password."""
    result = await db.execute(select(User).where(User.mobile == req.mobile))
    user = result.scalar_one_or_none()

    if not user or not verify_password(req.password, user.hashed_password or ""):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    token = create_access_token(
        data={"sub": str(user.id), "role": user.role},
        expires_delta=timedelta(hours=24),
    )

    return AuthResponse(
        access_token=token,
        user_id=str(user.id),
        role=user.role,
    )


@router.get("/me")
async def me(db: DBSession, current_user: dict = None):
    """Get current user profile."""
    from src.api.dependencies import get_current_user_role
    # This endpoint requires auth — handled via dependency injection in real call
    return {"message": "Use /me with Authorization header"}


@router.post("/udyam-lookup")
async def udyam_lookup(req: UdyamLookupRequest):
    """Fetch Udyam registration data (mocked for PoC)."""
    from src.tools.core.fetch_udyam_data import MOCK_UDYAM_DATA, FetchUdyamDataTool

    tool = FetchUdyamDataTool()
    result = await tool.execute({"udyam_number": req.udyam_number}, {})
    return result


@router.post("/verify-otp")
async def verify_otp(mobile: str, otp: str):
    """Verify OTP (mocked — always succeeds for demo)."""
    return {"verified": True, "mobile": mobile}
