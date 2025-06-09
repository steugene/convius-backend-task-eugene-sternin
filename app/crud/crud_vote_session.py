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
            votes_per_user=obj_in.votes_per_user,
            auto_close_at=obj_in.auto_close_at,
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

        restaurants = (
            db.query(Restaurant).filter(Restaurant.id.in_(restaurant_ids)).all()
        )
        if len(restaurants) != len(restaurant_ids):
            raise ValueError("Some restaurants not found")

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

    def end_session_with_winner(
        self, db: Session, *, session_id: int, user_id: int
    ) -> VoteSession:
        """End a vote session and return it with winning restaurant (only by creator)"""
        session = self.end_session(db, session_id=session_id, user_id=user_id)

        winning_restaurant_query = (
            db.query(Restaurant)
            .join(VoteParticipation, Restaurant.id == VoteParticipation.restaurant_id)
            .filter(VoteParticipation.vote_session_id == session_id)
            .group_by(Restaurant.id)
            .order_by(
                func.sum(VoteParticipation.weight).desc(),
                func.count(func.distinct(VoteParticipation.user_id)).desc(),
            )
            .first()
        )

        setattr(session, "winning_restaurant", winning_restaurant_query)

        return session

    def get_session_with_results(
        self, db: Session, *, session_id: int
    ) -> Optional[VoteSession]:
        """Get session with vote results calculated"""
        session = db.query(VoteSession).filter(VoteSession.id == session_id).first()
        if not session:
            return None

        results = (
            db.query(
                Restaurant.id,
                Restaurant.name,
                func.sum(VoteParticipation.weight).label("weighted_votes"),
                func.count(func.distinct(VoteParticipation.user_id)).label(
                    "distinct_voters"
                ),
            )
            .select_from(Restaurant)
            .join(VoteParticipation, Restaurant.id == VoteParticipation.restaurant_id)
            .filter(VoteParticipation.vote_session_id == session_id)
            .group_by(Restaurant.id, Restaurant.name)
            .order_by(
                func.sum(VoteParticipation.weight).desc(),
                func.count(func.distinct(VoteParticipation.user_id)).desc(),
            )
            .all()
        )

        total_votes = (
            db.query(func.sum(VoteParticipation.weight))
            .filter(VoteParticipation.vote_session_id == session_id)
            .scalar()
            or 0
        )

        setattr(session, "total_votes", float(total_votes))
        setattr(
            session,
            "results",
            [
                {
                    "restaurant_id": result.id,
                    "restaurant_name": result.name,
                    "weighted_votes": float(result.weighted_votes or 0),
                    "distinct_voters": result.distinct_voters,
                }
                for result in results
            ],
        )

        return session

    def check_and_auto_close_sessions(self, db: Session) -> int:
        """Check for sessions that should be auto-closed and close them"""
        now = datetime.now(timezone.utc)

        # Find active sessions that have passed their auto_close_at time
        sessions_to_close = (
            db.query(VoteSession)
            .filter(
                VoteSession.status == VoteSessionStatus.ACTIVE,
                VoteSession.auto_close_at.isnot(None),
                VoteSession.auto_close_at <= now,
            )
            .all()
        )

        closed_count = 0
        for session in sessions_to_close:
            session.status = VoteSessionStatus.CLOSED
            session.ended_at = now
            db.add(session)
            closed_count += 1

        if closed_count > 0:
            db.flush()

        return closed_count


vote_session = CRUDVoteSession(VoteSession)
