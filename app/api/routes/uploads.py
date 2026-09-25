import os
import uuid
from pathlib import Path
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from app.api.dependencies import UserLoggedDep
from app.database.redis import redis_db

router = APIRouter(prefix="/uploads", tags=["uploads"])

UPLOAD_DIR = Path("uploads")
AVATARS_DIR = UPLOAD_DIR / "avatars"
COMPANY_LOGOS_DIR = UPLOAD_DIR / "company-logos"

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def ensure_upload_dirs():
    AVATARS_DIR.mkdir(parents=True, exist_ok=True)
    COMPANY_LOGOS_DIR.mkdir(parents=True, exist_ok=True)


def is_valid_image_bytes(content: bytes) -> bool:
    """Validate image magic bytes for JPEG, PNG, GIF, and WebP."""
    if len(content) < 12:
        return False
    # JPEG: FF D8 FF
    if content.startswith(b"\xff\xd8\xff"):
        return True
    # PNG: 89 50 4E 47 0D 0A 1A 0A
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return True
    # GIF: GIF87a or GIF89a
    if content.startswith(b"GIF87a") or content.startswith(b"GIF89a"):
        return True
    # WEBP: RIFF....WEBP
    if content.startswith(b"RIFF") and content[8:12] == b"WEBP":
        return True
    return False


async def check_upload_rate_limit(user_id: uuid.UUID | str) -> None:
    allowed = await redis_db.check_rate_limit(
        f"rate_limit:upload:{user_id}", max_requests=30, window_seconds=60
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "errorRateLimitExceeded",
                "message": "Upload limit exceeded. Please wait a moment before trying again.",
            },
        )


async def save_upload_file(file: UploadFile, target_dir: Path, subpath: str) -> str:
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS or file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "errorInvalidFileType",
                "message": "Only JPG, PNG, WebP and GIF files are allowed.",
            },
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "errorFileTooLarge", "message": "File size exceeds 5MB limit."},
        )

    if not is_valid_image_bytes(content):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "errorInvalidImageContent",
                "message": "File content does not match a valid image format.",
            },
        )

    filename = f"{uuid.uuid4().hex}{ext}"
    target_path = target_dir / filename

    with open(target_path, "wb") as f:
        f.write(content)

    return f"/static/uploads/{subpath}/{filename}"


@router.post("/avatar")
async def upload_avatar(
    user: UserLoggedDep,
    file: UploadFile = File(...),
):
    await check_upload_rate_limit(user.id)
    ensure_upload_dirs()
    url = await save_upload_file(file, AVATARS_DIR, "avatars")
    return {"url": url}


@router.post("/company-logo")
async def upload_company_logo(
    user: UserLoggedDep,
    file: UploadFile = File(...),
):
    await check_upload_rate_limit(user.id)
    ensure_upload_dirs()
    url = await save_upload_file(file, COMPANY_LOGOS_DIR, "company-logos")
    return {"url": url}
