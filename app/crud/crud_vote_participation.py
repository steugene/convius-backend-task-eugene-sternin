from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.crud.base import CRUDBase
from app.models.models import VoteParticipation, VoteSession, VoteSessionStatus, Restaurant
from app.schemas.vote_session import VoteParticipationCreate, VoteParticipation as VoteParticipationSchema


class CRUDVoteParticipation(CRUDBase[VoteParticipation, VoteParticipationCreate, VoteParticipationSchema]):
    
    def vote_in_session(
        self, db: Session, *, session_id: int, restaurant_id: int, user_id: int
    ) -> VoteParticipation:
        """Cast or change a vote in a session"""
        
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

        # Check if user already voted in this session
        existing_vote = (
            db.query(VoteParticipation)
            .filter(
                VoteParticipation.vote_session_id == session_id,
                VoteParticipation.user_id == user_id
            )
            .first()
        )

        if existing_vote:
            # Update existing vote (change restaurant choice)
            existing_vote.restaurant_id = restaurant_id
            db.add(existing_vote)
            db.flush()
            return existing_vote
        else:
            # Create new vote
            db_obj = VoteParticipation(
                vote_session_id=session_id,
                user_id=user_id,
                restaurant_id=restaurant_id
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
                VoteParticipation.user_id == user_id
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