from datetime import date
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.models import Restaurant, Vote
from app.schemas.restaurant import RestaurantCreate, RestaurantUpdate


class CRUDRestaurant(CRUDBase[Restaurant, RestaurantCreate, RestaurantUpdate]):
    def get_by_name(self, db: Session, *, name: str) -> Optional[Restaurant]:
        return (
            db.query(Restaurant)
            .filter(Restaurant.name == name, Restaurant.is_active.is_(True))
            .first()
        )

    def get_with_votes(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        restaurant_id: Optional[int] = None,
    ) -> List[Restaurant]:
        today = date.today()

        # Base query - only active restaurants
        query = db.query(Restaurant).filter(Restaurant.is_active.is_(True))

        # If restaurant_id is provided, filter by it
        if restaurant_id is not None:
            query = query.filter(Restaurant.id == restaurant_id)

        # Get restaurants
        restaurants = query.offset(skip).limit(limit).all()

        # Calculate vote statistics for each restaurant
        for restaurant in restaurants:
            # Calculate total votes (simple count)
            total_votes = (
                db.query(func.count(Vote.id))
                .filter(Vote.restaurant_id == restaurant.id, Vote.vote_date == today)
                .scalar()
                or 0
            )

            # Calculate distinct voters (same as total votes in standard voting)
            distinct_voters = total_votes

            # Set the computed properties
            restaurant.total_votes = int(total_votes)
            restaurant.distinct_voters = int(distinct_voters)

            # Ensure the restaurant is attached to the session
            db.add(restaurant)
            db.flush()

        return restaurants

    def get_winner(self, db: Session) -> Optional[Restaurant]:
        today = date.today()

        # Get the restaurant with the most votes (only active restaurants)
        winner = (
            db.query(Restaurant)
            .join(Vote, Restaurant.id == Vote.restaurant_id)
            .filter(Vote.vote_date == today, Restaurant.is_active.is_(True))
            .group_by(Restaurant.id)
            .order_by(func.count(Vote.id).desc())
            .first()
        )

        if winner:
            # Calculate total votes (simple count)
            total_votes = (
                db.query(func.count(Vote.id))
                .filter(Vote.restaurant_id == winner.id, Vote.vote_date == today)
                .scalar()
                or 0
            )

            # Set the computed properties
            winner.total_votes = int(total_votes)
            winner.distinct_voters = int(
                total_votes
            )  # Same as total in standard voting

            # Ensure the restaurant is attached to the session
            db.add(winner)
            db.flush()

        return winner

    def is_in_active_sessions(self, db: Session, *, restaurant_id: int) -> bool:
        """Check if restaurant is currently in any active vote sessions"""
        from app.models.models import VoteSession, VoteSessionStatus

        active_sessions = (
            db.query(VoteSession)
            .join(VoteSession.restaurants)
            .filter(
                Restaurant.id == restaurant_id,
                VoteSession.status == VoteSessionStatus.ACTIVE,
            )
            .first()
        )
        return active_sessions is not None

    def soft_delete(self, db: Session, *, restaurant_id: int) -> Optional[Restaurant]:
        """Soft delete restaurant by setting is_active to False"""
        # Check if restaurant is in any active vote sessions
        if self.is_in_active_sessions(db, restaurant_id=restaurant_id):
            raise ValueError(
                "Cannot delete restaurant that is currently in active vote sessions"
            )

        restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
        if not restaurant:
            return None

        restaurant.is_active = False
        db.add(restaurant)
        db.flush()
        return restaurant

    def reactivate(self, db: Session, *, restaurant_id: int) -> Optional[Restaurant]:
        """Reactivate a soft-deleted restaurant"""
        restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
        if not restaurant:
            return None

        restaurant.is_active = True
        db.add(restaurant)
        db.flush()
        return restaurant


restaurant = CRUDRestaurant(Restaurant)
