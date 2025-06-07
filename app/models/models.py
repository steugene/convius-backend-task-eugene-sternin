from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
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
    votes = relationship("Vote", back_populates="user")


class Restaurant(Base):
    __tablename__ = "restaurant"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    address = Column(String, nullable=True)
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    votes = relationship("Vote", back_populates="restaurant")

    def __init__(self, **kwargs):
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


class Vote(Base):
    __tablename__ = "vote"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    restaurant_id = Column(Integer, ForeignKey("restaurant.id"), nullable=False)
    vote_date = Column(
        Date, nullable=False, default=lambda: datetime.now(timezone.utc).date()
    )
    weight = Column(Float, nullable=False, default=1.0)
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
    user = relationship("User", back_populates="votes")
    restaurant = relationship("Restaurant", back_populates="votes")
