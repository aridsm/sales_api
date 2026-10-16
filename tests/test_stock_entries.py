import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_verify_stock_entry(client: AsyncClient, test_user):
    cat_response = await client.post(
        "/categories/",
        json={"name": "Stock Entry Test Cat", "color": "#00ff00", "type": 1},
    )
    assert cat_response.status_code == 201
    category_id = cat_response.json()["id"]

    prod_response = await client.post(
        "/products/",
        json={
            "name": "Stock Entry Prod",
            "category_id": category_id,
            "price": 50.0,
            "stock_amount": 5,
        },
    )
    prod_id = prod_response.json()["id"]

    entry_response = await client.post(
        "/stock_entries/",
        json={
            "products": [{"product_id": prod_id, "quantity": 10, "unit_price": 30.0}]
        },
    )
    assert entry_response.status_code == 201
    entry_data = entry_response.json()
    entry_id = entry_data["id"]

    assert entry_data["total"] == 300.0

    prod_check = await client.get(f"/products/{prod_id}")
    assert prod_check.json()["stock_amount"] == 15

    del_active_res = await client.delete(f"/stock_entries/{entry_id}")
    assert del_active_res.status_code == 400
    assert (
        del_active_res.json()["detail"]["error"]
        == "errorStockEntryMustBeCanceledBeforeDeletion"
    )

    cancel_res = await client.post(f"/stock_entries/{entry_id}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == 2

    prod_check_after_cancel = await client.get(f"/products/{prod_id}")
    assert prod_check_after_cancel.json()["stock_amount"] == 5

    del_res = await client.delete(f"/stock_entries/{entry_id}")
    assert del_res.status_code == 204

    get_res = await client.get(f"/stock_entries/{entry_id}")
    assert get_res.status_code == 404
