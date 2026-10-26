"""
Health-check and model-status endpoint.
GET /api/health
"""
from fastapi import APIRouter
from pydantic import BaseModel

from app.config import settings
from app.services.model_service import model_service

router = APIRouter(prefix="/api", tags=["health"])


class HealthResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    status: str
    app_name: str
    app_version: str
    model_ready: bool
    model_version: str
    model_message: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="ok",
        app_name=settings.APP_NAME,
        app_version=settings.APP_VERSION,
        model_ready=model_service.is_ready,
        model_version=settings.MODEL_VERSION,
        model_message="" if model_service.is_ready else (model_service.load_error or "Model not configured."),
    )
