import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class MarkPresentRequest(BaseModel):
    to_do: Optional[str] = Field(
        None,
        example="1. Implemented attendance API\n2. Tested authentication endpoints",
        description="Optional daily tasks or to-do list content"
    )
    to_do_list: Optional[str] = Field(
        None,
        example="1. Implemented attendance API\n2. Tested authentication endpoints",
        description="Alias for to_do"
    )

    def get_to_do_content(self) -> Optional[str]:
        return self.to_do or self.to_do_list


class TaskUpdateRequest(BaseModel):
    to_do: Optional[str] = Field(
        None,
        example="1. Implemented attendance API\n2. Tested authentication endpoints",
        description="Daily tasks or to-do list content"
    )
    to_do_list: Optional[str] = Field(
        None,
        example="1. Implemented attendance API\n2. Tested authentication endpoints",
        description="Daily tasks or to-do list content"
    )

    def get_to_do_content(self) -> str:
        content = self.to_do or self.to_do_list
        return content or ""



class AttendanceResponse(BaseModel):
    attendance_id: uuid.UUID
    user_id: uuid.UUID
    login_time: datetime
    logout_time: Optional[datetime] = None
    to_do_list: Optional[str] = None

    class Config:
        from_attributes = True


class AttendanceDetailResponse(BaseModel):
    attendance_id: uuid.UUID
    user_id: uuid.UUID
    employee_name: str
    email: str
    login_time: datetime
    logout_time: Optional[datetime] = None
    to_do_list: Optional[str] = None

    class Config:
        from_attributes = True


class AttendanceLogoutResponse(BaseModel):
    message: str = "Logged out successfully."
    attendance_id: uuid.UUID
    login_time: datetime
    logout_time: datetime
    to_do_list: Optional[str] = None

    class Config:
        from_attributes = True
