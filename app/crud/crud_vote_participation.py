from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.models import VoteParticipation, VoteSession, VoteSessionStatus
from app.schemas.vote_session import VoteParticipation as VoteParticipationSchema
from app.schemas.vote_session import VoteParticipationCreate


class CRUDVoteParticipation(
    CRUDBase[VoteParticipation, VoteParticipationCreate, VoteParticipationSchema]
):
    def vote_in_session(
        self, db: Session, *, session_id: int, restaurant_id: int, user_id: int
    ) -> VoteParticipation:
        """Cast a vote in a session with weighted voting logic"""

        # Check for auto-close sessions first
        from app.crud.crud_vote_session import vote_session

        vote_session.check_and_auto_close_sessions(db)

        # Get the session and validate
        session = db.query(VoteSession).filter(VoteSession.id == session_id).first()
        if not session:
            raise ValueError("Vote session not found")

        if session.status != VoteSessionStatus.ACTIVE:
            raise ValueError("Cannot vote in inactive session")

        # Check if restaurant is part of this session
        restaurant_in_session = any(r.id == restaurant_id for r in session.restaurants)
        if not restaurant_in_session:
            raise ValueError("Restaurant is not part of this vote session")

        # Count how many votes user has already cast in this session
        user_vote_count = (
            db.query(VoteParticipation)
            .filter(
                VoteParticipation.vote_session_id == session_id,
                VoteParticipation.user_id == user_id,
            )
            .count()
        )

        # Check if user has reached their vote limit
        if user_vote_count >= session.votes_per_user:
            raise ValueError(
                f"User has already cast {session.votes_per_user} votes in this session"
            )

        # Calculate vote sequence and weight
        vote_sequence = user_vote_count + 1

        # Weighted voting logic: 1st = 1.0, 2nd = 0.5, 3rd+ = 0.25
        if vote_sequence == 1:
            weight = 1.0
        elif vote_sequence == 2:
            weight = 0.5
        else:
            weight = 0.25

        # Create new vote
        db_obj = VoteParticipation(
            vote_session_id=session_id,
            user_id=user_id,
            restaurant_id=restaurant_id,
            vote_sequence=vote_sequence,
            weight=weight,
        )
        try:
            db.add(db_obj)
            db.flush()
            return db_obj
        except IntegrityError:
            db.rollback()
            raise ValueError("Vote constraint violation")

    def get_user_vote_in_session(
        self, db: Session, *, session_id: int, user_id: int
    ) -> Optional[VoteParticipation]:
        """Get user's vote in a specific session"""
        return (
            db.query(VoteParticipation)
            .filter(
                VoteParticipation.vote_session_id == session_id,
                VoteParticipation.user_id == user_id,
            )
            .first()
        )

    def get_session_votes(
        self, db: Session, *, session_id: int, skip: int = 0, limit: int = 100
    ) -> list[VoteParticipation]:
        """Get all votes for a specific session"""
        return (
            db.query(VoteParticipation)
            .filter(VoteParticipation.vote_session_id == session_id)
            .offset(skip)
            .limit(limit)
            .all()
        )


vote_participation = CRUDVoteParticipation(VoteParticipation)
