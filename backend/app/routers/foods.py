"""
Supported foods endpoint.
GET /api/foods
"""
from fastapi import APIRouter
from pydantic import BaseModel

from app.services.shelf_life import get_supported_foods

router = APIRouter(prefix="/api", tags=["foods"])


class FoodsResponse(BaseModel):
    supported_foods: list[str]
    description: str


@router.get("/foods", response_model=FoodsResponse)
async def list_supported_foods():
    return FoodsResponse(
        supported_foods=get_supported_foods(),
        description=(
            "FreshCheck AI currently supports individual whole fruits placed on a plain background. "
            "It does not assess cooked food, mixed dishes, meat, dairy, or processed products."
        ),
    )
