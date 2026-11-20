import secrets
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.otp import UserOTP
from app.models.user import User
from app.services.email_service import send_login_otp_email


OTP_EXPIRY_MINUTES = 10


def generate_six_digit_otp() -> str:
    """Generates a random 6-digit numeric OTP."""
    return f"{secrets.randbelow(900000) + 100000}"


async def generate_and_save_login_otp(
    db: AsyncSession,
    user: User,
) -> tuple[str, str]:
    """Invalidates older active OTPs, generates a fresh 6-digit OTP, and saves it in database."""
    now = datetime.now(timezone.utc)

    # Invalidate previous unused login OTPs for this user
    await db.execute(
        update(UserOTP)
        .where(
            (UserOTP.user_id == user.id)
            & (UserOTP.purpose == "login")
            & (UserOTP.is_used == False)
        )
        .values(is_used=True)
    )

    otp_code = generate_six_digit_otp()
    expires_at = now + timedelta(minutes=OTP_EXPIRY_MINUTES)

    otp_record = UserOTP(
        id=uuid.uuid4(),
        user_id=user.id,
        otp_code=otp_code,
        purpose="login",
        expires_at=expires_at,
        is_used=False,
    )
    db.add(otp_record)
    await db.commit()

    recipient_name = f"{user.first_name} {user.last_name or ''}".strip()
    return otp_code, recipient_name


async def generate_and_send_login_otp(
    db: AsyncSession,
    user: User,
) -> str:
    """Backward compatible: generates, commits, and sends OTP email immediately."""
    otp_code, recipient_name = await generate_and_save_login_otp(db, user)
    await send_login_otp_email(
        to_email=user.email,
        recipient_name=recipient_name,
        otp_code=otp_code,
        expire_minutes=OTP_EXPIRY_MINUTES,
    )
    return otp_code


async def verify_login_otp(
    db: AsyncSession,
    email: str,
    otp_code: str,
) -> User:
    """Verifies that the provided OTP is valid, unused, and unexpired for the user."""
    # Find active user
    stmt = (
        select(User)
        .where(
            ((User.email == email) | (User.contact_number == email))
            & (User.is_deleted == False)
        )
        .options(selectinload(User.role))
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with identifier '{email}' was not found."
        )

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact Super Admin."
        )

    now = datetime.now(timezone.utc)

    # Find matching unexpired, unused OTP
    otp_stmt = (
        select(UserOTP)
        .where(
            (UserOTP.user_id == user.id)
            & (UserOTP.otp_code == otp_code.strip())
            & (UserOTP.purpose == "login")
            & (UserOTP.is_used == False)
            & (UserOTP.expires_at > now)
        )
        .order_by(UserOTP.created_at.desc())
    )
    otp_result = await db.execute(otp_stmt)
    otp_record = otp_result.scalar_one_or_none()

    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP. Please check the code or request a new one."
        )

    # Mark OTP as used
    otp_record.is_used = True
    await db.commit()

    return user
