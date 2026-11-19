from fastapi import APIRouter

from app.api import attendance, auth, lead_config, users
from app.api.auth import get_current_user_profile
from app.schemas.user import UserMeResponse

api_router = APIRouter()

# Support both /auth/me and /me
api_router.add_api_route(
    "/me",
    get_current_user_profile,
    methods=["GET"],
    tags=["Authentication & Session"],
    response_model=UserMeResponse,
    summary="Get current user profile (alias of /auth/me)",
)

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(attendance.router)
api_router.include_router(lead_config.router)

__all__ = ["api_router"]
