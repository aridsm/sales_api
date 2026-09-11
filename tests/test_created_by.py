import pytest
from httpx import AsyncClient
import uuid
from datetime import datetime, timezone

@pytest.mark.asyncio
async def test_created_by_and_created_by_name_all_routes(client: AsyncClient, test_user):
    # 1. Category
    cat_res = await client.post("/categories/", json={
        "name": "Electronics",
        "color": "#123456",
        "type": 1
    })
    assert cat_res.status_code == 201
    cat_id = cat_res.json()["id"]

    # Category GET list
    cats_list_res = await client.get("/categories/")
    assert cats_list_res.status_code == 200
    cat_item = next(c for c in cats_list_res.json()["items"] if c["id"] == cat_id)
    assert cat_item["created_by"] == str(test_user.id)
    assert cat_item["created_by_name"] == test_user.name
    assert cat_item["created_by_email"] == test_user.email

    # Category GET by ID
    cat_get_res = await client.get(f"/categories/{cat_id}")
    assert cat_get_res.status_code == 200
    assert cat_get_res.json()["created_by"] == str(test_user.id)
    assert cat_get_res.json()["created_by_name"] == test_user.name
    assert cat_get_res.json()["created_by_email"] == test_user.email

    # 2. Product
    prod_res = await client.post("/products/", json={
        "name": "Mechanical Keyboard",
        "category_id": cat_id,
        "price": 150.0,
        "stock_amount": 50
    })
    assert prod_res.status_code == 201
    prod_id = prod_res.json()["id"]

    # Product GET list
    prods_list_res = await client.get("/products/")
    assert prods_list_res.status_code == 200
    prod_item = next(p for p in prods_list_res.json()["items"] if p["id"] == prod_id)
    assert prod_item["created_by"] == str(test_user.id)
    assert prod_item["created_by_name"] == test_user.name
    assert prod_item["created_by_email"] == test_user.email

    # Product GET by ID
    prod_get_res = await client.get(f"/products/{prod_id}")
    assert prod_get_res.status_code == 200
    assert prod_get_res.json()["created_by"] == str(test_user.id)
    assert prod_get_res.json()["created_by_name"] == test_user.name
    assert prod_get_res.json()["created_by_email"] == test_user.email

    # 3. Stock Entry
    entry_res = await client.post("/stock_entries/", json={
        "date": datetime.now(timezone.utc).isoformat(),
        "products": [
            {
                "product_id": prod_id,
                "quantity": 10,
                "unit_price": 80.0
            }
        ]
    })
    assert entry_res.status_code == 201
    entry_id = entry_res.json()["id"]

    # Stock Entry GET list
    entries_list_res = await client.get("/stock_entries/")
    assert entries_list_res.status_code == 200
    entry_item = next(e for e in entries_list_res.json()["items"] if e["id"] == entry_id)
    assert entry_item["created_by"] == str(test_user.id)
    assert entry_item["created_by_name"] == test_user.name
    assert entry_item["created_by_email"] == test_user.email

    # Stock Entry GET by ID
    entry_get_res = await client.get(f"/stock_entries/{entry_id}")
    assert entry_get_res.status_code == 200
    assert entry_get_res.json()["created_by"] == str(test_user.id)
    assert entry_get_res.json()["created_by_name"] == test_user.name
    assert entry_get_res.json()["created_by_email"] == test_user.email

    # 4. Sale
    sale_res = await client.post("/sales/", json={
        "date": datetime.now(timezone.utc).isoformat(),
        "products": [
            {
                "product_id": prod_id,
                "quantity": 2
            }
        ]
    })
    assert sale_res.status_code == 201
    sale_id = sale_res.json()["id"]

    # Sale GET list
    sales_list_res = await client.get("/sales/")
    assert sales_list_res.status_code == 200
    sale_item = next(s for s in sales_list_res.json()["items"] if s["id"] == sale_id)
    assert sale_item["created_by"] == str(test_user.id)
    assert sale_item["created_by_name"] == test_user.name
    assert sale_item["created_by_email"] == test_user.email

    # Sale GET by ID
    sale_get_res = await client.get(f"/sales/{sale_id}")
    assert sale_get_res.status_code == 200
    assert sale_get_res.json()["created_by"] == str(test_user.id)
    assert sale_get_res.json()["created_by_name"] == test_user.name
    assert sale_get_res.json()["created_by_email"] == test_user.email

    # 5. Other Expense
    exp_res = await client.post("/other_expenses/", json={
        "name": "Office Supplies",
        "value": 45.0,
        "date": datetime.now(timezone.utc).isoformat(),
        "category_id": cat_id
    })
    assert exp_res.status_code == 201
    exp_id = exp_res.json()["id"]

    # Other Expense GET list
    exp_list_res = await client.get("/other_expenses/")
    assert exp_list_res.status_code == 200
    exp_item = next(e for e in exp_list_res.json()["items"] if e["id"] == exp_id)
    assert exp_item["created_by"] == str(test_user.id)
    assert exp_item["created_by_name"] == test_user.name
    assert exp_item["created_by_email"] == test_user.email

    # Other Expense GET by ID
    exp_get_res = await client.get(f"/other_expenses/{exp_id}")
    assert exp_get_res.status_code == 200
    assert exp_get_res.json()["created_by"] == str(test_user.id)
    assert exp_get_res.json()["created_by_name"] == test_user.name
    assert exp_get_res.json()["created_by_email"] == test_user.email

    # 6. History
    hist_res = await client.get("/history/")
    assert hist_res.status_code == 200
    hist_items = hist_res.json()["items"]
    assert len(hist_items) > 0
    for h in hist_items:
        assert h["created_by"] == str(test_user.id)
        assert h["created_by_name"] == test_user.name
        assert h["created_by_email"] == test_user.email

@pytest.mark.asyncio
async def test_created_by_not_editable(client: AsyncClient, test_user):
    cat_res = await client.post("/categories/", json={
        "name": "Immutable Test",
        "color": "#654321",
        "type": 1
    })
    cat_id = cat_res.json()["id"]

    fake_uuid = str(uuid.uuid4())
    update_res = await client.patch(f"/categories/{cat_id}", json={
        "name": "Updated Immutable Name",
        "created_by": fake_uuid
    })
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Updated Immutable Name"
    assert update_res.json()["created_by"] == str(test_user.id)

    # Check on GET
    get_res = await client.get(f"/categories/{cat_id}")
    assert get_res.json()["created_by"] == str(test_user.id)
    assert get_res.json()["created_by_name"] == test_user.name
    assert get_res.json()["created_by_email"] == test_user.email
