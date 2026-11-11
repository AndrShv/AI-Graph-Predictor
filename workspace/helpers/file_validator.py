import io

from workspace.configs.settings import settings
from PIL import Image, UnidentifiedImageError
from fastapi import UploadFile


def validate_file(file: UploadFile) -> None:
    if not file or not file.filename:
        raise ValueError("File cannot be empty")
    if file.content_type not in ["image/png", "image/jpeg"]:
        raise ValueError("Only PNG/JPG allowed")


def validate_image_bytes(content: bytes) -> None:
    if not content:
        raise ValueError("File cannot be empty")
    if len(content) > settings.MAX_UPLOAD_BYTES:
        raise ValueError("Image is too large")
    try:
        image = Image.open(io.BytesIO(content))
        image.verify()
    except UnidentifiedImageError as exc:
        raise ValueError("Invalid image data") from exc
    except Exception as exc:
        raise ValueError("Invalid image data") from exc
