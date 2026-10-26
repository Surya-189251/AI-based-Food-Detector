"""
Image preprocessing utilities.
- EXIF-aware orientation correction
- Quality checks (blur, brightness, dimensions)
- Resizing and MobileNetV2 normalization
"""
from __future__ import annotations

import io
import struct
from pathlib import Path
from typing import Tuple

import cv2
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

from app.config import settings


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

class ImageQualityWarning(Exception):
    """Raised when an image is technically decodable but unsuitable."""
    pass


class ImageValidationError(Exception):
    """Raised when an image cannot be decoded or violates constraints."""
    pass


def load_and_validate(raw_bytes: bytes, filename: str = "upload") -> Image.Image:
    """
    Decode raw bytes into a PIL Image, apply EXIF rotation, and run basic
    structural checks. Raises ImageValidationError on failure.
    """
    if not raw_bytes:
        raise ImageValidationError("Empty file uploaded.")

    if len(raw_bytes) > settings.MAX_UPLOAD_BYTES:
        mb = settings.MAX_UPLOAD_BYTES // (1024 * 1024)
        raise ImageValidationError(f"File exceeds the {mb} MB size limit.")

    # Check extension
    ext = Path(filename).suffix.lstrip(".").lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise ImageValidationError(
            f"Unsupported file type '.{ext}'. "
            f"Please upload one of: {', '.join(sorted(settings.ALLOWED_EXTENSIONS))}."
        )

    # Attempt decode
    try:
        pil_img = Image.open(io.BytesIO(raw_bytes))
        pil_img.verify()                       # catches truncated files
    except (UnidentifiedImageError, Exception) as exc:
        raise ImageValidationError(
            f"Could not decode image. The file may be corrupted: {exc}"
        )

    # Re-open after verify (verify() closes the stream)
    pil_img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")

    # EXIF orientation
    pil_img = ImageOps.exif_transpose(pil_img)

    w, h = pil_img.size
    if w < settings.MIN_IMAGE_DIM or h < settings.MIN_IMAGE_DIM:
        raise ImageValidationError(
            f"Image is too small ({w}×{h} px). "
            f"Minimum is {settings.MIN_IMAGE_DIM}×{settings.MIN_IMAGE_DIM} px."
        )

    # Down-scale very large images to avoid memory issues
    if w > settings.MAX_IMAGE_DIM or h > settings.MAX_IMAGE_DIM:
        pil_img.thumbnail((settings.MAX_IMAGE_DIM, settings.MAX_IMAGE_DIM), Image.LANCZOS)

    return pil_img


def check_quality(pil_img: Image.Image) -> list[str]:
    """
    Run heuristic quality checks on a PIL Image.
    Returns a list of human-readable warning strings (empty = OK).
    """
    warnings: list[str] = []

    arr = np.array(pil_img)

    # --- Blur (Laplacian variance on grayscale) ---
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
    if blur_score < settings.BLUR_THRESHOLD:
        warnings.append(
            f"Image appears blurry (sharpness score {blur_score:.1f}). "
            "Please retake with a steadier hand and good lighting."
        )

    # --- Brightness ---
    brightness = arr.mean()
    if brightness < 30:
        warnings.append(
            "Image is very dark. Please ensure adequate lighting and retake."
        )
    elif brightness > 245:
        warnings.append(
            "Image is overexposed. Please reduce lighting or move away from direct light."
        )

    return warnings


def preprocess_for_model(pil_img: Image.Image, target_size: Tuple[int, int] = (224, 224)) -> np.ndarray:
    """
    Resize to target_size and apply MobileNetV2 normalization
    (scale pixels to [-1, 1]).
    Returns shape (1, H, W, 3) float32 array.
    """
    resized = pil_img.resize(target_size, Image.LANCZOS)
    arr = np.array(resized, dtype=np.float32)
    # MobileNetV2 expects values in [-1, 1]
    arr = (arr / 127.5) - 1.0
    return np.expand_dims(arr, axis=0)
