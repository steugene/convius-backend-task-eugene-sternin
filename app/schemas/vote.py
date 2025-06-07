from datetime import date

from pydantic import BaseModel


class VoteBase(BaseModel):
    restaurant_id: int


class VoteCreate(VoteBase):
    pass


class VoteUpdate(VoteBase):
    pass


class VoteInDBBase(VoteBase):
    id: int
    user_id: int
    vote_date: date
    weight: float

    class Config:
        from_attributes = True


class Vote(VoteInDBBase):
    pass


class VoteHistory(BaseModel):
    date: date
    winning_restaurant_id: int
    winning_restaurant_name: str
    total_votes: float
    distinct_voters: int
