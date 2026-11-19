from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.attendance import Attendance


class Role(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    # Relationship to users (One-to-Many)
    users: Mapped[List["User"]] = relationship("User", back_populates="role")


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"

    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    contact_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)

    # Relationship to role (Many-to-One)
    role: Mapped["Role"] = relationship("Role", back_populates="users", lazy="selectin")

    # Relationship to attendances (One-to-Many)
    attendances: Mapped[List["Attendance"]] = relationship(
        "Attendance", back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
