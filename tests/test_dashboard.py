import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dashboard_top_products(client: AsyncClient, test_user):
    # 1. Empty top products
    empty_res = await client.get("/dashboard/top-products")
    assert empty_res.status_code == 200
    assert empty_res.json() == []

    # 2. Create category and products
    cat_res = await client.post(
        "/categories/", json={"name": "TopCategory", "color": "#00FF00", "type": 1}
    )
    assert cat_res.status_code == 201
    category_id = cat_res.json()["id"]

    prod1_res = await client.post(
        "/products/",
        json={
            "name": "Prod A",
            "category_id": category_id,
            "price": 50.0,
            "stock_amount": 50,
        },
    )
    prod1_id = prod1_res.json()["id"]

    prod2_res = await client.post(
        "/products/",
        json={
            "name": "Prod B",
            "category_id": category_id,
            "price": 10.0,
            "stock_amount": 50,
        },
    )
    prod2_id = prod2_res.json()["id"]

    # 3. Create sales: Prod A gets 3 units (revenue 150), Prod B gets 10 units (revenue 100)
    sale1_res = await client.post(
        "/sales/",
        json={
            "products": [{"product_id": prod1_id, "quantity": 3}],
            "discount": 0.0,
        },
    )
    assert sale1_res.status_code == 201

    sale2_res = await client.post(
        "/sales/",
        json={
            "products": [{"product_id": prod2_id, "quantity": 10}],
            "discount": 0.0,
        },
    )
    assert sale2_res.status_code == 201

    # 4. Query top products (default sort_by=quantity)
    top_res = await client.get("/dashboard/top-products")
    assert top_res.status_code == 200
    top_data = top_res.json()
    assert len(top_data) == 2

    # Prod B should be first because quantity_sold is 10 > 3
    assert top_data[0]["product_name"] == "Prod B"
    assert top_data[0]["quantity_sold"] == 10
    assert top_data[0]["total_revenue"] == 100.0
    assert top_data[0]["category_name"] == "TopCategory"
    assert top_data[0]["category_color"] == "#00FF00"

    assert top_data[1]["product_name"] == "Prod A"
    assert top_data[1]["quantity_sold"] == 3
    assert top_data[1]["total_revenue"] == 150.0

    # 5. Query top products sorted by revenue
    top_rev_res = await client.get("/dashboard/top-products?sort_by=revenue")
    assert top_rev_res.status_code == 200
    top_rev_data = top_rev_res.json()
    assert len(top_rev_data) == 2

    # Prod A should be first because total_revenue is 150.0 > 100.0
    assert top_rev_data[0]["product_name"] == "Prod A"
    assert top_rev_data[0]["total_revenue"] == 150.0
    assert top_rev_data[1]["product_name"] == "Prod B"
    assert top_rev_data[1]["total_revenue"] == 100.0



@pytest.mark.asyncio
async def test_dashboard_top_products_with_discount(client: AsyncClient, test_user):
    cat_res = await client.post(
        "/categories/", json={"name": "DiscountCat", "color": "#FF0000", "type": 1}
    )
    category_id = cat_res.json()["id"]

    prod1_res = await client.post(
        "/products/",
        json={
            "name": "Prod C",
            "category_id": category_id,
            "price": 60.0,
            "stock_amount": 50,
        },
    )
    prod1_id = prod1_res.json()["id"]

    prod2_res = await client.post(
        "/products/",
        json={
            "name": "Prod D",
            "category_id": category_id,
            "price": 40.0,
            "stock_amount": 50,
        },
    )
    prod2_id = prod2_res.json()["id"]

    # Subtotal = 60 + 40 = 100. Discount = 20. Total = 80.
    # Prod C proportional net = 60 * (80 / 100) = 48.0
    # Prod D proportional net = 40 * (80 / 100) = 32.0
    sale_res = await client.post(
        "/sales/",
        json={
            "products": [
                {"product_id": prod1_id, "quantity": 1},
                {"product_id": prod2_id, "quantity": 1},
            ],
            "discount": 20.0,
        },
    )
    assert sale_res.status_code == 201

    top_res = await client.get("/dashboard/top-products?limit=10")
    assert top_res.status_code == 200
    top_data = {p["product_name"]: p for p in top_res.json()}

    assert top_data["Prod C"]["total_revenue"] == 48.0
    assert top_data["Prod D"]["total_revenue"] == 32.0

