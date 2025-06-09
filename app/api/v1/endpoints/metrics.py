from typing import Any, Dict

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status_code"]
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

VOTE_COUNT = Counter("votes_total", "Total votes cast", ["restaurant_id"])

DATABASE_CONNECTIONS = Counter(
    "database_connections_total", "Total database connections", ["status"]
)


@router.get("/metrics")
def get_metrics() -> PlainTextResponse:
    """
    Prometheus metrics endpoint.
    Returns metrics in Prometheus format.
    """
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@router.get("/metrics/health")
def get_health_metrics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get application health metrics.
    """
    try:
        # Test database connectivity
        db.execute(text("SELECT 1"))
        db_healthy = True
        DATABASE_CONNECTIONS.labels(status="success").inc()
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_healthy = False
        DATABASE_CONNECTIONS.labels(status="error").inc()

    try:
        total_votes = db.execute(text("SELECT COUNT(*) FROM vote")).scalar()
        total_restaurants = db.execute(text("SELECT COUNT(*) FROM restaurant")).scalar()
        total_users = db.execute(text('SELECT COUNT(*) FROM "user"')).scalar()

        stats = {
            "total_votes": total_votes,
            "total_restaurants": total_restaurants,
            "total_users": total_users,
        }
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        stats = {"total_votes": 0, "total_restaurants": 0, "total_users": 0}

    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database_healthy": db_healthy,
        "stats": stats,
    }
