from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.models import VoteSessionStatus


def validate_auto_close_at(
    auto_close_at: Optional[datetime], allow_past: bool = False
) -> None:
    """
    Validate auto_close_at datetime value with explicit business rules.

    This is our custom validation - no magic decorators, full control!

    Args:
        auto_close_at: The datetime to validate
        allow_past: Whether to allow past times (for testing only)

    Raises:
        ValueError: If the datetime violates our business rules
    """
    if auto_close_at is None:
        return

    from datetime import timedelta, timezone

    if auto_close_at.tzinfo is not None:
        now = datetime.now(timezone.utc)
    else:
        now = datetime.now()

    if auto_close_at <= now and not allow_past:
        raise ValueError(
            f"auto_close_at must be in the future. "
            f"Provided: {auto_close_at}, Current time: {now}. "
            f"Creating a session that's already closed doesn't make business sense!"
        )

    max_future = now + timedelta(days=30)
    if auto_close_at > max_future:
        raise ValueError(
            f"auto_close_at cannot be more than 30 days in the future. "
            f"Provided: {auto_close_at}, Max allowed: {max_future}"
        )

    if allow_past:
        one_year_ago = now - timedelta(days=365)
        if auto_close_at < one_year_ago:
            raise ValueError(
                f"auto_close_at cannot be more than 1 year in the past. "
                f"Provided: {auto_close_at}"
            )


class VoteSessionBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Session title")
    description: Optional[str] = Field(
        None, max_length=1000, description="Session description"
    )
    votes_per_user: int = Field(
        default=1, ge=1, le=10, description="Number of votes per user"
    )
    auto_close_at: Optional[datetime] = Field(None, description="Automatic close time")


class VoteSessionCreate(VoteSessionBase):
    pass


class VoteSessionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class VoteSessionInDBBase(VoteSessionBase):
    id: int
    status: VoteSessionStatus
    created_by_user_id: int
    created_at: datetime
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class VoteSession(VoteSessionInDBBase):
    pass


class VoteSessionWithRestaurants(VoteSession):
    restaurants: List["Restaurant"] = []

    class Config:
        from_attributes = True


class VoteResult(BaseModel):
    restaurant_id: int
    restaurant_name: str
    weighted_votes: float
    distinct_voters: int


class VoteSessionWithResults(VoteSessionWithRestaurants):
    total_votes: float = 0.0
    results: List[VoteResult] = []

    class Config:
        from_attributes = True


class VoteSessionEndResponse(VoteSession):
    """Response schema when ending a vote session - includes winning restaurant."""

    winning_restaurant: Optional["Restaurant"] = Field(
        None, description="The restaurant that won the vote (if any votes were cast)"
    )

    class Config:
        from_attributes = True


class VoteParticipationBase(BaseModel):
    restaurant_id: int = Field(..., gt=0, description="Restaurant ID to vote for")


class VoteParticipationCreate(VoteParticipationBase):
    pass


class VoteParticipationInDBBase(VoteParticipationBase):
    id: int
    vote_session_id: int
    user_id: int
    vote_sequence: int
    weight: float
    voted_at: datetime

    class Config:
        from_attributes = True


class VoteParticipation(VoteParticipationInDBBase):
    pass


from app.schemas.restaurant import Restaurant  # noqa: E402

VoteSessionWithRestaurants.model_rebuild()
VoteSessionEndResponse.model_rebuild()
