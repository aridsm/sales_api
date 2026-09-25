import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_upload_avatar_standalone(client: AsyncClient, test_user):
    fake_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    files = {"file": ("avatar.png", fake_png, "image/png")}

    res = await client.post("/uploads/avatar", files=files)
    assert res.status_code == 200
    data = res.json()
    assert "url" in data
    assert "/static/uploads/avatars/" in data["url"]


@pytest.mark.asyncio
async def test_upload_company_logo_standalone(client: AsyncClient, test_user):
    fake_jpg = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00"
    files = {"file": ("logo.jpg", fake_jpg, "image/jpeg")}

    res = await client.post("/uploads/company-logo", files=files)
    assert res.status_code == 200
    data = res.json()
    assert "url" in data
    assert "/static/uploads/company-logos/" in data["url"]


@pytest.mark.asyncio
async def test_upload_invalid_file_type(client: AsyncClient, test_user):
    files = {"file": ("malicious.exe", b"binarycontent", "application/x-msdownload")}
    res = await client.post("/uploads/avatar", files=files)
    assert res.status_code == 400
    assert res.json()["detail"]["error"] == "errorInvalidFileType"


@pytest.mark.asyncio
async def test_upload_file_too_large(client: AsyncClient, test_user):
    large_payload = b"A" * (5 * 1024 * 1024 + 10)  # > 5MB
    files = {"file": ("large.png", large_payload, "image/png")}
    res = await client.post("/uploads/avatar", files=files)
    assert res.status_code == 400
    assert res.json()["detail"]["error"] == "errorFileTooLarge"
