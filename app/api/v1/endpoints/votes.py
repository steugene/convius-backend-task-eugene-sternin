from datetime import date, timedelta
from typing import Any, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.crud.crud_vote import vote
from app.models.models import User
from app.schemas.vote import VoteHistory

router = APIRouter()


@router.get("/history", response_model=List[VoteHistory])
def read_vote_history(
    *,
    db: Session = Depends(get_db),
    start_date: date = Query(default=None),
    end_date: date = Query(default=None),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve voting history for a date range.
    If no dates are provided, returns the last 7 days.
    """
    if not start_date:
        start_date = date.today() - timedelta(days=7)
    if not end_date:
        end_date = date.today()

    if start_date > end_date:
        raise ValueError("start_date must be before end_date")

    history = vote.get_vote_history(
        db,
        start_date=start_date,
        end_date=end_date,
    )
    return history
