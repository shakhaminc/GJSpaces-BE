from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.auth import (
    LoginInitiateResponse,
    LoginRequest,
    ResendOTPRequest,
    TokenResponse,
    VerifyOTPRequest,
)
from app.schemas.user import UserMeResponse
from app.services.email_service import dispatch_background_email, send_login_otp_email
from app.services.otp_service import (
    OTP_EXPIRY_MINUTES,
    generate_and_save_login_otp,
    verify_login_otp,
)
from app.services.user_service import authenticate_user, serialize_user_me

router = APIRouter(prefix="/auth", tags=["Authentication & Session"])


@router.post("/login", response_model=LoginInitiateResponse)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Authenticates credentials and sends a 6-digit verification OTP to the user's registered email."""
    user = await authenticate_user(db, credentials.email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact Super Admin."
        )

    # Generate & persist OTP in database in milliseconds
    otp_code, recipient_name = await generate_and_save_login_otp(db, user)

    # Dispatch email detached in background - returns API response in < 50ms
    dispatch_background_email(
        send_login_otp_email(
            to_email=user.email,
            recipient_name=recipient_name,
            otp_code=otp_code,
            expire_minutes=OTP_EXPIRY_MINUTES,
        )
    )

    return LoginInitiateResponse(
        message=f"Verification OTP has been sent to your registered email ({user.email}).",
        email=user.email,
        otp_sent=True,
    )


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(
    payload: VerifyOTPRequest,
    db: AsyncSession = Depends(get_db)
):
    """Verifies the 6-digit email OTP and returns the signed JWT access token."""
    user = await verify_login_otp(db, payload.email, payload.otp)
    access_token = create_access_token(subject=user.id)
    role_name = user.role.role_name if user.role else "Unknown"

    return TokenResponse(
        message="Authentication successful.",
        access_token=access_token,
        token_type="bearer",
        role_name=role_name,
        email=user.email,
    )


@router.post("/resend-otp", response_model=LoginInitiateResponse)
async def resend_otp(
    payload: ResendOTPRequest,
    db: AsyncSession = Depends(get_db)
):
    """Regenerates and resends a fresh 6-digit verification code to the registered email."""
    stmt = (
        select(User)
        .where(
            ((User.email == payload.email) | (User.contact_number == payload.email))
            & (User.is_deleted == False)
        )
        .options(selectinload(User.role))
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with identifier '{payload.email}' was not found."
        )

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact Super Admin."
        )

    # Generate & persist fresh OTP in database in milliseconds
    otp_code, recipient_name = await generate_and_save_login_otp(db, user)

    # Deliver OTP email detached in background
    dispatch_background_email(
        send_login_otp_email(
            to_email=user.email,
            recipient_name=recipient_name,
            otp_code=otp_code,
            expire_minutes=OTP_EXPIRY_MINUTES,
        )
    )

    return LoginInitiateResponse(
        message=f"A fresh verification OTP has been sent to your registered email ({user.email}).",
        email=user.email,
        otp_sent=True,
    )


@router.get("/me", response_model=UserMeResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Retrieves authenticated profile: role_name, first_name, last_name, email, contact_number."""
    return serialize_user_me(current_user)
