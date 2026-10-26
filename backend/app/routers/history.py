"""
History endpoints.
GET    /api/history
DELETE /api/history/{id}
DELETE /api/history
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.config import settings
from app.database import get_db

router = APIRouter(prefix="/api", tags=["history"])


class HistoryRecord(BaseModel):
    id: int
    created_at: str
    image_filename: Optional[str]
    food_type: Optional[str]
    freshness_label: Optional[str]
    confidence: Optional[float]
    quality_warning: Optional[str]
    shelf_life_estimate: Optional[str]
    shelf_life_method: Optional[str]
    storage_condition: Optional[str]
    whole_or_cut: Optional[str]
    time_since_purchase: Optional[str]
    model_version: Optional[str]
    is_demo: bool


class HistoryResponse(BaseModel):
    records: list[HistoryRecord]
    total: int


@router.get("/history", response_model=HistoryResponse)
async def get_history(limit: int = 50, offset: int = 0, db=Depends(get_db)):
    cursor = await db.execute(
        "SELECT * FROM analyses ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (limit, offset),
    )
    rows = await cursor.fetchall()
    count_cursor = await db.execute("SELECT COUNT(*) FROM analyses")
    total = (await count_cursor.fetchone())[0]
    records = [HistoryRecord(**dict(row)) for row in rows]
    return HistoryResponse(records=records, total=total)


@router.delete("/history/{record_id}")
async def delete_record(record_id: int, db=Depends(get_db)):
    # Get filename to delete associated upload
    cursor = await db.execute(
        "SELECT image_filename FROM analyses WHERE id = ?", (record_id,)
    )
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Record {record_id} not found.")

    filename = row["image_filename"]
    await db.execute("DELETE FROM analyses WHERE id = ?", (record_id,))
    await db.commit()

    if filename:
        file_path = settings.UPLOAD_DIR / filename
        try:
            if file_path.exists():
                os.remove(file_path)
        except OSError:
            pass  # Non-critical: record is deleted regardless

    return {"deleted": True, "id": record_id}


@router.delete("/history")
async def clear_history(db=Depends(get_db)):
    # Collect filenames before deletion
    cursor = await db.execute("SELECT image_filename FROM analyses WHERE image_filename IS NOT NULL")
    rows = await cursor.fetchall()
    filenames = [row["image_filename"] for row in rows]

    await db.execute("DELETE FROM analyses")
    await db.commit()

    deleted_files = 0
    for fname in filenames:
        file_path = settings.UPLOAD_DIR / fname
        try:
            if file_path.exists():
                os.remove(file_path)
                deleted_files += 1
        except OSError:
            pass

    return {"deleted": True, "records_removed": len(filenames), "files_removed": deleted_files}
