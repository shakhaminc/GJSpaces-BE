import uuid
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class RoleNameEnum(str, Enum):
    SUPER_ADMIN = "Super Admin"
    MANAGER = "Manager"
    EMPLOYEE = "Employee"


class RoleResponse(BaseModel):
    id: int
    role_name: str
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100, example="Rajesh")
    last_name: Optional[str] = Field(None, max_length=100, example="Kumar")
    email: EmailStr = Field(..., example="rajesh@gjspaces.com")
    contact_number: str = Field(..., min_length=10, max_length=20, example="+919876543210")
    password: str = Field(..., min_length=6, example="SecurePassword123!")
    role_id: int = Field(..., description="Role ID (e.g. 2 for Manager, 3 for Employee)")
    status: str = Field("active", example="active")


class UserResponse(BaseModel):
    id: uuid.UUID
    role_id: int
    role_name: str
    first_name: str
    last_name: Optional[str] = None
    email: EmailStr
    contact_number: str
    status: str
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    class Config:
        from_attributes = True
