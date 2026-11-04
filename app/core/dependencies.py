import uuid
from typing import Callable, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import RoleNameEnum

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Decodes JWT access token and loads current active, non-deleted User with their role."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id_str: str = payload.get("sub")
        token_type: str = payload.get("type")
        if user_id_str is None or token_type != "access":
            raise credentials_exception
        user_id = uuid.UUID(user_id_str)
    except (jwt.PyJWTError, ValueError):
        raise credentials_exception

    stmt = (
        select(User)
        .where((User.id == user_id) & (User.is_deleted == False))
        .options(selectinload(User.role))
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact your Super Admin."
        )

    return user


def require_roles(allowed_roles: List[RoleNameEnum]) -> Callable:
    """Dependency factory that verifies the current user has one of the allowed roles."""
    async def role_checker(
        current_user: User = Depends(get_current_user)
    ) -> User:
        user_role_name = current_user.role.role_name if current_user.role else ""
        allowed_names = [r.value for r in allowed_roles]

        if user_role_name not in allowed_names:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required roles: {allowed_names}"
            )
        return current_user

    return role_checker
