from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_client_id(request: Request) -> str:
    """
    Get client identifier for rate limiting.
    Uses authenticated user ID if available, otherwise IP address.
    """
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.id}"  # noqa: E231

    return get_remote_address(request)


limiter = Limiter(
    key_func=get_client_id, default_limits=[f"{settings.REQUESTS_PER_MINUTE}/minute"]
)


def custom_rate_limit_handler(request: Request, exc: Exception) -> JSONResponse:
    """Custom handler for rate limit exceeded."""
    logger.warning(
        f"Rate limit exceeded for client: {get_client_id(request)}",
        extra={
            "client_id": get_client_id(request),
            "path": request.url.path,
            "method": request.method,
        },
    )

    # Ensure it's actually a RateLimitExceeded exception
    if isinstance(exc, RateLimitExceeded):
        detail = getattr(exc, "detail", "Unknown limit")
        retry_after = getattr(exc, "retry_after", None)
    else:
        detail = "Unknown limit"
        retry_after = None

    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "message": f"Too many requests. Limit: {detail}",
            "retry_after": retry_after,
        },
    )


def strict_rate_limit(limit: str):
    """Apply stricter rate limiting to sensitive endpoints."""
    return limiter.limit(limit)


auth_rate_limit = limiter.limit("5/minute")

vote_rate_limit = limiter.limit("10/minute")
