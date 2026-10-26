"""
Image analysis endpoint.
POST /api/analyze
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import aiofiles
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import settings
from app.database import get_db
from app.services.model_service import model_service
from app.services.shelf_life import estimate_shelf_life
from app.utils.image_processing import (
    ImageQualityWarning,
    ImageValidationError,
    check_quality,
    load_and_validate,
    preprocess_for_model,
)

router = APIRouter(prefix="/api", tags=["analysis"])

FOOD_SAFETY_NOTICE = (
    "This tool assesses visible freshness. It cannot detect all harmful bacteria, "
    "toxins, or internal spoilage and cannot confirm food safety."
)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class ShelfLifeInfo(BaseModel):
    available: bool
    min_days: Optional[int] = None
    max_days: Optional[int] = None
    remaining_min: Optional[int] = None
    remaining_max: Optional[int] = None
    method: str = ""
    assumptions: str = ""
    message: str = ""


class AnalysisResponse(BaseModel):
    analysis_id: Optional[int] = None
    created_at: str
    image_filename: Optional[str] = None
    model_available: bool
    food_type: Optional[str] = None
    food_type_display: Optional[str] = None
    freshness_label: Optional[str] = None
    confidence: Optional[float] = None
    unable_to_assess: bool
    is_supported: bool
    quality_warnings: list[str]
    shelf_life: ShelfLifeInfo
    food_safety_notice: str
    model_version: str
    message: str
    is_demo: bool


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_image(
    image: UploadFile = File(..., description="Food image (JPG, PNG, WebP, max 10 MB)"),
    storage_condition: str = Form("unknown"),
    whole_or_cut: str = Form("whole"),
    days_since_purchase: Optional[str] = Form(None),
    db=Depends(get_db),
):
    # ---- 1. Read raw bytes ------------------------------------------------
    raw = await image.read()

    # ---- 2. Validate & decode image ---------------------------------------
    try:
        pil_img = load_and_validate(raw, image.filename or "upload.jpg")
    except ImageValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # ---- 3. Quality checks ------------------------------------------------
    quality_warnings = check_quality(pil_img)

    # ---- 4. Save file (generated UUID filename, no user-supplied paths) ---
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    ext = Path(image.filename or "upload.jpg").suffix.lower() or ".jpg"
    safe_filename = f"{uuid.uuid4().hex}{ext}"
    save_path = settings.UPLOAD_DIR / safe_filename
    async with aiofiles.open(save_path, "wb") as f:
        await f.write(raw)

    # ---- 5. Preprocess & run model ----------------------------------------
    preprocessed = preprocess_for_model(pil_img)
    result = model_service.predict(preprocessed)

    # ---- 6. Shelf-life estimate -------------------------------------------
    days_float: Optional[float] = None
    if days_since_purchase:
        try:
            days_float = float(days_since_purchase)
        except ValueError:
            pass

    sl = estimate_shelf_life(
        food_type=result.food_type,
        freshness_label=result.freshness_label,
        whole_or_cut=whole_or_cut,
        storage_condition=storage_condition,
        days_since_purchase=days_float,
    )

    # ---- 7. Persist to SQLite --------------------------------------------
    now_iso = datetime.now(timezone.utc).isoformat()
    analysis_id = None

    if result.model_available:
        cursor = await db.execute(
            """
            INSERT INTO analyses
              (created_at, image_filename, food_type, freshness_label, confidence,
               quality_warning, shelf_life_estimate, shelf_life_method,
               storage_condition, whole_or_cut, time_since_purchase,
               model_version, is_demo)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                now_iso,
                safe_filename,
                result.food_type,
                result.freshness_label,
                result.confidence,
                "; ".join(quality_warnings) if quality_warnings else None,
                sl.message,
                sl.method,
                storage_condition,
                whole_or_cut,
                days_since_purchase,
                result.model_version,
                0,
            ),
        )
        await db.commit()
        analysis_id = cursor.lastrowid

    # ---- 8. Build response ------------------------------------------------
    return AnalysisResponse(
        analysis_id=analysis_id,
        created_at=now_iso,
        image_filename=safe_filename,
        model_available=result.model_available,
        food_type=result.food_type,
        food_type_display=result.food_type_display,
        freshness_label=result.freshness_label,
        confidence=result.confidence,
        unable_to_assess=result.unable_to_assess,
        is_supported=result.is_supported,
        quality_warnings=quality_warnings,
        shelf_life=ShelfLifeInfo(
            available=sl.available,
            min_days=sl.min_days,
            max_days=sl.max_days,
            remaining_min=sl.remaining_min,
            remaining_max=sl.remaining_max,
            method=sl.method,
            assumptions=sl.assumptions,
            message=sl.message,
        ),
        food_safety_notice=FOOD_SAFETY_NOTICE,
        model_version=result.model_version,
        message=result.message,
        is_demo=False,
    )
