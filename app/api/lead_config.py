from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.lead_config import LeadCategory, LeadSource, LeadStatus
from app.models.user import User
from app.schemas.lead_config import (
    LeadConfigDeleteResponse,
    LeadConfigItemCreate,
    LeadConfigItemResponse,
    LeadConfigItemUpdate,
)
from app.schemas.user import RoleNameEnum
from app.services.lead_config_service import (
    create_config_item,
    delete_config_item,
    list_config_items,
    update_config_item,
)

router = APIRouter(
    tags=["Lead Master Configuration"],
    dependencies=[Depends(require_roles([RoleNameEnum.SUPER_ADMIN]))],
)


# ---------------------------------------------------------------------------
# 1. Lead Sources (/lead-sources)
# ---------------------------------------------------------------------------

@router.post(
    "/lead-sources",
    response_model=LeadConfigItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new lead source (Super Admin only)",
)
async def create_lead_source(
    payload: LeadConfigItemCreate,
    current_user: User = Depends(require_roles([RoleNameEnum.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Adds a new lead source (e.g. Instagram, Website, Justdial)."""
    return await create_config_item(db, LeadSource, "Lead Source", payload)


@router.get(
    "/lead-sources",
    response_model=List[LeadConfigItemResponse],
    summary="List all active lead sources (Super Admin only)",
)
async def list_lead_sources(
    current_user: User = Depends(require_roles([RoleNameEnum.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves all active lead sources."""
    return await list_config_items(db, LeadSource)


@router.put(
    "/lead-sources/{id}",
    response_model=LeadConfigItemResponse,
    summary="Update a lead source (Super Admin only)",
)
async def update_lead_source(
    id: int,
    payload: LeadConfigItemUpdate,
    current_user: User = Depends(require_roles([RoleNameEnum.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Updates the name, description, or active status of a lead source."""
    return await update_config_item(db, LeadSource, "Lead Source", id, payload)


@router.delete(
    "/lead-sources/{id}",
    response_model=LeadConfigDeleteResponse,
    summary="Delete a lead source (Super Admin only)",
)
async def delete_lead_source(
    id: int,
    current_user: User = Depends(require_roles([RoleNameEnum.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Soft deletes a lead source."""
    return await delete_config_item(db, LeadSource, "Lead Source", id)


# ---------------------------------------------------------------------------
# 2. Lead Categories (/lead-categories)
# ---------------------------------------------------------------------------

@router.post(
    "/lead-categories",
    response_model=LeadConfigItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new lead category (Super Admin only)",
)
async def create_lead_category(
    payload: LeadConfigItemCreate,
    current_user: User = Depends(require_roles([RoleNameEnum.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Adds a new lead category (e.g. Hot, Warm, Cold)."""
    return await create_config_item(db, LeadCategory, "Lead Category", payload)


@router.get(
    "/lead-categories",
    response_model=List[LeadConfigItemResponse],
    summary="List all active lead categories (Super Admin only)",
)
async def list_lead_categories(
    current_user: User = Depends(require_roles([RoleNameEnum.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves all active lead categories."""
    return await list_config_items(db, LeadCategory)


@router.put(
    "/lead-categories/{id}",
    response_model=LeadConfigItemResponse,
    summary="Update a lead category (Super Admin only)",
)
async def update_lead_category(
    id: int,
    payload: LeadConfigItemUpdate,
    current_user: User = Depends(require_roles([RoleNameEnum.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Updates the name, description, or active status of a lead category."""
    return await update_config_item(db, LeadCategory, "Lead Category", id, payload)


@router.delete(
    "/lead-categories/{id}",
    response_model=LeadConfigDeleteResponse,
    summary="Delete a lead category (Super Admin only)",
)
async def delete_lead_category(
    id: int,
    current_user: User = Depends(require_roles([RoleNameEnum.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Soft deletes a lead category."""
    return await delete_config_item(db, LeadCategory, "Lead Category", id)


# ---------------------------------------------------------------------------
# 3. Lead Statuses (/lead-statuses)
# ---------------------------------------------------------------------------

@router.post(
    "/lead-statuses",
    response_model=LeadConfigItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new lead status (Super Admin only)",
)
async def create_lead_status(
    payload: LeadConfigItemCreate,
    current_user: User = Depends(require_roles([RoleNameEnum.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Adds a new lead status (e.g. Contacted, Visit Completed)."""
    return await create_config_item(db, LeadStatus, "Lead Status", payload)


@router.get(
    "/lead-statuses",
    response_model=List[LeadConfigItemResponse],
    summary="List all active lead statuses (Super Admin only)",
)
async def list_lead_statuses(
    current_user: User = Depends(require_roles([RoleNameEnum.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves all active lead statuses."""
    return await list_config_items(db, LeadStatus)


@router.put(
    "/lead-statuses/{id}",
    response_model=LeadConfigItemResponse,
    summary="Update a lead status (Super Admin only)",
)
async def update_lead_status(
    id: int,
    payload: LeadConfigItemUpdate,
    current_user: User = Depends(require_roles([RoleNameEnum.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Updates the name, description, or active status of a lead status."""
    return await update_config_item(db, LeadStatus, "Lead Status", id, payload)


@router.delete(
    "/lead-statuses/{id}",
    response_model=LeadConfigDeleteResponse,
    summary="Delete a lead status (Super Admin only)",
)
async def delete_lead_status(
    id: int,
    current_user: User = Depends(require_roles([RoleNameEnum.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Soft deletes a lead status."""
    return await delete_config_item(db, LeadStatus, "Lead Status", id)
