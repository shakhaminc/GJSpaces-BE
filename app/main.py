from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import settings
from app.core.database import AsyncSessionLocal, Base, engine
from app.services.user_service import seed_default_roles_and_super_admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initializes database tables and seeds master roles & Super Admin."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        await seed_default_roles_and_super_admin(session)

    yield

    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for GJ Spaces Centralized CRM - Authentication, RBAC, and Workforce Management",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Router directly (no api/v1 prefix)
app.include_router(api_router)


@app.get("/", tags=["Health"])
async def root():
    """Service status and interactive documentation entry point."""
    return {
        "service": settings.PROJECT_NAME,
        "status": "online",
        "documentation": "/docs",
        "version": "1.0.0",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for container and uptime monitors."""
    return {"status": "healthy"}
