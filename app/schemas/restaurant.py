from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class RestaurantBase(BaseModel):
    name: str
    description: Optional[str] = None
    address: Optional[str] = None
    is_active: bool = True


class RestaurantCreate(RestaurantBase):
    pass


class RestaurantUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None


class RestaurantInDBBase(RestaurantBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Restaurant(RestaurantInDBBase):
    pass


class RestaurantWithVotes(Restaurant):
    total_votes: float = 0.0
    distinct_voters: int = 0

    class Config:
        from_attributes = True
