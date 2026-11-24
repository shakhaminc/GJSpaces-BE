import uuid
from datetime import date, datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.attendance import Attendance
from app.models.user import User
from app.schemas.attendance import (
    AttendanceDetailResponse,
    AttendanceLogoutResponse,
    AttendanceResponse,
)


def _get_day_bounds() -> tuple[datetime, datetime]:
    """Returns the start and end datetime for the current local calendar day.
    Uses the server/local timezone to correctly match the employee's workday.
    """
    now_local = datetime.now().astimezone()
    start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    end_local = now_local.replace(hour=23, minute=59, second=59, microsecond=999999)
    return start_local, end_local


async def get_today_attendance(
    db: AsyncSession, user_id: uuid.UUID
) -> Optional[Attendance]:
    """Retrieves today's attendance record for the given user, if any."""
    start_of_day, end_of_day = _get_day_bounds()
    stmt = (
        select(Attendance)
        .where(
            (Attendance.user_id == user_id)
            & (Attendance.login_time >= start_of_day)
            & (Attendance.login_time <= end_of_day)
        )
        .order_by(Attendance.login_time.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().first()


async def mark_present(
    db: AsyncSession, user_id: uuid.UUID, to_do_list: Optional[str] = None
) -> Attendance:
    """Marks attendance as present for today. Strictly allowed ONCE per day.
    Cannot be marked again once already checked in or after check-out.
    """
    existing = await get_today_attendance(db, user_id)
    if existing:
        # Edge Case 1: Already checked out today
        if existing.logout_time is not None:
            formatted_logout = existing.logout_time.strftime("%H:%M:%S")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You have already checked out for today at {formatted_logout}. Cannot mark attendance again today."
            )

        # Edge Case 2: Already marked present today
        formatted_login = existing.login_time.strftime("%H:%M:%S")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Attendance already marked present for today at {formatted_login}. Attendance can only be marked once per day."
        )

    now = datetime.now(timezone.utc)
    clean_to_do = to_do_list.strip() if to_do_list and to_do_list.strip() else None

    new_attendance = Attendance(
        attendance_id=uuid.uuid4(),
        user_id=user_id,
        login_time=now,
        logout_time=None,
        to_do_list=clean_to_do,
    )
    db.add(new_attendance)
    await db.commit()
    await db.refresh(new_attendance)
    return new_attendance


async def update_daily_tasks(
    db: AsyncSession, user_id: uuid.UUID, to_do_list: str
) -> Attendance:
    """Updates the to_do_list for today's active attendance record."""
    clean_tasks = to_do_list.strip() if to_do_list else ""
    if not clean_tasks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task content cannot be empty."
        )

    attendance = await get_today_attendance(db, user_id)
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No attendance record found for today. Please mark present first."
        )

    # Edge Case 3: Cannot update tasks after check-out
    if attendance.logout_time is not None:
        formatted_logout = attendance.logout_time.strftime("%H:%M:%S")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update tasks after check-out. You have already logged out today at {formatted_logout}."
        )

    attendance.to_do_list = clean_tasks
    await db.commit()
    await db.refresh(attendance)
    return attendance


async def record_logout(
    db: AsyncSession, user_id: uuid.UUID
) -> AttendanceLogoutResponse:
    """Records logout_time for today's attendance record."""
    attendance = await get_today_attendance(db, user_id)
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No attendance record found for today. You must mark present before checking out."
        )

    # Edge Case 4: Cannot check out multiple times
    if attendance.logout_time is not None:
        formatted_time = attendance.logout_time.strftime("%H:%M:%S")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Already logged out today at {formatted_time}. You cannot check out multiple times."
        )

    now = datetime.now(timezone.utc)
    attendance.logout_time = now
    await db.commit()
    await db.refresh(attendance)

    return AttendanceLogoutResponse(
        message="Logged out successfully.",
        attendance_id=attendance.attendance_id,
        login_time=attendance.login_time,
        logout_time=attendance.logout_time,
        to_do_list=attendance.to_do_list,
    )


async def get_user_attendance_history(
    db: AsyncSession, user_id: uuid.UUID, limit: int = 30
) -> List[Attendance]:
    """Retrieves an employee's historical attendance records."""
    stmt = (
        select(Attendance)
        .where(Attendance.user_id == user_id)
        .order_by(Attendance.login_time.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_all_attendances(
    db: AsyncSession,
    target_date: Optional[date] = None,
    user_id: Optional[uuid.UUID] = None,
) -> List[AttendanceDetailResponse]:
    """Super Admin & Manager endpoint to view all workforce attendance."""
    stmt = (
        select(Attendance)
        .options(selectinload(Attendance.user))
        .order_by(Attendance.login_time.desc())
    )

    if user_id is not None:
        stmt = stmt.where(Attendance.user_id == user_id)

    if target_date is not None:
        stmt = stmt.where(func.date(Attendance.login_time) == target_date)

    result = await db.execute(stmt)
    records = result.scalars().all()

    response: List[AttendanceDetailResponse] = []
    for att in records:
        emp_name = "Unknown"
        email = "Unknown"
        if att.user:
            emp_name = f"{att.user.first_name} {att.user.last_name or ''}".strip()
            email = att.user.email

        response.append(
            AttendanceDetailResponse(
                attendance_id=att.attendance_id,
                user_id=att.user_id,
                employee_name=emp_name,
                email=email,
                login_time=att.login_time,
                logout_time=att.logout_time,
                to_do_list=att.to_do_list,
            )
        )

    return response
