from datetime import date, time
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import Restaurant


def test_vote_restaurant(
    authorized_client: TestClient, test_restaurant: Restaurant
) -> None:
    # Mock valid voting time (weekday before 14:00)
    with patch("app.crud.crud_vote.datetime") as mock_datetime:
        mock_datetime.now.return_value.time.return_value = time(12, 0)  # 12 PM
        mock_datetime.now.return_value.weekday.return_value = 1  # Tuesday

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


def test_vote_change(authorized_client: TestClient, db: Session) -> None:
    # Mock valid voting time (weekday before 14:00)
    with patch("app.crud.crud_vote.datetime") as mock_datetime:
        mock_datetime.now.return_value.time.return_value = time(12, 0)  # 12 PM
        mock_datetime.now.return_value.weekday.return_value = 1  # Tuesday

        # Create two restaurants
        restaurant1 = Restaurant(name="Restaurant 1", description="First restaurant")
        restaurant2 = Restaurant(name="Restaurant 2", description="Second restaurant")
        db.add_all([restaurant1, restaurant2])
        db.commit()
        db.refresh(restaurant1)
        db.refresh(restaurant2)

        # Store IDs before they might become detached
        restaurant1_id = restaurant1.id
        restaurant2_id = restaurant2.id

        # Vote for restaurant1
        response = authorized_client.post(
            f"{settings.API_V1_STR}/restaurants/{restaurant1_id}/vote"
        )
        assert response.status_code == 200
        content = response.json()
        assert content["total_votes"] == 1

        # Change vote to restaurant2
        response = authorized_client.post(
            f"{settings.API_V1_STR}/restaurants/{restaurant2_id}/vote"
        )
        assert response.status_code == 200

        # Check restaurant1 now has 0 votes
        response = authorized_client.get(
            f"{settings.API_V1_STR}/restaurants/{restaurant1_id}"
        )
        assert response.status_code == 200
        content = response.json()
        assert content["total_votes"] == 0


def test_simple_voting(
    authorized_client: TestClient, db: Session, test_restaurant: Restaurant
) -> None:
    # Mock valid voting time (weekday before 14:00)
    with patch("app.crud.crud_vote.datetime") as mock_datetime:
        mock_datetime.now.return_value.time.return_value = time(12, 0)  # 12 PM
        mock_datetime.now.return_value.weekday.return_value = 1  # Tuesday

        # Vote for restaurant
        response = authorized_client.post(
            f"{settings.API_V1_STR}/restaurants/{test_restaurant.id}/vote"
        )
        assert response.status_code == 200
        content = response.json()
        assert content["total_votes"] == 1
        assert content["distinct_voters"] == 1

        # Try to vote again for same restaurant (should update, not add)
        response = authorized_client.post(
            f"{settings.API_V1_STR}/restaurants/{test_restaurant.id}/vote"
        )
        assert response.status_code == 200
        content = response.json()
        assert content["total_votes"] == 1  # Still 1, not 2
        assert content["distinct_voters"] == 1


def test_vote_history(
    authorized_client: TestClient,
    db: Session,
    test_restaurant: Restaurant,
    test_dates: tuple[date, date],
) -> None:
    # Mock valid voting time (weekday before 14:00)
    with patch("app.crud.crud_vote.datetime") as mock_datetime:
        mock_datetime.now.return_value.time.return_value = time(12, 0)  # 12 PM
        mock_datetime.now.return_value.weekday.return_value = 1  # Tuesday

        # Add a vote (only one since user can vote once)
        response = authorized_client.post(
            f"{settings.API_V1_STR}/restaurants/{test_restaurant.id}/vote"
        )
        assert response.status_code == 200

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
    # Mock valid voting time (weekday before 14:00)
    with patch("app.crud.crud_vote.datetime") as mock_datetime:
        mock_datetime.now.return_value.time.return_value = time(12, 0)  # 12 PM
        mock_datetime.now.return_value.weekday.return_value = 1  # Tuesday

        # Create two restaurants
        restaurant1 = Restaurant(name="Restaurant 1", description="First restaurant")
        restaurant2 = Restaurant(name="Restaurant 2", description="Second restaurant")
        db.add_all([restaurant1, restaurant2])
        db.commit()
        db.refresh(restaurant1)
        db.refresh(restaurant2)

        # Vote for restaurant1 (1 vote from default user)
        response = authorized_client.post(
            f"{settings.API_V1_STR}/restaurants/{restaurant1.id}/vote"
        )
        assert response.status_code == 200

        # Get winner - restaurant1 should win with 1 vote vs 0
        response = authorized_client.get(
            f"{settings.API_V1_STR}/restaurants/winner/today"
        )
        assert response.status_code == 200
        content = response.json()
        assert content["id"] == restaurant1.id  # Should win with 1 vote vs 0


def test_voting_deadline(
    authorized_client: TestClient, test_restaurant: Restaurant
) -> None:
    # Mock the current time to be after voting deadline (15:00)
    with patch("app.crud.crud_vote.datetime") as mock_datetime:
        mock_datetime.now.return_value.time.return_value = time(15, 0)  # 3 PM
        mock_datetime.now.return_value.weekday.return_value = 1  # Tuesday (weekday)

        response = authorized_client.post(
            f"{settings.API_V1_STR}/restaurants/{test_restaurant.id}/vote"
        )
        assert response.status_code == 400
        assert "Voting is closed" in response.json()["detail"]
        assert "14:00" in response.json()["detail"]  # Should mention the deadline


def test_weekend_voting(
    authorized_client: TestClient, test_restaurant: Restaurant
) -> None:
    # Mock the current time to be on a Saturday (weekday 5)
    with patch("app.crud.crud_vote.datetime") as mock_datetime:
        mock_datetime.now.return_value.weekday.return_value = 5  # Saturday
        mock_datetime.now.return_value.time.return_value = time(
            12, 0
        )  # 12 PM (before deadline)

        response = authorized_client.post(
            f"{settings.API_V1_STR}/restaurants/{test_restaurant.id}/vote"
        )
        assert response.status_code == 400
        assert "only allowed on weekdays" in response.json()["detail"]


def test_unauthorized_vote(client: TestClient, test_restaurant: Restaurant) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/restaurants/{test_restaurant.id}/vote"
    )
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]
