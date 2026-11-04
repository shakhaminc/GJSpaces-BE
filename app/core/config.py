from typing import Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings strictly populated from the .env file."""
    # Application Info (required in .env)
    PROJECT_NAME: str
    BASE_URL: str
    ENVIRONMENT: str
    DEBUG: bool

    # Database (required in .env)
    DATABASE_URL: str

    @field_validator("DATABASE_URL", mode="before")
    def assemble_db_connection(cls, v: str) -> str:
        if isinstance(v, str):
            # Adapt standard postgresql:// to asyncpg driver if needed
            if v.startswith("postgresql://"):
                return v.replace("postgresql://", "postgresql+asyncpg://", 1)
            elif v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql+asyncpg://", 1)
        return v

    # SMTP Email Configuration (optional in .env)
    SMTP_SERVER: Optional[str] = None
    SMTP_PORT: Optional[int] = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    FROM_EMAIL: Optional[str] = None
    TO_EMAIL: Optional[str] = None
    FROM_NAME: Optional[str] = None

    # Security & JWT (required in .env)
    JWT_SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # Default Super Admin Credentials (required in .env)
    ADMIN_EMAIL: str
    ADMIN_PASSWORD: str
    ADMIN_FIRST_NAME: str = "Super"
    ADMIN_LAST_NAME: Optional[str] = "Admin"
    ADMIN_CONTACT_NUMBER: str = "+910000000000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
