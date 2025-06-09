from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import crud, models
from app.api import deps
from app.models.models import Vote
from app.schemas.restaurant import (
    Restaurant,
    RestaurantCreate,
    RestaurantUpdate,
    RestaurantWithVotes,
)

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


@router.get("/all", response_model=List[RestaurantWithVotes])
def read_all_restaurants(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve all restaurants including inactive ones (for admin purposes).
    """
    # Use base CRUD method that doesn't filter by is_active
    restaurants = crud.restaurant.get_multi(db, skip=skip, limit=limit)

    # Calculate vote statistics for each restaurant
    from datetime import date

    today = date.today()

    for restaurant in restaurants:
        # Calculate total votes (simple count)
        total_votes = (
            db.query(func.count(Vote.id))
            .filter(Vote.restaurant_id == restaurant.id, Vote.vote_date == today)
            .scalar()
            or 0
        )

        restaurant.total_votes = int(total_votes)
        restaurant.distinct_voters = int(total_votes)
        db.add(restaurant)
        db.flush()

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
    Soft delete a restaurant (sets is_active to False).
    Cannot delete restaurants that are in active vote sessions.
    """
    try:
        restaurant = crud.restaurant.soft_delete(db, restaurant_id=id)
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        db.commit()
        return restaurant
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{id}/reactivate", response_model=Restaurant)
def reactivate_restaurant(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Reactivate a soft-deleted restaurant.
    """
    restaurant = crud.restaurant.reactivate(db, restaurant_id=id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    db.commit()
    return restaurant
