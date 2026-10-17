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

@pytest.mark.asyncio
async def test_get_categories_amounts(client: AsyncClient, test_user):
    from datetime import datetime, timezone
    now_iso = datetime.now(timezone.utc).isoformat()

    # 1. Create a category for products/sales
    cat_sale_res = await client.post("/categories/", json={"name": "Cat Sale", "color": "#123456", "type": 1})
    assert cat_sale_res.status_code == 201
    cat_sale_id = cat_sale_res.json()["id"]

    # 2. Create a product
    prod_res = await client.post("/products/", json={
        "name": "Prod 1",
        "category_id": cat_sale_id,
        "price": 25.0,
        "stock_amount": 100
    })
    assert prod_res.status_code == 201
    prod_id = prod_res.json()["id"]

    # 3. Create a sale (subtotal = 2 * 25.0 = 50.0, discount = 10.0 -> net = 40.0)
    sale_res = await client.post("/sales/", json={
        "date": now_iso,
        "discount": 10.0,
        "products": [{"product_id": prod_id, "quantity": 2}]
    })
    assert sale_res.status_code == 201

    # 4. Create stock entry (subtotal = 10 * 15.0 = 150.0, discount = 30.0 -> net = 120.0)
    stock_res = await client.post("/stock_entries/", json={
        "date": now_iso,
        "discount": 30.0,
        "products": [{"product_id": prod_id, "quantity": 10, "unit_price": 15.0}]
    })
    assert stock_res.status_code == 201

    # 5. Create category for expense and expense
    cat_exp_res = await client.post("/categories/", json={"name": "Cat Exp", "color": "#654321", "type": 2})
    assert cat_exp_res.status_code == 201
    cat_exp_id = cat_exp_res.json()["id"]

    exp_res = await client.post("/other_expenses/", json={
        "name": "Expense 1",
        "value": 80.0,
        "date": now_iso,
        "category_id": cat_exp_id
    })
    assert exp_res.status_code == 201

    # Test sales amounts (should reflect discount: 50.0 - 10.0 = 40.0)
    res_sales = await client.get("/categories/amounts", params={"type": "sales", "start_created_at": now_iso})
    assert res_sales.status_code == 200, f"Error on sales: {res_sales.text}"
    data_sales = res_sales.json()
    assert "items" in data_sales
    assert len(data_sales["items"]) >= 1
    assert data_sales["total"] == 40.0
    assert data_sales["items"][0]["value"] == 40.0

    # Test stock_entries amounts (should reflect discount: 150.0 - 30.0 = 120.0)
    res_stock = await client.get("/categories/amounts", params={"type": "stock_entries", "start_created_at": now_iso})
    assert res_stock.status_code == 200, f"Error on stock_entries: {res_stock.text}"
    data_stock = res_stock.json()
    assert "items" in data_stock
    assert len(data_stock["items"]) >= 1
    assert data_stock["total"] == 120.0
    assert data_stock["items"][0]["value"] == 120.0

    # Test other_expenses amounts
    res_expenses = await client.get("/categories/amounts", params={"type": "other_expenses", "start_created_at": now_iso})
    assert res_expenses.status_code == 200, f"Error on other_expenses: {res_expenses.text}"
    data_expenses = res_expenses.json()
    assert "items" in data_expenses
    assert len(data_expenses["items"]) >= 1
    assert data_expenses["total"] == 80.0

