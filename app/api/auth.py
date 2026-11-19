from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserMeResponse
from app.services.user_service import authenticate_user, serialize_user_me

router = APIRouter(prefix="/auth", tags=["Authentication & Session"])


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Authenticates credentials using email/contact and password, returns signed JWT access token."""
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

    access_token = create_access_token(subject=user.id)

    return TokenResponse(
        message="Authentication successful.",
        access_token=access_token
    )


@router.get("/me", response_model=UserMeResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Retrieves authenticated profile: role_name, first_name, last_name, email, contact_number."""
    return serialize_user_me(current_user)
