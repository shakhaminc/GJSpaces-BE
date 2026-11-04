import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.user import Role, User
from app.schemas.common import ResponseEnvelope
from app.schemas.user import RoleNameEnum, RoleResponse, UserCreate, UserResponse
from app.services.user_service import create_user_with_role, serialize_user

router = APIRouter(prefix="/users", tags=["Workforce & User Administration"])


@router.get("/roles", response_model=ResponseEnvelope[List[RoleResponse]])
async def list_roles(
    current_user: User = Depends(require_roles([RoleNameEnum.SUPER_ADMIN, RoleNameEnum.MANAGER])),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves available master roles."""
    stmt = select(Role).where(Role.is_deleted == False).order_by(Role.id)
    result = await db.execute(stmt)
    roles = result.scalars().all()
    return ResponseEnvelope(
        data=[RoleResponse.model_validate(r) for r in roles]
    )


@router.post("", response_model=ResponseEnvelope[UserResponse], status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    current_user: User = Depends(require_roles([RoleNameEnum.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Super Admin endpoint to create new Managers and Employees."""
    new_user = await create_user_with_role(db, user_in)
    return ResponseEnvelope(
        statusCode=201,
        message=f"{new_user.role.role_name} '{new_user.first_name} {new_user.last_name or ''}' created successfully.",
        data=serialize_user(new_user)
    )


@router.get("", response_model=ResponseEnvelope[List[UserResponse]])
async def list_users(
    role_id: Optional[int] = Query(None, description="Filter users by role_id"),
    status: Optional[str] = Query(None, description="Filter by status (active, inactive)"),
    current_user: User = Depends(require_roles([RoleNameEnum.SUPER_ADMIN, RoleNameEnum.MANAGER])),
    db: AsyncSession = Depends(get_db),
):
    """Lists workforce users. Super Admin and Managers can view employee and manager records."""
    stmt = (
        select(User)
        .where(User.is_deleted == False)
        .options(selectinload(User.role))
        .order_by(User.created_at.desc())
    )

    if role_id is not None:
        stmt = stmt.where(User.role_id == role_id)
    if status is not None:
        stmt = stmt.where(User.status == status)

    result = await db.execute(stmt)
    users = result.scalars().all()

    return ResponseEnvelope(
        data=[serialize_user(u) for u in users]
    )


@router.get("/{user_id}", response_model=ResponseEnvelope[UserResponse])
async def get_user_by_id(
    user_id: uuid.UUID,
    current_user: User = Depends(require_roles([RoleNameEnum.SUPER_ADMIN, RoleNameEnum.MANAGER])),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves user profile and assigned role."""
    stmt = (
        select(User)
        .where((User.id == user_id) & (User.is_deleted == False))
        .options(selectinload(User.role))
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' was not found."
        )

    return ResponseEnvelope(
        data=serialize_user(user)
    )


@router.delete("/{user_id}", response_model=ResponseEnvelope[dict])
async def delete_user(
    user_id: uuid.UUID,
    current_user: User = Depends(require_roles([RoleNameEnum.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Soft deletes a user record (marks is_deleted=True and records deleted_at). Super Admin only."""
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Super Admin cannot delete their own account."
        )

    stmt = select(User).where((User.id == user_id) & (User.is_deleted == False))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' was not found or already deleted."
        )

    user.is_deleted = True
    user.deleted_at = datetime.now(timezone.utc)
    user.status = "inactive"
    await db.commit()

    return ResponseEnvelope(
        message=f"User '{user.first_name} {user.last_name or ''}' has been soft-deleted successfully.",
        data={"user_id": str(user_id), "is_deleted": True}
    )
