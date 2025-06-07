import secrets
from typing import List, Union, Any, Optional
from pydantic import field_validator, ConfigDict, computed_field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
        case_sensitive=True
    )
    
    # Project Configuration
    PROJECT_NAME: str = "Lunch Voting API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = False
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return []

    # Database Configuration
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None

    @field_validator("POSTGRES_USER", mode="before")
    @classmethod
    def validate_postgres_user(cls, v: Any) -> str:
        if v is None or v == "" or v == {}:
            return "postgres"
        return str(v)

    @field_validator("POSTGRES_PASSWORD", mode="before")
    @classmethod
    def validate_postgres_password(cls, v: Any) -> str:
        if v is None or v == "" or v == {}:
            return "postgres"
        return str(v)

    @field_validator("POSTGRES_DB", mode="before")
    @classmethod
    def validate_postgres_db(cls, v: Any) -> str:
        if v is None or v == "" or v == {}:
            return "lunch_voting"
        return str(v)

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Security Configuration
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Rate Limiting
    REQUESTS_PER_MINUTE: int = 60
    
    # Voting Configuration
    VOTES_PER_DAY: int = 3
    VOTE_WEIGHTS: List[float] = [1.0, 0.5, 0.25]
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "app.log"
    
    # Health Check Configuration
    HEALTH_CHECK_TIMEOUT: int = 30
    
    @field_validator("SECRET_KEY", mode="before")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if not v or v == "your-secret-key-here":
            return secrets.token_urlsafe(32)
        return v

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Validate production configuration
        if self.ENVIRONMENT == "production":
            if self.POSTGRES_PASSWORD == "postgres":
                raise ValueError("Default database password not allowed in production! Set POSTGRES_PASSWORD environment variable.")
            if self.SECRET_KEY == "dev-secret-key-change-in-production":
                raise ValueError("Default SECRET_KEY not allowed in production! Set SECRET_KEY environment variable.")

settings = Settings() 