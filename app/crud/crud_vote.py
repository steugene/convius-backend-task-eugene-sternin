from datetime import date, datetime, time
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

    def create_vote(
        self, db: Session, *, obj_in: VoteCreate, user_id: int
    ) -> Vote:
        today = self.get_current_date()
        
        # Check if voting is still allowed (before deadline)
        now = datetime.now().time()
        deadline = time(settings.VOTING_DEADLINE_HOUR, settings.VOTING_DEADLINE_MINUTE)
        
        if now > deadline:
            raise ValueError(
                f"Voting is closed. Deadline was {settings.VOTING_DEADLINE_HOUR:02d}:{settings.VOTING_DEADLINE_MINUTE:02d}"
            )
        
        # Check if it's a weekday (optional - most lunch voting is weekdays only)
        if datetime.now().weekday() >= 5:  # Saturday = 5, Sunday = 6
            raise ValueError("Voting is only allowed on weekdays")

        # Check if user has already voted today
        existing_vote = (
            db.query(Vote)
            .filter(Vote.user_id == user_id, Vote.vote_date == today)
            .first()
        )
        
        if existing_vote:
            # Update existing vote (change restaurant choice)
            existing_vote.restaurant_id = obj_in.restaurant_id
            db.add(existing_vote)
            db.flush()
            return existing_vote
        
        # Create new vote with standard weight of 1.0
        db_obj = Vote(
            user_id=user_id,
            restaurant_id=obj_in.restaurant_id,
            vote_date=today,
            weight=1.0,  # Standard voting - all votes equal
        )

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
                func.count(Vote.id).label("total_votes"),
                func.count(Vote.id).label("distinct_voters"),  # Same as total in standard voting
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
                "total_votes": int(vote.total_votes),
                "distinct_voters": int(vote.distinct_voters),
            }
            for vote in votes
        ]


vote = CRUDVote(Vote)
