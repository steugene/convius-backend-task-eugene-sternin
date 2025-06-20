import secrets
from typing import Any, List, Optional, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore", case_sensitive=True
    )

    # Project Configuration
    PROJECT_NAME: str = "Lunch Voting API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = False
    ENABLE_DOCS: bool = True  # Enable API documentation (Swagger/Redoc)

    # CORS Configuration
    BACKEND_CORS_ORIGINS: Union[List[str], str] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json

                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [str(item) for item in parsed]
                except json.JSONDecodeError:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return [str(item) for item in v]
        return []

    # Database Configuration
    # Support both Railway and standard environment variables
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None

    @field_validator("POSTGRES_SERVER", mode="before")
    @classmethod
    def validate_postgres_server(cls, v: Any) -> str:
        # Railway provides POSTGRES_HOST, fallback to POSTGRES_SERVER
        import os

        railway_host = os.getenv("POSTGRES_HOST")
        if railway_host:
            return railway_host
        if v is None or v == "" or v == {}:
            return "localhost"
        return str(v)

    @field_validator("POSTGRES_PORT", mode="before")
    @classmethod
    def validate_postgres_port(cls, v: Any) -> int:
        # Railway provides POSTGRES_PORT
        import os

        railway_port = os.getenv("POSTGRES_PORT")
        if railway_port:
            return int(railway_port)
        if v is None or v == "" or v == {}:
            return 5432
        return int(v)

    @field_validator("POSTGRES_USER", mode="before")
    @classmethod
    def validate_postgres_user(cls, v: Any) -> str:
        # Railway provides POSTGRES_USER
        import os

        railway_user = os.getenv("POSTGRES_USER")
        if railway_user:
            return railway_user
        if v is None or v == "" or v == {}:
            return "postgres"
        return str(v)

    @field_validator("POSTGRES_PASSWORD", mode="before")
    @classmethod
    def validate_postgres_password(cls, v: Any) -> str:
        # Railway provides POSTGRES_PASSWORD
        import os

        railway_password = os.getenv("POSTGRES_PASSWORD")
        if railway_password:
            return railway_password
        if v is None or v == "" or v == {}:
            return "postgres"
        return str(v)

    @field_validator("POSTGRES_DB", mode="before")
    @classmethod
    def validate_postgres_db(cls, v: Any) -> str:
        # Railway provides POSTGRES_DB, also try PGDATABASE
        import os

        railway_db = os.getenv("POSTGRES_DB") or os.getenv("PGDATABASE")
        if railway_db:
            return railway_db
        if v is None or v == "" or v == {}:
            return "lunch_voting"
        return str(v)

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        import os

        database_url = os.getenv("DATABASE_URL")
        if database_url:
            # Railway sometimes provides postgres:// instead of postgresql://
            if database_url.startswith("postgres://"):
                database_url = database_url.replace("postgres://", "postgresql://", 1)
            return database_url

        # Fallback to individual components
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"  # noqa: E231
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/"  # noqa: E231
            f"{self.POSTGRES_DB}"
        )

    # Security Configuration
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Rate Limiting
    REQUESTS_PER_MINUTE: int = 60

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "app.log"

    # Health Check Configuration
    HEALTH_CHECK_TIMEOUT: int = 30

    @field_validator("SECRET_KEY", mode="before")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        # Check environment variable first (Railway/production provides SECRET_KEY)
        import os

        env_secret = os.getenv("SECRET_KEY")
        if env_secret:
            return env_secret

        # If no env var and in production, generate a secure key
        environment = os.getenv("ENVIRONMENT", "development")
        if environment == "production" and (
            not v or v == "dev-secret-key-change-in-production"
        ):
            return secrets.token_urlsafe(32)

        # For development/testing, allow the default key for stability
        return v or "dev-secret-key-change-in-production"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        if self.ENVIRONMENT == "production":
            if self.POSTGRES_PASSWORD == "postgres":
                import warnings

                warnings.warn(
                    "Using default database password in production!", UserWarning
                )


settings = Settings()
