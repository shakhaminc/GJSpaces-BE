from typing import Optional
from pydantic import BaseModel, Field


class LeadConfigItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, example="Instagram", description="Unique name")
    description: Optional[str] = Field(None, max_length=255, example="Leads from Instagram ads", description="Optional description")


class LeadConfigItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100, example="Instagram Ads")
    description: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = Field(None, example=True)


class LeadConfigItemResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_active: bool = True

    class Config:
        from_attributes = True


class LeadConfigDeleteResponse(BaseModel):
    message: str
    id: int
