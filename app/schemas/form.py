import uuid
from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ----------------------------------------------------
# Form Field Schemas
# ----------------------------------------------------

class FormFieldBase(BaseModel):
    field_name: str = Field(..., example="Customer Contact No.", description="Name or label of the field")
    field_type: str = Field(..., example="text", description="Field type: text, textarea, number, select, multiselect, radio, date, boolean, phone, email")
    is_required: bool = Field(False, description="Whether this field is mandatory")
    display_order: int = Field(0, description="Display order sequence")
    options: Optional[List[Any]] = Field(None, example=["1 BHK", "2 BHK", "3 BHK"], description="List of options for select, multiselect, or radio fields")
    is_active: bool = Field(True, description="Whether this field is active")


class FormFieldCreate(FormFieldBase):
    pass


class FormFieldUpdate(BaseModel):
    field_name: Optional[str] = Field(None, example="Updated Field Name")
    field_type: Optional[str] = Field(None, example="select")
    is_required: Optional[bool] = Field(None)
    display_order: Optional[int] = Field(None)
    options: Optional[List[Any]] = Field(None)
    is_active: Optional[bool] = Field(None)


class FormFieldResponse(FormFieldBase):
    id: uuid.UUID
    form_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FormFieldReorderItem(BaseModel):
    field_id: uuid.UUID
    display_order: int


class FormFieldReorderRequest(BaseModel):
    orders: List[FormFieldReorderItem] = Field(..., description="List of field IDs and their new display_order")


# ----------------------------------------------------
# Form Schemas
# ----------------------------------------------------

class FormBase(BaseModel):
    form_title: str = Field(..., example="Lead Format", description="Title of the form")
    description: Optional[str] = Field(None, example="Form for capturing new buyer leads", description="Description or instructions for the form")
    is_active: bool = Field(True, description="Whether the form is active")


class FormCreate(FormBase):
    pass


class FormUpdate(BaseModel):
    form_title: Optional[str] = Field(None, example="Updated Form Title")
    description: Optional[str] = Field(None)
    is_active: Optional[bool] = Field(None)


class FormResponse(FormBase):
    id: uuid.UUID
    field_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FormDetailResponse(FormResponse):
    fields: List[FormFieldResponse] = []
