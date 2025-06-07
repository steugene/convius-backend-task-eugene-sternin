from datetime import date
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud.base import CRUDBase
from app.models.models import Restaurant, Vote
from app.schemas.vote import VoteCreate, VoteUpdate


class CRUDVote(CRUDBase[Vote, VoteCreate, VoteUpdate]):
    def get_current_date(self) -> date:
        """Get today's date."""
        return date.today()

    def get_user_votes_today(
        self, db: Session, *, user_id: int, vote_date: date
    ) -> List[Vote]:
        return (
            db.query(Vote)
            .filter(Vote.user_id == user_id, Vote.vote_date == vote_date)
            .all()
        )

    def get_restaurant_votes_today(
        self, db: Session, *, restaurant_id: int, vote_date: Optional[date] = None
    ) -> List[Vote]:
        if vote_date is None:
            vote_date = date.today()
        return (
            db.query(Vote)
            .filter(Vote.restaurant_id == restaurant_id, Vote.vote_date == vote_date)
            .all()
        )

    def create_with_weight(
        self, db: Session, *, obj_in: VoteCreate, user_id: int
    ) -> Vote:
        today = self.get_current_date()

        # Get today's votes for the user (all votes, not just for this restaurant)
        today_votes = self.get_user_votes_today(db, user_id=user_id, vote_date=today)

        # Check if user has reached the daily vote limit
        if len(today_votes) >= settings.VOTES_PER_DAY:
            raise ValueError(
                f"User has already used all {settings.VOTES_PER_DAY} votes for today"
            )

        # Get votes for this specific restaurant today by this user
        restaurant_votes = [
            v for v in today_votes if v.restaurant_id == obj_in.restaurant_id
        ]

        # Determine weight based on how many times user has voted for this restaurant today
        weights = settings.VOTE_WEIGHTS
        vote_count = len(restaurant_votes)
        weight_index = min(vote_count, len(weights) - 1)
        weight = weights[weight_index]

        # Create new vote object
        db_obj = Vote(
            user_id=user_id,
            restaurant_id=obj_in.restaurant_id,
            vote_date=today,
            weight=weight,
        )

        # Add to session and flush to get the ID
        db.add(db_obj)
        db.flush()

        return db_obj

    def get_vote_history(
        self, db: Session, *, start_date: date, end_date: date
    ) -> List[Dict[str, Any]]:
        # Get all votes in date range
        votes = (
            db.query(
                Vote.vote_date,
                Restaurant.id.label("winning_restaurant_id"),
                Restaurant.name.label("winning_restaurant_name"),
                func.sum(Vote.weight).label("total_votes"),
                func.count(func.distinct(Vote.user_id)).label("distinct_voters"),
            )
            .join(Restaurant)
            .filter(Vote.vote_date.between(start_date, end_date))
            .group_by(Vote.vote_date, Restaurant.id, Restaurant.name)
            .order_by(Vote.vote_date.desc())
            .all()
        )

        # Convert to list of dicts
        return [
            {
                "date": vote.vote_date,
                "winning_restaurant_id": vote.winning_restaurant_id,
                "winning_restaurant_name": vote.winning_restaurant_name,
                "total_votes": float(vote.total_votes),
                "distinct_voters": vote.distinct_voters,
            }
            for vote in votes
        ]


vote = CRUDVote(Vote)
