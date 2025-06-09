from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, models
from app.api import deps
from app.schemas.vote_session import (
    VoteParticipation,
    VoteParticipationCreate,
    VoteSession,
    VoteSessionCreate,
    VoteSessionUpdate,
    VoteSessionWithRestaurants,
    VoteSessionWithResults,
    validate_auto_close_at,
)

router = APIRouter()


@router.get("/", response_model=List[VoteSessionWithRestaurants])
def read_vote_sessions(
    db: Session = Depends(deps.get_db),
    skip: int = Query(
        default=0, ge=0, le=1000, description="Number of records to skip"
    ),
    limit: int = Query(
        default=100, ge=1, le=1000, description="Number of records to return"
    ),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve all vote sessions.
    """
    sessions = crud.vote_session.get_multi(db, skip=skip, limit=limit)
    return sessions


@router.get("/active", response_model=List[VoteSessionWithRestaurants])
def read_active_vote_sessions(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve active vote sessions.
    """
    sessions = crud.vote_session.get_active_sessions(db, skip=skip, limit=limit)
    return sessions


@router.get("/my", response_model=List[VoteSessionWithRestaurants])
def read_my_vote_sessions(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve vote sessions created by current user.
    """
    sessions = crud.vote_session.get_user_sessions(
        db, user_id=current_user.id, skip=skip, limit=limit
    )
    return sessions


@router.post("/", response_model=VoteSession)
def create_vote_session(
    *,
    db: Session = Depends(deps.get_db),
    session_in: VoteSessionCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new vote session.
    """
    # Manual validation instead of relying on Pydantic decorators
    try:
        validate_auto_close_at(session_in.auto_close_at, allow_past=False)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    session = crud.vote_session.create_vote_session(
        db, obj_in=session_in, created_by_user_id=current_user.id
    )
    db.commit()
    return session


@router.get("/{session_id}", response_model=VoteSessionWithResults)
def read_vote_session(
    *,
    db: Session = Depends(deps.get_db),
    session_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get vote session by ID with results.
    """
    session = crud.vote_session.get_session_with_results(db, session_id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Vote session not found")
    return session


@router.put("/{session_id}", response_model=VoteSession)
def update_vote_session(
    *,
    db: Session = Depends(deps.get_db),
    session_id: int,
    session_in: VoteSessionUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a vote session (only by creator).
    """
    session = crud.vote_session.get(db, id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Vote session not found")

    if session.created_by_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # Manual validation if auto_close_at is being updated
    if hasattr(session_in, "auto_close_at") and session_in.auto_close_at is not None:
        try:
            validate_auto_close_at(session_in.auto_close_at, allow_past=False)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

    session = crud.vote_session.update(db, db_obj=session, obj_in=session_in)
    db.commit()
    return session


@router.post("/{session_id}/restaurants", response_model=VoteSessionWithRestaurants)
def add_restaurants_to_session(
    *,
    db: Session = Depends(deps.get_db),
    session_id: int,
    restaurant_ids: List[int],
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Add restaurants to a vote session (only by creator).
    """
    try:
        session = crud.vote_session.add_restaurants_to_session(
            db,
            session_id=session_id,
            restaurant_ids=restaurant_ids,
            user_id=current_user.id,
        )
        db.commit()
        return session
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{session_id}/restaurants", response_model=VoteSessionWithRestaurants)
def remove_restaurants_from_session(
    *,
    db: Session = Depends(deps.get_db),
    session_id: int,
    restaurant_ids: List[int],
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Remove restaurants from a vote session (only by creator).
    """
    try:
        session = crud.vote_session.remove_restaurants_from_session(
            db,
            session_id=session_id,
            restaurant_ids=restaurant_ids,
            user_id=current_user.id,
        )
        db.commit()
        return session
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{session_id}/start", response_model=VoteSession)
def start_vote_session(
    *,
    db: Session = Depends(deps.get_db),
    session_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Start a vote session (only by creator).
    """
    try:
        session = crud.vote_session.start_session(
            db, session_id=session_id, user_id=current_user.id
        )
        db.commit()
        return session
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{session_id}/end", response_model=VoteSession)
def end_vote_session(
    *,
    db: Session = Depends(deps.get_db),
    session_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    End a vote session (only by creator).
    """
    try:
        session = crud.vote_session.end_session(
            db, session_id=session_id, user_id=current_user.id
        )
        db.commit()
        return session
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{session_id}/vote", response_model=VoteParticipation)
def vote_in_session(
    *,
    db: Session = Depends(deps.get_db),
    session_id: int,
    vote_in: VoteParticipationCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Vote in a session.
    """
    try:
        vote = crud.vote_participation.vote_in_session(
            db,
            session_id=session_id,
            restaurant_id=vote_in.restaurant_id,
            user_id=current_user.id,
        )
        db.commit()
        return vote
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{session_id}/my-vote", response_model=VoteParticipation)
def get_my_vote_in_session(
    *,
    db: Session = Depends(deps.get_db),
    session_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current user's vote in a session.
    """
    vote = crud.vote_participation.get_user_vote_in_session(
        db, session_id=session_id, user_id=current_user.id
    )
    if not vote:
        raise HTTPException(status_code=404, detail="No vote found in this session")
    return vote


@router.get("/{session_id}/votes", response_model=List[VoteParticipation])
def get_session_votes(
    *,
    db: Session = Depends(deps.get_db),
    session_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get all votes for a session.
    """
    votes = crud.vote_participation.get_session_votes(
        db, session_id=session_id, skip=skip, limit=limit
    )
    return votes
