import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_and_verify_sale_items_count(client: AsyncClient, test_user):
    # 1. Create a Category
    cat_response = await client.post("/categories/", json={
        "name": "Books Test",
        "color": "#0000ff",
        "type": 1
    })
    assert cat_response.status_code == 201
    category_id = cat_response.json()["id"]

    # 2. Create Products
    prod1_response = await client.post("/products/", json={
        "name": "Book 1",
        "category_id": category_id,
        "price": 20.0,
        "stock_amount": 10
    })
    prod1_id = prod1_response.json()["id"]

    prod2_response = await client.post("/products/", json={
        "name": "Book 2",
        "category_id": category_id,
        "price": 30.0,
        "stock_amount": 5
    })
    prod2_id = prod2_response.json()["id"]

    # 3. Create Sale
    sale_response = await client.post("/sales/", json={
        "products": [
            {
                "product_id": prod1_id,
                "quantity": 2
            },
            {
                "product_id": prod2_id,
                "quantity": 1
            }
        ]
    })
    assert sale_response.status_code == 201
    
    sale_data = sale_response.json()
    sale_id = sale_data["id"]
    
    # Check that total is calculated correctly (20*2 + 30*1 = 70)
    assert sale_data["total"] == 70.0

    # 4. Fetch the sale to check items_count
    get_sale_response = await client.get(f"/sales/{sale_id}")
    assert get_sale_response.status_code == 200
    fetched_sale = get_sale_response.json()
    
    # 2 distinct products were added, so count(sale_products.id) = 2
    assert fetched_sale["items_count"] == 2

    # 5. Check if stock was reduced
    p1_check = await client.get(f"/products/{prod1_id}")
    assert p1_check.json()["stock_amount"] == 8
    assert p1_check.json()["sold_amount"] == 2

@pytest.mark.asyncio
async def test_cancel_sale(client: AsyncClient, test_user):
    # Create category and product
    cat_response = await client.post("/categories/", json={"name": "Cancel Test", "color": "#000000", "type": 1})
    category_id = cat_response.json()["id"]

    prod_response = await client.post("/products/", json={
        "name": "Cancel Item",
        "category_id": category_id,
        "price": 50.0,
        "stock_amount": 10
    })
    product_id = prod_response.json()["id"]

    # Create sale
    sale_response = await client.post("/sales/", json={
        "products": [{"product_id": product_id, "quantity": 4}]
    })
    sale_id = sale_response.json()["id"]

    # Check stock (10 - 4 = 6)
    p_check_before = await client.get(f"/products/{product_id}")
    assert p_check_before.json()["stock_amount"] == 6

    # Cancel sale
    cancel_response = await client.post(f"/sales/{sale_id}/cancel")
    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == 2

    # Check stock returned (6 + 4 = 10)
    p_check_after = await client.get(f"/products/{product_id}")
    assert p_check_after.json()["stock_amount"] == 10
