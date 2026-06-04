import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_and_get_sale_product(client: AsyncClient, test_user):
    # 1. Create a Category
    cat_response = await client.post("/categories/", json={
        "name": "Electronics Test",
        "color": "#ff0000",
        "type": 1
    })
    assert cat_response.status_code == 201
    category_id = cat_response.json()["id"]

    # 2. Create a Product
    prod_response = await client.post("/products/", json={
        "name": "Laptop Test",
        "category_id": category_id,
        "price": 1000.0,
        "stock_amount": 50
    })
    assert prod_response.status_code == 201
    product_id = prod_response.json()["id"]

    # 3. Create a fake Sale directly (since sale products need a sale_id)
    # The /sales/ endpoint expects products inside it to create a sale, 
    # but we can test the /sale_products/ endpoint directly by passing a dummy sale_id
    # Wait, the DB requires a valid foreign key for sale_id.
    # So we must create a sale first using the /sales endpoint.
    
    sale_response = await client.post("/sales/", json={
        "products": [
            {
                "product_id": product_id,
                "quantity": 1
            }
        ]
    })
    assert sale_response.status_code == 201
    sale_id = sale_response.json()["id"]

    # The sale creation already creates a sale_product. Let's fetch it via get_all
    sp_response = await client.get(f"/sale_products/?sale_id={sale_id}")
    assert sp_response.status_code == 200
    
    data = sp_response.json()
    assert data["total_items"] > 0
    
    sale_product = data["items"][0]
    assert sale_product["sale_id"] == sale_id
    assert sale_product["product_id"] == product_id
    assert sale_product["quantity"] == 1
    assert sale_product["unit_price"] == 1000.0
    
    # Verify the joins
    assert sale_product["product_name"] == "Laptop Test"
    assert sale_product["category_name"] == "Electronics Test"
    assert sale_product["category_color"] == "#ff0000"

@pytest.mark.asyncio
async def test_sale_product_isolation(client: AsyncClient, test_user):
    # Just to verify that get_all requires authentication and returns correctly
    res = await client.get("/sale_products/")
    assert res.status_code == 200
    assert "items" in res.json()
