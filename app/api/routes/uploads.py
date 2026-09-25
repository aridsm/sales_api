import os
import uuid
from pathlib import Path
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from app.api.dependencies import UserLoggedDep

router = APIRouter(prefix="/uploads", tags=["uploads"])

UPLOAD_DIR = Path("uploads")
AVATARS_DIR = UPLOAD_DIR / "avatars"
COMPANY_LOGOS_DIR = UPLOAD_DIR / "company-logos"

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"}
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
    "image/svg+xml",
}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def ensure_upload_dirs():
    AVATARS_DIR.mkdir(parents=True, exist_ok=True)
    COMPANY_LOGOS_DIR.mkdir(parents=True, exist_ok=True)


async def save_upload_file(file: UploadFile, target_dir: Path, subpath: str) -> str:
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS or file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "errorInvalidFileType", "message": "Only JPG, PNG, WebP, GIF and SVG files are allowed."},
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "errorFileTooLarge", "message": "File size exceeds 5MB limit."},
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
    ensure_upload_dirs()
    url = await save_upload_file(file, AVATARS_DIR, "avatars")
    return {"url": url}


@router.post("/company-logo")
async def upload_company_logo(
    user: UserLoggedDep,
    file: UploadFile = File(...),
):
    ensure_upload_dirs()
    url = await save_upload_file(file, COMPANY_LOGOS_DIR, "company-logos")
    return {"url": url}
