import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_category(client: AsyncClient, test_user):
    payload = {
        "name": "Groceries",
        "color": "#00ff00",
        "type": 2  # OTHER_EXPENSE
    }
    
    response = await client.post("/categories/", json=payload)
    assert response.status_code == 201
    
    data = response.json()
    assert data["name"] == "Groceries"
    assert data["color"] == "#00ff00"
    assert data["type"] == 2
    assert "id" in data
    assert data["user_id"] == str(test_user.id)

@pytest.mark.asyncio
async def test_get_categories_isolation(client: AsyncClient, test_user):
    # Fetch categories for the current test_user
    response = await client.get("/categories/")
    assert response.status_code == 200
    
    data = response.json()
    assert "items" in data
    assert "total_items" in data

@pytest.mark.asyncio
async def test_update_category(client: AsyncClient, test_user):
    # First create
    create_response = await client.post("/categories/", json={
        "name": "To Update",
        "color": "#111111",
        "type": 1
    })
    cat_id = create_response.json()["id"]

    # Update
    update_payload = {"name": "Updated Name"}
    update_response = await client.patch(f"/categories/{cat_id}", json=update_payload)
    
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Updated Name"
    # Color and type should remain the same since they were omitted
    assert update_response.json()["color"] == "#111111"
    assert update_response.json()["type"] == 1
