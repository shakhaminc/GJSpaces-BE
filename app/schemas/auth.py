import uuid
from typing import Optional
from pydantic import BaseModel, Field

from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    email: str = Field(..., example="admin@gjspaces.com", description="User email or contact number")
    password: str = Field(..., example="password1234")


class TokenResponse(BaseModel):
    message: str = Field("Authentication successful.", example="Authentication successful.")
    access_token: str


class CurrentUser(BaseModel):
    id: uuid.UUID
    email: str
    role_name: str
    status: str
