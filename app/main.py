from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import uvicorn

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.middleware import (
    ErrorHandlerMiddleware,
    RequestTrackingMiddleware, 
    SecurityHeadersMiddleware
)
from app.core.rate_limiter import limiter, custom_rate_limit_handler

# Initialize logging
setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Production-ready REST API for lunch voting system",
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DEBUG else None,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)

# Add middleware (order matters - first added is outermost)
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestTrackingMiddleware)

# Security middleware for production
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure with your actual domains in production
    )

# CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Root endpoint for load balancer health checks
@app.get("/")
async def root():
    """Root endpoint for basic health check."""
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "running",
        "environment": settings.ENVIRONMENT
    }

@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info(f"🚀 Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    logger.info(f"🌍 Environment: {settings.ENVIRONMENT}")
    logger.info(f"🔧 Debug mode: {settings.DEBUG}")
    logger.info(f"📊 API Documentation: {'/docs' if settings.DEBUG else 'disabled'}")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info(f"🛑 Shutting down {settings.PROJECT_NAME}")

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
    ) 