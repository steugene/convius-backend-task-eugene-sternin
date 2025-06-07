from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models
from app.api import deps
from app.core.config import settings
from app.schemas.restaurant import (
    Restaurant,
    RestaurantCreate,
    RestaurantUpdate,
    RestaurantWithVotes,
)
from app.schemas.vote import VoteCreate

router = APIRouter()

@router.get("/", response_model=List[RestaurantWithVotes])
def read_restaurants(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve restaurants.
    """
    restaurants = crud.restaurant.get_with_votes(db, skip=skip, limit=limit)
    return restaurants

@router.post("/", response_model=Restaurant)
def create_restaurant(
    *,
    db: Session = Depends(deps.get_db),
    restaurant_in: RestaurantCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new restaurant.
    """
    restaurant = crud.restaurant.get_by_name(db, name=restaurant_in.name)
    if restaurant:
        raise HTTPException(
            status_code=400,
            detail="A restaurant with this name already exists",
        )
    restaurant = crud.restaurant.create(db, obj_in=restaurant_in)
    return restaurant

@router.get("/{id}", response_model=RestaurantWithVotes)
def read_restaurant(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get restaurant by ID.
    """
    restaurant = crud.restaurant.get_with_votes(db, restaurant_id=id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant[0] if restaurant else None

@router.put("/{id}", response_model=Restaurant)
def update_restaurant(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    restaurant_in: RestaurantUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update a restaurant.
    """
    restaurant = crud.restaurant.get(db, id=id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    restaurant = crud.restaurant.update(db, db_obj=restaurant, obj_in=restaurant_in)
    return restaurant

@router.delete("/{id}", response_model=Restaurant)
def delete_restaurant(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete a restaurant.
    """
    restaurant = crud.restaurant.get(db, id=id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    restaurant = crud.restaurant.remove(db, id=id)
    return restaurant

@router.post("/{id}/vote", response_model=RestaurantWithVotes)
def vote_for_restaurant(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Vote for a restaurant.
    """
    # Get restaurant and ensure it exists
    restaurant_obj = db.query(models.Restaurant).filter(models.Restaurant.id == id).first()
    if not restaurant_obj:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    # Create vote with weight calculation
    vote_in = VoteCreate(restaurant_id=id)
    try:
        crud.vote.create_with_weight(db, obj_in=vote_in, user_id=current_user.id)
        db.commit()
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    # Get updated restaurant with votes
    updated_restaurants = crud.restaurant.get_with_votes(db, restaurant_id=id)
    if not updated_restaurants:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    return updated_restaurants[0]

@router.get("/winner/today", response_model=RestaurantWithVotes)
def get_winner(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get today's winning restaurant.
    """
    winner = crud.restaurant.get_winner(db)
    if not winner:
        raise HTTPException(status_code=404, detail="No votes have been cast today")
    return winner 