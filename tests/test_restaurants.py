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
