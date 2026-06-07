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

@pytest.mark.asyncio
async def test_delete_category_with_products(client: AsyncClient, test_user):
    cat_res = await client.post("/categories/", json={"name": "Temp Cat", "color": "#111111", "type": 1})
    category_id = cat_res.json()["id"]

    prod_res = await client.post("/products/", json={
        "name": "Linked Product",
        "category_id": category_id,
        "price": 10.0,
        "stock_amount": 5
    })
    assert prod_res.status_code == 201

    del_res = await client.delete(f"/categories/{category_id}")
    assert del_res.status_code == 400
    assert del_res.json()["detail"]["error"] == "errorHasProducts"

@pytest.mark.asyncio
async def test_delete_bulk_categories_with_products(client: AsyncClient, test_user):
    cat1_res = await client.post("/categories/", json={"name": "Cat Bulk 1", "color": "#111111", "type": 1})
    category1_id = cat1_res.json()["id"]

    cat2_res = await client.post("/categories/", json={"name": "Cat Bulk 2", "color": "#111111", "type": 1})
    category2_id = cat2_res.json()["id"]

    prod_res = await client.post("/products/", json={
        "name": "Linked Product",
        "category_id": category1_id,
        "price": 10.0,
        "stock_amount": 5
    })
    assert prod_res.status_code == 201

    del_res = await client.request("DELETE", "/categories/bulk", json={"ids": [category1_id, category2_id]})
    assert del_res.status_code == 400
    assert del_res.json()["detail"]["error"] == "errorHasProducts"
    assert "Cat Bulk 1" in del_res.json()["detail"]["categories"]

@pytest.mark.asyncio
async def test_delete_category_with_expenses(client: AsyncClient, test_user):
    cat_res = await client.post("/categories/", json={"name": "Cat Expense", "color": "#111111", "type": 1})
    category_id = cat_res.json()["id"]

    from datetime import datetime
    exp_res = await client.post("/other_expenses/", json={
        "name": "Linked Expense",
        "description": "Desc",
        "value": 50.0,
        "date": datetime.utcnow().isoformat(),
        "category_id": category_id
    })
    assert exp_res.status_code == 201

    del_res = await client.delete(f"/categories/{category_id}")
    assert del_res.status_code == 400
    assert del_res.json()["detail"]["error"] == "errorHasExpenses"

@pytest.mark.asyncio
async def test_delete_bulk_categories_with_expenses(client: AsyncClient, test_user):
    cat1_res = await client.post("/categories/", json={"name": "Cat Bulk Exp 1", "color": "#111111", "type": 1})
    category1_id = cat1_res.json()["id"]

    cat2_res = await client.post("/categories/", json={"name": "Cat Bulk Exp 2", "color": "#111111", "type": 1})
    category2_id = cat2_res.json()["id"]

    from datetime import datetime
    exp_res = await client.post("/other_expenses/", json={
        "name": "Linked Expense",
        "description": "Desc",
        "value": 50.0,
        "date": datetime.utcnow().isoformat(),
        "category_id": category1_id
    })
    assert exp_res.status_code == 201

    del_res = await client.request("DELETE", "/categories/bulk", json={"ids": [category1_id, category2_id]})
    assert del_res.status_code == 400
    assert del_res.json()["detail"]["error"] == "errorHasExpenses"
    assert "Cat Bulk Exp 1" in del_res.json()["detail"]["categories"]
