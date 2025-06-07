from typing import Optional, Dict, Any
from fastapi import Request, HTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_client_id(request: Request) -> str:
    """
    Get client identifier for rate limiting.
    Uses authenticated user ID if available, otherwise IP address.
    """
    # Try to get user ID from request state (set during authentication)
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.id}"

    # Fall back to IP address
    return get_remote_address(request)


# Create limiter instance
limiter = Limiter(
    key_func=get_client_id, default_limits=[f"{settings.REQUESTS_PER_MINUTE}/minute"]
)


# Custom rate limit exceeded handler
def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded."""
    logger.warning(
        f"Rate limit exceeded for client: {get_client_id(request)}",
        extra={
            "client_id": get_client_id(request),
            "path": request.url.path,
            "method": request.method,
        },
    )

    return HTTPException(
        status_code=429,
        detail={
            "error": "Rate limit exceeded",
            "message": f"Too many requests. Limit: {exc.detail}",
            "retry_after": exc.retry_after,
        },
    )


# Decorator for stricter rate limiting on sensitive endpoints
def strict_rate_limit(limit: str):
    """Apply stricter rate limiting to sensitive endpoints."""
    return limiter.limit(limit)


# Decorator for auth endpoints
auth_rate_limit = limiter.limit("5/minute")

# Decorator for voting endpoints
vote_rate_limit = limiter.limit("10/minute")
