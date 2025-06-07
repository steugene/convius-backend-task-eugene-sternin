from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud.crud_vote import vote
from app.models.models import Restaurant, User


def test_vote_restaurant(
    authorized_client: TestClient, test_restaurant: Restaurant
) -> None:
    response = authorized_client.post(
        f"{settings.API_V1_STR}/restaurants/{test_restaurant.id}/vote"
    )
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == test_restaurant.id
    assert "total_votes" in content
    assert "distinct_voters" in content


def test_vote_nonexistent_restaurant(authorized_client: TestClient) -> None:
    response = authorized_client.post(f"{settings.API_V1_STR}/restaurants/99999/vote")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_vote_limit(
    authorized_client: TestClient, db: Session, test_restaurant: Restaurant
) -> None:
    # Create multiple restaurants
    restaurant_ids = []
    for i in range(settings.VOTES_PER_DAY + 1):
        restaurant = Restaurant(
            name=f"Restaurant {i}",
            description=f"Description {i}",
            address=f"Address {i}",
        )
        db.add(restaurant)
        db.commit()
        db.refresh(restaurant)
        restaurant_ids.append(restaurant.id)

    # Vote for each restaurant
    for idx, restaurant_id in enumerate(restaurant_ids):
        response = authorized_client.post(
            f"{settings.API_V1_STR}/restaurants/{restaurant_id}/vote"
        )
        if idx == len(restaurant_ids) - 1:
            # Last vote should fail
            assert response.status_code == 400
            assert "already used all" in response.json()["detail"]
        else:
            assert response.status_code == 200


def test_vote_weights(
    authorized_client: TestClient, db: Session, test_restaurant: Restaurant
) -> None:
    # Create another user
    user2 = User(
        email="user2@example.com",
        hashed_password="hashed_password",
        full_name="User 2",
    )
    db.add(user2)
    db.commit()
    db.refresh(user2)

    # First vote (weight 1.0)
    response = authorized_client.post(
        f"{settings.API_V1_STR}/restaurants/{test_restaurant.id}/vote"
    )
    assert response.status_code == 200
    content = response.json()
    assert content["total_votes"] == 1.0

    # Second vote (weight 0.5)
    response = authorized_client.post(
        f"{settings.API_V1_STR}/restaurants/{test_restaurant.id}/vote"
    )
    assert response.status_code == 200
    content = response.json()
    assert content["total_votes"] == 1.5

    # Third vote (weight 0.25)
    response = authorized_client.post(
        f"{settings.API_V1_STR}/restaurants/{test_restaurant.id}/vote"
    )
    assert response.status_code == 200
    content = response.json()
    assert content["total_votes"] == 1.75


def test_vote_history(
    authorized_client: TestClient,
    db: Session,
    test_restaurant: Restaurant,
    test_dates: tuple[date, date],
) -> None:
    # Add some votes
    for _ in range(3):
        authorized_client.post(
            f"{settings.API_V1_STR}/restaurants/{test_restaurant.id}/vote"
        )

    # Get vote history
    start_date, end_date = test_dates
    response = authorized_client.get(
        f"{settings.API_V1_STR}/votes/history",
        params={"start_date": start_date, "end_date": end_date},
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content) > 0
    assert all("date" in item for item in content)
    assert all("winning_restaurant_id" in item for item in content)
    assert all("total_votes" in item for item in content)
    assert all("distinct_voters" in item for item in content)


def test_winner_determination(authorized_client: TestClient, db: Session) -> None:
    # Create two restaurants
    restaurant1 = Restaurant(name="Restaurant 1", description="First restaurant")
    restaurant2 = Restaurant(name="Restaurant 2", description="Second restaurant")
    db.add_all([restaurant1, restaurant2])
    db.commit()
    db.refresh(restaurant1)
    db.refresh(restaurant2)

    # Vote for restaurant1 multiple times (total weight: 1.75)
    for _ in range(3):
        authorized_client.post(
            f"{settings.API_V1_STR}/restaurants/{restaurant1.id}/vote"
        )

    # Vote for restaurant2 with more distinct users (total weight: 1.0)
    # Create another user and vote
    user2 = User(
        email="user2@example.com",
        hashed_password="hashed_password",
        full_name="User 2",
    )
    db.add(user2)
    db.commit()
    db.refresh(user2)

    # Get winner
    response = authorized_client.get(f"{settings.API_V1_STR}/restaurants/winner/today")
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == restaurant1.id  # Should win due to higher total weight


def test_unauthorized_vote(client: TestClient, test_restaurant: Restaurant) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/restaurants/{test_restaurant.id}/vote"
    )
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]
