import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.user import User
from app.schemas.form import (
    FormCreate,
    FormDetailResponse,
    FormFieldCreate,
    FormFieldReorderRequest,
    FormFieldResponse,
    FormFieldUpdate,
    FormResponse,
    FormUpdate,
)
from app.schemas.user import RoleNameEnum
from app.services.form_service import (
    add_field_to_form,
    create_form,
    delete_field,
    delete_form,
    get_form_by_id,
    list_forms,
    reorder_fields,
    update_field,
    update_form,
)

router = APIRouter(prefix="/forms", tags=["Configurable Forms"])


# ==============================================================================
# Form Operations
# ==============================================================================

@router.post("", response_model=FormResponse, status_code=status.HTTP_201_CREATED)
async def create_new_form(
    form_in: FormCreate,
    current_user: User = Depends(require_roles([RoleNameEnum.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Super Admin endpoint to create a new form definition."""
    form = await create_form(db, form_in)
    return FormResponse(
        id=form.id,
        form_title=form.form_title,
        description=form.description,
        is_active=form.is_active,
        field_count=0,
        created_at=form.created_at,
        updated_at=form.updated_at,
    )


@router.get("", response_model=List[FormResponse])
async def get_all_forms(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(require_roles([RoleNameEnum.SUPER_ADMIN, RoleNameEnum.MANAGER, RoleNameEnum.EMPLOYEE])),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves all forms with their respective active field counts."""
    forms_data = await list_forms(db, is_active=is_active)
    return [FormResponse(**f) for f in forms_data]


@router.get("/{form_id}", response_model=FormDetailResponse)
async def get_form_details(
    form_id: uuid.UUID,
    current_user: User = Depends(require_roles([RoleNameEnum.SUPER_ADMIN, RoleNameEnum.MANAGER, RoleNameEnum.EMPLOYEE])),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves full form structure with all its ordered fields."""
    form = await get_form_by_id(db, form_id)
    fields = [FormFieldResponse.model_validate(fld) for fld in form.fields]
    active_field_count = len([f for f in fields if f.is_active])

    return FormDetailResponse(
        id=form.id,
        form_title=form.form_title,
        description=form.description,
        is_active=form.is_active,
        field_count=active_field_count,
        created_at=form.created_at,
        updated_at=form.updated_at,
        fields=fields,
    )


@router.put("/{form_id}", response_model=FormResponse)
async def update_form_metadata(
    form_id: uuid.UUID,
    form_in: FormUpdate,
    current_user: User = Depends(require_roles([RoleNameEnum.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Super Admin endpoint to update form title, description, or is_active toggle."""
    form = await update_form(db, form_id, form_in)
    active_field_count = len([fld for fld in form.fields if not fld.is_deleted and fld.is_active])

    return FormResponse(
        id=form.id,
        form_title=form.form_title,
        description=form.description,
        is_active=form.is_active,
        field_count=active_field_count,
        created_at=form.created_at,
        updated_at=form.updated_at,
    )


@router.delete("/{form_id}", status_code=status.HTTP_200_OK)
async def delete_form_endpoint(
    form_id: uuid.UUID,
    current_user: User = Depends(require_roles([RoleNameEnum.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Super Admin endpoint to soft-delete a form and its fields."""
    await delete_form(db, form_id)
    return {
        "status": "success",
        "message": f"Form '{form_id}' and all its fields have been soft-deleted successfully.",
    }


# ==============================================================================
# Field Operations
# ==============================================================================

@router.post("/{form_id}/fields", response_model=FormFieldResponse, status_code=status.HTTP_201_CREATED)
async def add_new_field(
    form_id: uuid.UUID,
    field_in: FormFieldCreate,
    current_user: User = Depends(require_roles([RoleNameEnum.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Super Admin endpoint to add a new field to a form."""
    field = await add_field_to_form(db, form_id, field_in)
    return FormFieldResponse.model_validate(field)


@router.put("/fields/{field_id}", response_model=FormFieldResponse)
async def update_existing_field(
    field_id: uuid.UUID,
    field_in: FormFieldUpdate,
    current_user: User = Depends(require_roles([RoleNameEnum.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Super Admin endpoint to update field properties (name, type, options, required, order, active)."""
    field = await update_field(db, field_id, field_in)
    return FormFieldResponse.model_validate(field)


@router.delete("/fields/{field_id}", status_code=status.HTTP_200_OK)
async def delete_existing_field(
    field_id: uuid.UUID,
    current_user: User = Depends(require_roles([RoleNameEnum.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Super Admin endpoint to soft-delete a field."""
    await delete_field(db, field_id)
    return {
        "status": "success",
        "message": f"Field '{field_id}' has been soft-deleted successfully.",
    }


@router.put("/{form_id}/reorder-fields", response_model=List[FormFieldResponse])
async def reorder_form_fields(
    form_id: uuid.UUID,
    payload: FormFieldReorderRequest,
    current_user: User = Depends(require_roles([RoleNameEnum.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Super Admin endpoint to bulk update display orders for fields within a form."""
    reordered_fields = await reorder_fields(db, form_id, payload.orders)
    return [FormFieldResponse.model_validate(f) for f in reordered_fields]
