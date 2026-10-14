import io
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

from app.core.config import get_settings

ALLOWED = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}


async def save_image(file: UploadFile) -> str:
    """Validate by decoding (not by trusting the content-type), downscale, re-encode, and store."""
    settings = get_settings()
    data = await file.read()
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"Image larger than {settings.max_upload_mb}MB")
    try:
        img = Image.open(io.BytesIO(data))
        fmt = img.format
        img.load()
    except (UnidentifiedImageError, OSError):
        raise HTTPException(400, "File is not a valid image")
    if fmt not in ALLOWED:
        raise HTTPException(400, "Only JPEG, PNG or WEBP images are allowed")
    img.thumbnail((1280, 1280))
    name = f"{uuid.uuid4().hex}{ALLOWED[fmt]}"
    folder = Path(settings.upload_dir)
    folder.mkdir(parents=True, exist_ok=True)
    img.save(folder / name, format=fmt)  # re-encoding strips EXIF (incl. GPS) metadata
    return name
