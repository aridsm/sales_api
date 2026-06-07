import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_product(client: AsyncClient, test_user):
    # First create a category to link
    cat_res = await client.post("/categories/", json={
        "name": "Tech",
        "color": "#333333",
        "type": 1
    })
    category_id = cat_res.json()["id"]

    # Now create the product
    product_payload = {
        "name": "Wireless Mouse",
        "category_id": category_id,
        "price": 25.50,
        "stock_amount": 100
    }
    prod_res = await client.post("/products/", json=product_payload)
    
    assert prod_res.status_code == 201
    data = prod_res.json()
    assert data["name"] == "Wireless Mouse"
    assert data["price"] == 25.50
    assert data["stock_amount"] == 100
    assert data["category_id"] == category_id

@pytest.mark.asyncio
async def test_update_product(client: AsyncClient, test_user):
    cat_res = await client.post("/categories/", json={"name": "Accessories", "color": "#111111", "type": 1})
    category_id = cat_res.json()["id"]

    prod_res = await client.post("/products/", json={
        "name": "Keyboard",
        "category_id": category_id,
        "price": 40.0,
        "stock_amount": 10
    })
    product_id = prod_res.json()["id"]

    # Update product price and stock
    update_res = await client.patch(f"/products/{product_id}", json={
        "price": 35.0,
        "stock_amount": 15
    })
    
    assert update_res.status_code == 200
    update_data = update_res.json()
    assert update_data["price"] == 35.0
    assert update_data["stock_amount"] == 15
    # Name should be unchanged
    assert update_data["name"] == "Keyboard"

@pytest.mark.asyncio
async def test_delete_product(client: AsyncClient, test_user):
    cat_res = await client.post("/categories/", json={"name": "Temp", "color": "#111111", "type": 1})
    category_id = cat_res.json()["id"]

    prod_res = await client.post("/products/", json={
        "name": "To Delete",
        "category_id": category_id,
        "price": 10.0,
        "stock_amount": 5
    })
    product_id = prod_res.json()["id"]

    # Delete
    del_res = await client.delete(f"/products/{product_id}")
    assert del_res.status_code == 204

    # Verify deletion
    get_res = await client.get(f"/products/{product_id}")
    assert get_res.status_code == 404

@pytest.mark.asyncio
async def test_delete_product_with_done_sale(client: AsyncClient, test_user):
    cat_res = await client.post("/categories/", json={"name": "Temp", "color": "#111111", "type": 1})
    category_id = cat_res.json()["id"]

    prod_res = await client.post("/products/", json={
        "name": "Product With Sale",
        "category_id": category_id,
        "price": 10.0,
        "stock_amount": 5
    })
    product_id = prod_res.json()["id"]

    sale_res = await client.post("/sales/", json={
        "products": [{"product_id": product_id, "quantity": 1}]
    })
    assert sale_res.status_code == 201

    del_res = await client.delete(f"/products/{product_id}")
    assert del_res.status_code == 400
    assert del_res.json()["detail"]["error"] == "errorHasDoneSales"

@pytest.mark.asyncio
async def test_delete_bulk_products_with_done_sale(client: AsyncClient, test_user):
    cat_res = await client.post("/categories/", json={"name": "Temp", "color": "#111111", "type": 1})
    category_id = cat_res.json()["id"]

    prod1_res = await client.post("/products/", json={
        "name": "Product Bulk 1",
        "category_id": category_id,
        "price": 10.0,
        "stock_amount": 5
    })
    product1_id = prod1_res.json()["id"]

    prod2_res = await client.post("/products/", json={
        "name": "Product Bulk 2",
        "category_id": category_id,
        "price": 15.0,
        "stock_amount": 5
    })
    product2_id = prod2_res.json()["id"]

    sale_res = await client.post("/sales/", json={
        "products": [{"product_id": product1_id, "quantity": 1}]
    })
    assert sale_res.status_code == 201

    del_res = await client.request("DELETE", "/products/bulk", json={"ids": [product1_id, product2_id]})
    assert del_res.status_code == 400
    assert del_res.json()["detail"]["error"] == "errorHasDoneSales"
    assert "Product Bulk 1" in del_res.json()["detail"]["products"]
