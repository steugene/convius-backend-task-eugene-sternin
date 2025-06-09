from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import Restaurant


def test_create_restaurant(authorized_client: TestClient) -> None:
    data = {
        "name": "New Restaurant",
        "description": "A new restaurant",
        "address": "456 New St",
    }
    response = authorized_client.post(f"{settings.API_V1_STR}/restaurants", json=data)
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == data["name"]
    assert content["description"] == data["description"]
    assert content["address"] == data["address"]
    assert "id" in content


def test_create_duplicate_restaurant(
    authorized_client: TestClient, test_restaurant: Restaurant
) -> None:
    data = {
        "name": test_restaurant.name,
        "description": "Another description",
        "address": "789 Another St",
    }
    response = authorized_client.post(f"{settings.API_V1_STR}/restaurants", json=data)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_get_restaurants(
    authorized_client: TestClient, test_restaurant: Restaurant
) -> None:
    response = authorized_client.get(f"{settings.API_V1_STR}/restaurants")
    assert response.status_code == 200
    content = response.json()
    assert len(content) > 0
    assert any(r["id"] == test_restaurant.id for r in content)


def test_get_restaurant(
    authorized_client: TestClient, test_restaurant: Restaurant
) -> None:
    response = authorized_client.get(
        f"{settings.API_V1_STR}/restaurants/{test_restaurant.id}"
    )
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == test_restaurant.id
    assert content["name"] == test_restaurant.name


def test_get_nonexistent_restaurant(authorized_client: TestClient) -> None:
    response = authorized_client.get(f"{settings.API_V1_STR}/restaurants/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_update_restaurant(
    authorized_client: TestClient, test_restaurant: Restaurant
) -> None:
    data = {
        "name": "Updated Restaurant",
        "description": "Updated description",
        "address": "Updated address",
    }
    response = authorized_client.put(
        f"{settings.API_V1_STR}/restaurants/{test_restaurant.id}", json=data
    )
    assert response.status_code == 200
    content = response.json()
    assert content["name"] == data["name"]
    assert content["description"] == data["description"]
    assert content["address"] == data["address"]


def test_delete_restaurant(
    authorized_client: TestClient, test_restaurant: Restaurant
) -> None:
    response = authorized_client.delete(
        f"{settings.API_V1_STR}/restaurants/{test_restaurant.id}"
    )
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == test_restaurant.id

    # Verify restaurant is deleted
    response = authorized_client.get(
        f"{settings.API_V1_STR}/restaurants/{test_restaurant.id}"
    )
    assert response.status_code == 404


def test_unauthorized_access(client: TestClient) -> None:
    response = client.get(f"{settings.API_V1_STR}/restaurants")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]


def test_soft_delete_restaurant(authorized_client: TestClient, db: Session) -> None:
    """Test soft deleting a restaurant"""
    # Create restaurant
    restaurant_data = {
        "name": "To Be Deleted",
        "description": "This restaurant will be soft deleted",
    }
    response = authorized_client.post(
        f"{settings.API_V1_STR}/restaurants/", json=restaurant_data
    )
    assert response.status_code == 200
    restaurant_id = response.json()["id"]

    # Soft delete restaurant
    response = authorized_client.delete(
        f"{settings.API_V1_STR}/restaurants/{restaurant_id}"
    )
    assert response.status_code == 200
    content = response.json()
    assert content["is_active"] is False

    # Verify restaurant doesn't appear in regular listing
    response = authorized_client.get(f"{settings.API_V1_STR}/restaurants/")
    assert response.status_code == 200
    restaurants = response.json()
    restaurant_ids = [r["id"] for r in restaurants]
    assert restaurant_id not in restaurant_ids

    # Verify restaurant appears in admin listing
    response = authorized_client.get(f"{settings.API_V1_STR}/restaurants/all")
    assert response.status_code == 200
    all_restaurants = response.json()
    deleted_restaurant = next(
        (r for r in all_restaurants if r["id"] == restaurant_id), None
    )
    assert deleted_restaurant is not None
    assert deleted_restaurant["is_active"] is False


def test_cannot_delete_restaurant_in_active_session(
    authorized_client: TestClient, db: Session
) -> None:
    """Test that restaurants in active vote sessions cannot be deleted"""
    # Create restaurant
    restaurant_data = {
        "name": "Protected Restaurant",
        "description": "In active session",
    }
    response = authorized_client.post(
        f"{settings.API_V1_STR}/restaurants/", json=restaurant_data
    )
    restaurant_id = response.json()["id"]

    # Create vote session and add restaurant
    session_data = {"title": "Active Session", "description": "Test"}
    response = authorized_client.post(
        f"{settings.API_V1_STR}/vote-sessions/", json=session_data
    )
    session_id = response.json()["id"]

    # Add restaurant to session
    authorized_client.post(
        f"{settings.API_V1_STR}/vote-sessions/{session_id}/restaurants",
        json=[restaurant_id],
    )

    # Start session (make it active)
    authorized_client.post(f"{settings.API_V1_STR}/vote-sessions/{session_id}/start")

    # Try to delete restaurant - should fail
    response = authorized_client.delete(
        f"{settings.API_V1_STR}/restaurants/{restaurant_id}"
    )
    assert response.status_code == 400
    assert "active vote sessions" in response.json()["detail"]

    # Restaurant should still be active
    response = authorized_client.get(
        f"{settings.API_V1_STR}/restaurants/{restaurant_id}"
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is True


def test_can_delete_restaurant_after_session_ends(
    authorized_client: TestClient, db: Session
) -> None:
    """Test that restaurants can be deleted after vote sessions end"""
    # Create restaurant
    restaurant_data = {
        "name": "Later Deletable",
        "description": "Will be deletable later",
    }
    response = authorized_client.post(
        f"{settings.API_V1_STR}/restaurants/", json=restaurant_data
    )
    restaurant_id = response.json()["id"]

    # Create and run vote session
    session_data = {"title": "Temporary Session", "description": "Test"}
    response = authorized_client.post(
        f"{settings.API_V1_STR}/vote-sessions/", json=session_data
    )
    session_id = response.json()["id"]

    # Add restaurant, start session, then end it
    authorized_client.post(
        f"{settings.API_V1_STR}/vote-sessions/{session_id}/restaurants",
        json=[restaurant_id],
    )
    authorized_client.post(f"{settings.API_V1_STR}/vote-sessions/{session_id}/start")
    authorized_client.post(f"{settings.API_V1_STR}/vote-sessions/{session_id}/end")

    # Now deletion should work
    response = authorized_client.delete(
        f"{settings.API_V1_STR}/restaurants/{restaurant_id}"
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_reactivate_restaurant(authorized_client: TestClient, db: Session) -> None:
    """Test reactivating a soft-deleted restaurant"""
    # Create and soft delete restaurant
    restaurant_data = {"name": "Reactivatable", "description": "Will be reactivated"}
    response = authorized_client.post(
        f"{settings.API_V1_STR}/restaurants/", json=restaurant_data
    )
    restaurant_id = response.json()["id"]

    # Soft delete
    authorized_client.delete(f"{settings.API_V1_STR}/restaurants/{restaurant_id}")

    # Verify it's inactive
    response = authorized_client.get(f"{settings.API_V1_STR}/restaurants/all")
    deleted_restaurant = next(
        (r for r in response.json() if r["id"] == restaurant_id), None
    )
    assert deleted_restaurant["is_active"] is False

    # Reactivate
    response = authorized_client.post(
        f"{settings.API_V1_STR}/restaurants/{restaurant_id}/reactivate"
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is True

    # Verify it appears in regular listing again
    response = authorized_client.get(f"{settings.API_V1_STR}/restaurants/")
    restaurant_ids = [r["id"] for r in response.json()]
    assert restaurant_id in restaurant_ids


def test_vote_history_shows_deleted_restaurants(
    authorized_client: TestClient, db: Session
) -> None:
    """Test that vote history still shows restaurants even after soft delete"""
    # Create restaurant and vote for it
    restaurant_data = {
        "name": "Historical Restaurant",
        "description": "For history test",
    }
    response = authorized_client.post(
        f"{settings.API_V1_STR}/restaurants/", json=restaurant_data
    )
    restaurant_id = response.json()["id"]

    # Create vote session, add restaurant, and vote
    session_data = {"title": "History Session", "description": "Test"}
    response = authorized_client.post(
        f"{settings.API_V1_STR}/vote-sessions/", json=session_data
    )
    session_id = response.json()["id"]

    authorized_client.post(
        f"{settings.API_V1_STR}/vote-sessions/{session_id}/restaurants",
        json=[restaurant_id],
    )
    authorized_client.post(f"{settings.API_V1_STR}/vote-sessions/{session_id}/start")
    authorized_client.post(
        f"{settings.API_V1_STR}/vote-sessions/{session_id}/vote",
        json={"restaurant_id": restaurant_id},
    )
    authorized_client.post(f"{settings.API_V1_STR}/vote-sessions/{session_id}/end")

    # Get results before deletion
    response = authorized_client.get(
        f"{settings.API_V1_STR}/vote-sessions/{session_id}"
    )
    results_before = response.json()["results"]
    assert len(results_before) == 1
    assert results_before[0]["restaurant_name"] == "Historical Restaurant"

    # Soft delete restaurant
    authorized_client.delete(f"{settings.API_V1_STR}/restaurants/{restaurant_id}")

    # Results should still show the restaurant name
    response = authorized_client.get(
        f"{settings.API_V1_STR}/vote-sessions/{session_id}"
    )
    results_after = response.json()["results"]
    assert len(results_after) == 1
    assert results_after[0]["restaurant_name"] == "Historical Restaurant"
    assert results_after[0]["restaurant_id"] == restaurant_id
