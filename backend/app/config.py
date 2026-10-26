"""
Application configuration via environment variables.
Copy .env.example to backend/.env and adjust values before running.
"""
from pydantic_settings import BaseSettings
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # --- Application ---
    APP_NAME: str = "FreshCheck AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # --- CORS ---
    # Comma-separated list of allowed origins, e.g. http://localhost:5173
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # --- File uploads ---
    UPLOAD_DIR: Path = BASE_DIR / "data" / "uploads"
    MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024   # 10 MB
    ALLOWED_EXTENSIONS: set[str] = {"jpg", "jpeg", "png", "webp"}

    # --- Database ---
    DATABASE_PATH: Path = BASE_DIR / "data" / "db" / "freshcheck.db"

    # --- ML Model ---
    MODEL_DIR: Path = BASE_DIR / "saved_models"
    MODEL_FILENAME: str = "freshcheck_model.keras"
    LABELS_FILENAME: str = "labels.json"
    MODEL_VERSION: str = "1.0.0"

    # Minimum confidence to report a result (0-1). Below this → "Unable to assess".
    CONFIDENCE_THRESHOLD: float = 0.60

    # --- Image quality ---
    BLUR_THRESHOLD: float = 80.0        # Laplacian variance below this = blurry
    MIN_IMAGE_DIM: int = 64             # Pixels — smaller images are rejected
    MAX_IMAGE_DIM: int = 8192           # Pixels — larger images are resized

    class Config:
        env_file = str(BASE_DIR / ".env")
        env_file_encoding = "utf-8"


settings = Settings()
