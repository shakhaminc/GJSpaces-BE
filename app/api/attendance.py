import uuid
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.schemas.attendance import (
    AttendanceDetailResponse,
    AttendanceLogoutResponse,
    AttendanceResponse,
    MarkPresentRequest,
    TaskUpdateRequest,
)
from app.schemas.user import RoleNameEnum
from app.services.attendance_service import (
    get_all_attendances,
    get_today_attendance,
    get_user_attendance_history,
    mark_present,
    record_logout,
    update_daily_tasks,
)

router = APIRouter(prefix="/attendance", tags=["Attendance & Daily Tasks"])


@router.post("/mark-present", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
async def mark_attendance_present(
    payload: Optional[MarkPresentRequest] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Marks attendance as present for today, captures login_time, and optionally accepts initial to_do tasks."""
    to_do_content = payload.get_to_do_content() if payload else None
    attendance = await mark_present(db, current_user.id, to_do_list=to_do_content)
    return attendance


@router.put("/tasks", response_model=AttendanceResponse)
async def update_tasks(
    payload: TaskUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Uploads or updates daily to_do / to_do_list for today's active attendance record."""
    attendance = await update_daily_tasks(db, current_user.id, payload.get_to_do_content())
    return attendance


@router.post("/logout", response_model=AttendanceLogoutResponse)
async def logout_workday(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Clocks out the employee and records the logout_time timestamp for today."""
    result = await record_logout(db, current_user.id)
    return result


@router.get("/today", response_model=AttendanceResponse)
async def view_today_attendance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves the authenticated user's attendance status and to_do_list for today."""
    attendance = await get_today_attendance(db, current_user.id)
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No attendance record found for today. Please mark present first."
        )
    return attendance


@router.get("/my-history", response_model=List[AttendanceResponse])
async def view_my_attendance_history(
    limit: int = Query(30, ge=1, le=100, description="Number of past records to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves the authenticated user's past attendance records."""
    history = await get_user_attendance_history(db, current_user.id, limit=limit)
    return history


@router.get("", response_model=List[AttendanceDetailResponse])
async def list_all_attendance(
    target_date: Optional[date] = Query(None, description="Filter by date (YYYY-MM-DD)"),
    user_id: Optional[uuid.UUID] = Query(None, description="Filter by specific employee UUID"),
    current_user: User = Depends(require_roles([RoleNameEnum.SUPER_ADMIN, RoleNameEnum.MANAGER])),
    db: AsyncSession = Depends(get_db),
):
    """Super Admin & Manager endpoint to view workforce attendance records with employee details."""
    records = await get_all_attendances(db, target_date=target_date, user_id=user_id)
    return records
