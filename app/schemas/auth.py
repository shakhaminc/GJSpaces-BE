import uuid
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    email: str = Field(..., example="admin@gjspaces.com", description="User email or contact number")
    password: str = Field(..., example="password1234")


class LoginInitiateResponse(BaseModel):
    message: str = "OTP has been sent to your registered email address."
    email: str
    otp_sent: bool = True


class VerifyOTPRequest(BaseModel):
    email: str = Field(..., example="admin@gjspaces.com", description="User email or contact number")
    otp: str = Field(..., min_length=6, max_length=6, example="123456", description="6-digit verification code")


class ResendOTPRequest(BaseModel):
    email: str = Field(..., example="admin@gjspaces.com", description="User email or contact number")


class TokenResponse(BaseModel):
    message: str = Field("Authentication successful.", example="Authentication successful.")
    access_token: str
    token_type: str = "bearer"
    role_name: Optional[str] = None
    email: Optional[str] = None


class CurrentUser(BaseModel):
    id: uuid.UUID
    email: str
    role_name: str
    status: str

