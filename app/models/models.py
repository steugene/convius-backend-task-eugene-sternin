import enum
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class VoteSessionStatus(enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"


# Junction table for vote session and restaurants (many-to-many)
vote_session_restaurants = Table(
    "vote_session_restaurants",
    Base.metadata,
    Column("vote_session_id", Integer, ForeignKey("vote_session.id"), primary_key=True),
    Column("restaurant_id", Integer, ForeignKey("restaurant.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships


class Restaurant(Base):
    __tablename__ = "restaurant"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True, nullable=False)
    description = Column(String(500), nullable=True)
    address = Column(String(200), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    vote_sessions = relationship(
        "VoteSession", secondary=vote_session_restaurants, back_populates="restaurants"
    )

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._total_votes: float = 0.0
        self._distinct_voters: int = 0

    @property
    def total_votes(self) -> float:
        return self._total_votes

    @total_votes.setter
    def total_votes(self, value: float) -> None:
        self._total_votes = float(value)

    @property
    def distinct_voters(self) -> int:
        return self._distinct_voters

    @distinct_voters.setter
    def distinct_voters(self, value: int) -> None:
        self._distinct_voters = int(value)


class VoteSession(Base):
    __tablename__ = "vote_session"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status: Mapped[VoteSessionStatus] = mapped_column(
        Enum(VoteSessionStatus), nullable=False, default=VoteSessionStatus.DRAFT
    )
    created_by_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id"), nullable=False
    )
    votes_per_user: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    auto_close_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    restaurants = relationship(
        "Restaurant", secondary=vote_session_restaurants, back_populates="vote_sessions"
    )
    participations = relationship("VoteParticipation", back_populates="vote_session")

    # Indexes for performance
    __table_args__ = (
        Index("ix_vote_session_status", "status"),
        Index("ix_vote_session_created_by", "created_by_user_id"),
        Index("ix_vote_session_auto_close", "auto_close_at"),
    )

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._total_votes: float = 0.0
        self._results: list = []

    @property
    def total_votes(self) -> float:
        return self._total_votes

    @total_votes.setter
    def total_votes(self, value: float) -> None:
        self._total_votes = float(value)

    @property
    def results(self) -> list:
        return self._results

    @results.setter
    def results(self, value: list) -> None:
        self._results = value


class VoteParticipation(Base):
    __tablename__ = "vote_participation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    vote_session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("vote_session.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    restaurant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("restaurant.id", ondelete="RESTRICT"), nullable=False
    )
    vote_sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    voted_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    vote_session = relationship("VoteSession", back_populates="participations")
    user = relationship("User")
    restaurant = relationship("Restaurant")

    # Unique constraint: one vote per user per session per sequence
    __table_args__ = (
        UniqueConstraint(
            "vote_session_id",
            "user_id",
            "vote_sequence",
            name="unique_user_vote_sequence_per_session",
        ),
    )
