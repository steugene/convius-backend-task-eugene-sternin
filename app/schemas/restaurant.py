from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime

class RestaurantBase(BaseModel):
    name: str
    description: Optional[str] = None
    address: Optional[str] = None

class RestaurantCreate(RestaurantBase):
    pass

class RestaurantUpdate(RestaurantBase):
    pass

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