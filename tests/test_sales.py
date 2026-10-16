import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_verify_sale_items_count(client: AsyncClient, test_user):
    cat_response = await client.post(
        "/categories/", json={"name": "Books Test", "color": "#0000ff", "type": 1}
    )
    assert cat_response.status_code == 201
    category_id = cat_response.json()["id"]

    prod1_response = await client.post(
        "/products/",
        json={
            "name": "Book 1",
            "category_id": category_id,
            "price": 20.0,
            "stock_amount": 10,
        },
    )
    prod1_id = prod1_response.json()["id"]

    prod2_response = await client.post(
        "/products/",
        json={
            "name": "Book 2",
            "category_id": category_id,
            "price": 30.0,
            "stock_amount": 5,
        },
    )
    prod2_id = prod2_response.json()["id"]

    sale_response = await client.post(
        "/sales/",
        json={
            "products": [
                {"product_id": prod1_id, "quantity": 2},
                {"product_id": prod2_id, "quantity": 1},
            ]
        },
    )
    assert sale_response.status_code == 201

    sale_data = sale_response.json()
    sale_id = sale_data["id"]

    assert sale_data["total"] == 70.0

    get_sale_response = await client.get(f"/sales/{sale_id}")
    assert get_sale_response.status_code == 200
    fetched_sale = get_sale_response.json()

    assert fetched_sale["items_count"] == 2

    p1_check = await client.get(f"/products/{prod1_id}")
    assert p1_check.json()["stock_amount"] == 8
    assert p1_check.json()["sold_amount"] == 2


@pytest.mark.asyncio
async def test_cancel_sale(client: AsyncClient, test_user):
    cat_response = await client.post(
        "/categories/", json={"name": "Cancel Test", "color": "#000000", "type": 1}
    )
    category_id = cat_response.json()["id"]

    prod_response = await client.post(
        "/products/",
        json={
            "name": "Cancel Item",
            "category_id": category_id,
            "price": 50.0,
            "stock_amount": 10,
        },
    )
    product_id = prod_response.json()["id"]

    sale_response = await client.post(
        "/sales/", json={"products": [{"product_id": product_id, "quantity": 4}]}
    )
    sale_id = sale_response.json()["id"]

    p_check_before = await client.get(f"/products/{product_id}")
    assert p_check_before.json()["stock_amount"] == 6

    cancel_response = await client.post(f"/sales/{sale_id}/cancel")
    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == 2

    p_check_after = await client.get(f"/products/{product_id}")
    assert p_check_after.json()["stock_amount"] == 10


@pytest.mark.asyncio
async def test_delete_sale_only_when_canceled(client: AsyncClient, test_user):
    cat_res = await client.post(
        "/categories/", json={"name": "Delete Sale Test", "color": "#112233", "type": 1}
    )
    category_id = cat_res.json()["id"]

    prod_res = await client.post(
        "/products/",
        json={
            "name": "Delete Sale Item",
            "category_id": category_id,
            "price": 100.0,
            "stock_amount": 20,
        },
    )
    product_id = prod_res.json()["id"]

    sale_res = await client.post(
        "/sales/", json={"products": [{"product_id": product_id, "quantity": 5}]}
    )
    sale_id = sale_res.json()["id"]

    del_active_res = await client.delete(f"/sales/{sale_id}")
    assert del_active_res.status_code == 400
    assert (
        del_active_res.json()["detail"]["error"]
        == "errorSaleMustBeCanceledBeforeDeletion"
    )

    cancel_res = await client.post(f"/sales/{sale_id}/cancel")
    assert cancel_res.status_code == 200

    del_res = await client.delete(f"/sales/{sale_id}")
    assert del_res.status_code == 204

    get_res = await client.get(f"/sales/{sale_id}")
    assert get_res.status_code == 404
