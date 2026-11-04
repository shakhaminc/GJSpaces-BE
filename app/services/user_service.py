import uuid
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models.user import Role, User
from app.schemas.user import RoleNameEnum, UserCreate, UserResponse


def serialize_user(user: User) -> UserResponse:
    """Serializes a SQLAlchemy User entity to a UserResponse DTO."""
    role_name = user.role.role_name if user.role else "Unknown"
    return UserResponse(
        id=user.id,
        role_id=user.role_id,
        role_name=role_name,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        contact_number=user.contact_number,
        status=user.status,
        created_at=user.created_at,
        updated_at=user.updated_at,
        is_deleted=user.is_deleted,
    )


async def authenticate_user(
    db: AsyncSession, email_or_contact: str, password: str
) -> Optional[User]:
    """Validates user credentials against email or contact number."""
    stmt = (
        select(User)
        .where(
            ((User.email == email_or_contact) | (User.contact_number == email_or_contact))
            & (User.is_deleted == False)
        )
        .options(selectinload(User.role))
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user


async def create_user_with_role(
    db: AsyncSession, user_in: UserCreate
) -> User:
    """Creates a new user and assigns the selected role."""
    # Check duplicate email or contact number
    dup_stmt = select(User).where(
        ((User.email == user_in.email) | (User.contact_number == user_in.contact_number))
        & (User.is_deleted == False)
    )
    existing_user = (await db.execute(dup_stmt)).scalar_one_or_none()
    if existing_user:
        if existing_user.email == user_in.email:
            detail = f"Email '{user_in.email}' is already registered."
        else:
            detail = f"Contact number '{user_in.contact_number}' is already registered."
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)

    # Validate role_id
    role_stmt = select(Role).where((Role.id == user_in.role_id) & (Role.is_deleted == False))
    role = (await db.execute(role_stmt)).scalar_one_or_none()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role with ID '{user_in.role_id}' does not exist."
        )

    # Prevent secondary Super Admin creation via standard endpoint
    if role.role_name.lower() == RoleNameEnum.SUPER_ADMIN.value.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Secondary Super Admin users cannot be created via this endpoint."
        )

    new_user = User(
        id=uuid.uuid4(),
        role_id=role.id,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        password=get_password_hash(user_in.password),
        email=user_in.email,
        contact_number=user_in.contact_number,
        status=user_in.status,
        is_deleted=False,
    )
    db.add(new_user)
    await db.commit()

    # Reload with role relationship
    stmt = select(User).where(User.id == new_user.id).options(selectinload(User.role))
    result = await db.execute(stmt)
    return result.scalar_one()


async def seed_default_roles_and_super_admin(db: AsyncSession) -> None:
    """Initializes master roles (Super Admin, Manager, Employee) and seeds Super Admin from .env."""
    default_roles = [
        RoleNameEnum.SUPER_ADMIN.value,
        RoleNameEnum.MANAGER.value,
        RoleNameEnum.EMPLOYEE.value,
    ]

    for role_name in default_roles:
        stmt = select(Role).where(Role.role_name == role_name)
        role = (await db.execute(stmt)).scalar_one_or_none()
        if not role:
            role = Role(
                role_name=role_name,
                is_deleted=False
            )
            db.add(role)
    await db.commit()

    # Find Super Admin role
    admin_role_stmt = select(Role).where(Role.role_name == RoleNameEnum.SUPER_ADMIN.value)
    admin_role = (await db.execute(admin_role_stmt)).scalar_one()

    # Seed Super Admin User if doesn't exist
    admin_stmt = select(User).where(User.email == settings.ADMIN_EMAIL)
    admin_user = (await db.execute(admin_stmt)).scalar_one_or_none()

    if not admin_user:
        admin_user = User(
            id=uuid.uuid4(),
            role_id=admin_role.id,
            first_name=settings.ADMIN_FIRST_NAME,
            last_name=settings.ADMIN_LAST_NAME,
            password=get_password_hash(settings.ADMIN_PASSWORD),
            email=settings.ADMIN_EMAIL,
            contact_number=settings.ADMIN_CONTACT_NUMBER,
            status="active",
            is_deleted=False,
        )
        db.add(admin_user)
        await db.commit()
