from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.models import (
    Restaurant,
    VoteParticipation,
    VoteSession,
    VoteSessionStatus,
)
from app.schemas.vote_session import VoteSessionCreate, VoteSessionUpdate


class CRUDVoteSession(CRUDBase[VoteSession, VoteSessionCreate, VoteSessionUpdate]):
    def create_vote_session(
        self, db: Session, *, obj_in: VoteSessionCreate, created_by_user_id: int
    ) -> VoteSession:
        """Create a new vote session"""
        db_obj = VoteSession(
            title=obj_in.title,
            description=obj_in.description,
            created_by_user_id=created_by_user_id,
            status=VoteSessionStatus.DRAFT,
        )
        db.add(db_obj)
        db.flush()
        return db_obj

    def get_user_sessions(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[VoteSession]:
        """Get all vote sessions created by a user"""
        return (
            db.query(VoteSession)
            .filter(VoteSession.created_by_user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_active_sessions(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[VoteSession]:
        """Get all active vote sessions"""
        return (
            db.query(VoteSession)
            .filter(VoteSession.status == VoteSessionStatus.ACTIVE)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def add_restaurants_to_session(
        self, db: Session, *, session_id: int, restaurant_ids: List[int], user_id: int
    ) -> VoteSession:
        """Add restaurants to a vote session (only by creator)"""
        session = db.query(VoteSession).filter(VoteSession.id == session_id).first()
        if not session:
            raise ValueError("Vote session not found")

        if session.created_by_user_id != user_id:
            raise ValueError("Only the session creator can add restaurants")

        if session.status != VoteSessionStatus.DRAFT:
            raise ValueError("Can only add restaurants to draft sessions")

        # Get restaurants
        restaurants = (
            db.query(Restaurant).filter(Restaurant.id.in_(restaurant_ids)).all()
        )
        if len(restaurants) != len(restaurant_ids):
            raise ValueError("Some restaurants not found")

        # Add restaurants to session
        session.restaurants.extend(restaurants)
        db.add(session)
        db.flush()
        return session

    def remove_restaurants_from_session(
        self, db: Session, *, session_id: int, restaurant_ids: List[int], user_id: int
    ) -> VoteSession:
        """Remove restaurants from a vote session (only by creator)"""
        session = db.query(VoteSession).filter(VoteSession.id == session_id).first()
        if not session:
            raise ValueError("Vote session not found")

        if session.created_by_user_id != user_id:
            raise ValueError("Only the session creator can remove restaurants")

        if session.status != VoteSessionStatus.DRAFT:
            raise ValueError("Can only remove restaurants from draft sessions")

        # Remove restaurants from session
        session.restaurants = [
            r for r in session.restaurants if r.id not in restaurant_ids
        ]
        db.add(session)
        db.flush()
        return session

    def start_session(
        self, db: Session, *, session_id: int, user_id: int
    ) -> VoteSession:
        """Start a vote session (only by creator)"""
        session = db.query(VoteSession).filter(VoteSession.id == session_id).first()
        if not session:
            raise ValueError("Vote session not found")

        if session.created_by_user_id != user_id:
            raise ValueError("Only the session creator can start the session")

        if session.status != VoteSessionStatus.DRAFT:
            raise ValueError("Can only start draft sessions")

        if not session.restaurants:
            raise ValueError("Cannot start session without restaurants")

        session.status = VoteSessionStatus.ACTIVE
        session.started_at = datetime.now(timezone.utc)
        db.add(session)
        db.flush()
        return session

    def end_session(self, db: Session, *, session_id: int, user_id: int) -> VoteSession:
        """End a vote session (only by creator)"""
        session = db.query(VoteSession).filter(VoteSession.id == session_id).first()
        if not session:
            raise ValueError("Vote session not found")

        if session.created_by_user_id != user_id:
            raise ValueError("Only the session creator can end the session")

        if session.status != VoteSessionStatus.ACTIVE:
            raise ValueError("Can only end active sessions")

        session.status = VoteSessionStatus.CLOSED
        session.ended_at = datetime.now(timezone.utc)
        db.add(session)
        db.flush()
        return session

    def get_session_with_results(
        self, db: Session, *, session_id: int
    ) -> Optional[VoteSession]:
        """Get session with vote results calculated"""
        session = db.query(VoteSession).filter(VoteSession.id == session_id).first()
        if not session:
            return None

        # Calculate results
        results = (
            db.query(
                Restaurant.id,
                Restaurant.name,
                func.count(VoteParticipation.id).label("vote_count"),
            )
            .select_from(Restaurant)
            .join(VoteParticipation, Restaurant.id == VoteParticipation.restaurant_id)
            .filter(VoteParticipation.vote_session_id == session_id)
            .group_by(Restaurant.id, Restaurant.name)
            .order_by(func.count(VoteParticipation.id).desc())
            .all()
        )

        # Calculate total votes
        total_votes = (
            db.query(func.count(VoteParticipation.id))
            .filter(VoteParticipation.vote_session_id == session_id)
            .scalar()
            or 0
        )

        # Set computed properties
        session.total_votes = total_votes
        session.results = [
            {
                "restaurant_id": result.id,
                "restaurant_name": result.name,
                "vote_count": result.vote_count,
            }
            for result in results
        ]

        return session


vote_session = CRUDVoteSession(VoteSession)
