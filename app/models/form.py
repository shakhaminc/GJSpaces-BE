import uuid
from typing import Any, List, Optional
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Form(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Represents a configurable form definition (e.g. Lead Format, Project Form)."""
    __tablename__ = "forms"

    form_title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    # Relationship to fields
    fields: Mapped[List["FormField"]] = relationship(
        "FormField",
        back_populates="form",
        cascade="all, delete-orphan",
        order_by="FormField.display_order",
        lazy="selectin"
    )


class FormField(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Individual configurable field within a form."""
    __tablename__ = "form_fields"

    form_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("forms.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    field_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    field_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )  # text, textarea, number, select, multiselect, radio, date, boolean, phone, email
    is_required: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    options: Mapped[Optional[Any]] = mapped_column(
        JSONB,
        nullable=True
    )  # list of strings e.g. ["1 BHK", "2 BHK"] or [{"label": ..., "value": ...}]
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    # Relationship to form
    form: Mapped["Form"] = relationship(
        "Form",
        back_populates="fields"
    )

