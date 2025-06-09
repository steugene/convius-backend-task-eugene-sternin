from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    health,
    metrics,
    restaurants,
    vote_sessions,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(
    restaurants.router, prefix="/restaurants", tags=["restaurants"]
)
api_router.include_router(
    vote_sessions.router, prefix="/vote-sessions", tags=["vote-sessions"]
)
api_router.include_router(health.router, tags=["health"])
api_router.include_router(metrics.router, tags=["metrics"])
