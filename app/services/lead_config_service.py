from datetime import datetime, timezone
from typing import List, Optional, Type, TypeVar
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead_config import LeadCategory, LeadSource, LeadStatus
from app.schemas.lead_config import (
    LeadConfigDeleteResponse,
    LeadConfigItemCreate,
    LeadConfigItemUpdate,
)

T = TypeVar("T", LeadSource, LeadCategory, LeadStatus)


async def list_config_items(
    db: AsyncSession, model_cls: Type[T]
) -> List[T]:
    """Retrieves all non-deleted configuration items ordered by ID."""
    stmt = (
        select(model_cls)
        .where(model_cls.is_deleted == False)
        .order_by(model_cls.id.asc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_config_item_by_id(
    db: AsyncSession, model_cls: Type[T], entity_name: str, item_id: int
) -> T:
    """Retrieves a single configuration item by ID."""
    stmt = select(model_cls).where(
        (model_cls.id == item_id) & (model_cls.is_deleted == False)
    )
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity_name} with ID '{item_id}' was not found."
        )
    return item


async def create_config_item(
    db: AsyncSession,
    model_cls: Type[T],
    entity_name: str,
    payload: LeadConfigItemCreate,
) -> T:
    """Creates a new configuration item with unique name validation."""
    clean_name = payload.name.strip()
    if not clean_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{entity_name} name cannot be empty."
        )

    # Check for existing active or soft-deleted item with the same name (case-insensitive)
    stmt = select(model_cls).where(
        func.lower(model_cls.name) == clean_name.lower()
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        if not existing.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"{entity_name} '{clean_name}' already exists."
            )
        # Revive soft-deleted record
        existing.is_deleted = False
        existing.deleted_at = None
        existing.is_active = True
        existing.name = clean_name
        existing.description = payload.description.strip() if payload.description else None
        await db.commit()
        await db.refresh(existing)
        return existing

    clean_desc = payload.description.strip() if payload.description else None
    new_item = model_cls(
        name=clean_name,
        description=clean_desc,
        is_active=True,
    )
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    return new_item


async def update_config_item(
    db: AsyncSession,
    model_cls: Type[T],
    entity_name: str,
    item_id: int,
    payload: LeadConfigItemUpdate,
) -> T:
    """Updates an existing configuration item."""
    item = await get_config_item_by_id(db, model_cls, entity_name, item_id)

    if payload.name is not None:
        clean_name = payload.name.strip()
        if not clean_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{entity_name} name cannot be empty."
            )
        # Check duplicate name on another active item
        dup_stmt = select(model_cls).where(
            (func.lower(model_cls.name) == clean_name.lower())
            & (model_cls.id != item_id)
            & (model_cls.is_deleted == False)
        )
        existing = (await db.execute(dup_stmt)).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"{entity_name} with name '{clean_name}' already exists."
            )
        item.name = clean_name

    if payload.description is not None:
        item.description = payload.description.strip() if payload.description else None

    if payload.is_active is not None:
        item.is_active = payload.is_active

    await db.commit()
    await db.refresh(item)
    return item


async def delete_config_item(
    db: AsyncSession,
    model_cls: Type[T],
    entity_name: str,
    item_id: int,
) -> LeadConfigDeleteResponse:
    """Soft deletes a configuration item."""
    item = await get_config_item_by_id(db, model_cls, entity_name, item_id)
    item.is_deleted = True
    item.deleted_at = datetime.now(timezone.utc)
    item.is_active = False
    await db.commit()

    return LeadConfigDeleteResponse(
        message=f"{entity_name} '{item.name}' deleted successfully.",
        id=item_id,
    )


async def seed_default_lead_configs(db: AsyncSession) -> None:
    """Seeds baseline lead sources, categories, and statuses if empty."""
    default_sources = [
        ("Instagram", "Leads from Instagram ads & page"),
        ("Website", "Organic form inquiries from company website"),
        ("Justdial", "Inquiries from Justdial listings"),
        ("Facebook", "Leads from Facebook ad campaigns"),
        ("Referral", "Word-of-mouth or customer referral"),
        ("Direct Walk-in", "Walk-in inquiries at project office"),
    ]

    default_categories = [
        ("Hot", "High purchase intent, immediate follow-up required"),
        ("Warm", "Interested buyer evaluating options"),
        ("Cold", "Low engagement or future prospect"),
    ]

    default_statuses = [
        ("New Lead", "Newly created lead, not contacted yet"),
        ("Contacted", "First call/message delivered to lead"),
        ("Follow-up", "Follow-up conversation in progress"),
        ("Site Visit Scheduled", "Appointment booked for property tour"),
        ("Site Visit Completed", "Client attended property walkthrough"),
        ("Negotiation", "Price or terms negotiation underway"),
        ("Closed Won", "Booking finalized and deal closed"),
        ("Lost", "Lead dropped or opted out"),
    ]

    # Seed Sources
    for name, desc in default_sources:
        stmt = select(LeadSource).where(LeadSource.name == name)
        if not (await db.execute(stmt)).scalar_one_or_none():
            db.add(LeadSource(name=name, description=desc, is_active=True))

    # Seed Categories
    for name, desc in default_categories:
        stmt = select(LeadCategory).where(LeadCategory.name == name)
        if not (await db.execute(stmt)).scalar_one_or_none():
            db.add(LeadCategory(name=name, description=desc, is_active=True))

    # Seed Statuses
    for name, desc in default_statuses:
        stmt = select(LeadStatus).where(LeadStatus.name == name)
        if not (await db.execute(stmt)).scalar_one_or_none():
            db.add(LeadStatus(name=name, description=desc, is_active=True))

    await db.commit()
