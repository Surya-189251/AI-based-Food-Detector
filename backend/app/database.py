"""
SQLite database initialization and async access helpers.
"""
import aiosqlite
from pathlib import Path

from app.config import settings


async def get_db() -> aiosqlite.Connection:
    """Dependency that yields an open aiosqlite connection."""
    db_path = settings.DATABASE_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        yield db


async def init_db() -> None:
    """Create tables if they do not already exist."""
    db_path = settings.DATABASE_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
                image_filename  TEXT,
                food_type       TEXT,
                freshness_label TEXT,
                confidence      REAL,
                quality_warning TEXT,
                shelf_life_estimate TEXT,
                shelf_life_method   TEXT,
                storage_condition   TEXT,
                whole_or_cut        TEXT,
                time_since_purchase TEXT,
                model_version       TEXT,
                is_demo             INTEGER NOT NULL DEFAULT 0
            )
        """)
        await db.commit()
