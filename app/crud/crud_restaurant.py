from typing import List, Optional

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.models import Restaurant
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
        query = db.query(Restaurant).filter(Restaurant.is_active.is_(True))

        if restaurant_id is not None:
            query = query.filter(Restaurant.id == restaurant_id)

        restaurants = query.offset(skip).limit(limit).all()

        # Set default vote counts since we're using session-based voting now
        for restaurant in restaurants:
            restaurant.total_votes = 0.0
            restaurant.distinct_voters = 0

            # Ensure the restaurant is attached to the session
            db.add(restaurant)
            db.flush()

        return restaurants

    def get_winner(self, db: Session) -> Optional[Restaurant]:
        """
        Get daily winner - deprecated with session-based voting.
        Use vote session results instead.
        """
        # Daily winner concept no longer applies with session-based voting
        return None

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
