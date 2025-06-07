from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.models.models import VoteSessionStatus


# Shared properties
class VoteSessionBase(BaseModel):
    title: str
    description: Optional[str] = None


# Properties to receive on item creation
class VoteSessionCreate(VoteSessionBase):
    pass


# Properties to receive on item update
class VoteSessionUpdate(VoteSessionBase):
    title: Optional[str] = None


# Properties shared by models stored in DB
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


# Properties to return to client
class VoteSession(VoteSessionInDBBase):
    pass


# Properties to return with restaurants included
class VoteSessionWithRestaurants(VoteSession):
    restaurants: List["Restaurant"] = []

    class Config:
        from_attributes = True


# Properties to return with full details and results
class VoteSessionWithResults(VoteSessionWithRestaurants):
    total_votes: int = 0
    results: List[dict] = []

    class Config:
        from_attributes = True


# VoteParticipation schemas
class VoteParticipationBase(BaseModel):
    restaurant_id: int


class VoteParticipationCreate(VoteParticipationBase):
    pass


class VoteParticipationInDBBase(VoteParticipationBase):
    id: int
    vote_session_id: int
    user_id: int
    voted_at: datetime

    class Config:
        from_attributes = True


class VoteParticipation(VoteParticipationInDBBase):
    pass


# Import Restaurant here to avoid circular imports
from app.schemas.restaurant import Restaurant
VoteSessionWithRestaurants.model_rebuild() 