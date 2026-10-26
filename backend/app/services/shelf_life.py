"""
Shelf-life reference data and estimation logic.

This module implements a REFERENCE-BASED estimate using verified food-science
guidance. It does NOT use a trained regression model (no longitudinal training
dataset is bundled). All assumptions are documented.

Sources used for reference ranges:
  - USDA FoodKeeper App (https://www.foodsafety.gov/keep-food-safe/foodkeeper-app)
  - FDA Food Safety (https://www.fda.gov/food/buy-store-serve-safe-food)
  - UC Davis Postharvest Center commodity fact sheets
    (https://postharvest.ucdavis.edu)

Estimation method label shown to users: "Reference-based estimate (USDA/FDA guidance)"
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# ---------------------------------------------------------------------------
# Reference shelf-life table
# ---------------------------------------------------------------------------
# Structure:
#   food_key -> storage_condition -> (min_days, max_days, notes)
# "unknown" storage falls back to "room_temp" reference ranges.
# All ranges assume "whole" unless specified under the "cut" sub-key.
#
# IMPORTANT: These are approximate ranges for planning purposes only.
# Actual shelf life depends on pre-purchase history, temperature fluctuations,
# humidity, and many other factors not visible in a single image.

SHELF_LIFE_REFERENCE: dict[str, dict] = {
    "apple": {
        "room_temp": {
            "whole": (5, 10, "At 18–22 °C. Waxed/store-bought apples last toward the upper end."),
            "cut":   (1, 2,  "Cover tightly; use lemon juice to slow browning."),
        },
        "refrigerated": {
            "whole": (21, 42, "Refrigerator crisper drawer (1–4 °C)."),
            "cut":   (3, 5,   "In airtight container."),
        },
    },
    "banana": {
        "room_temp": {
            "whole": (2, 7, "Depends heavily on ripeness at purchase. Very ripe = 1–2 days."),
            "cut":   (1, 1, "Browning is rapid; use immediately or refrigerate."),
        },
        "refrigerated": {
            "whole": (5, 9,  "Skin blackens but flesh stays good longer."),
            "cut":   (2, 3,  "In airtight container."),
        },
    },
    "orange": {
        "room_temp": {
            "whole": (5, 10, "At 18–22 °C. Dry environments shorten shelf life."),
            "cut":   (1, 2,  "Cover cut surfaces; refrigerate promptly."),
        },
        "refrigerated": {
            "whole": (21, 35, "Mesh bag in crisper drawer."),
            "cut":   (3, 4,   "In airtight container."),
        },
    },
}

# ---------------------------------------------------------------------------
# Estimation
# ---------------------------------------------------------------------------

@dataclass
class ShelfLifeResult:
    available: bool
    min_days: Optional[int] = None
    max_days: Optional[int] = None
    remaining_min: Optional[int] = None
    remaining_max: Optional[int] = None
    method: str = ""
    assumptions: str = ""
    message: str = ""


def estimate_shelf_life(
    food_type: Optional[str],
    freshness_label: Optional[str],
    whole_or_cut: str = "whole",
    storage_condition: str = "unknown",
    days_since_purchase: Optional[float] = None,
) -> ShelfLifeResult:
    """
    Return a ShelfLifeResult for the given inputs.

    Parameters
    ----------
    food_type          : Normalised food key (e.g. "apple").
    freshness_label    : "Fresh", "Moderately Fresh", "Spoiled", or None.
    whole_or_cut       : "whole" | "cut"
    storage_condition  : "room_temp" | "refrigerated" | "unknown"
    days_since_purchase: Days elapsed since purchase or cutting, if known.
    """
    food_key = (food_type or "").lower().strip()
    if food_key not in SHELF_LIFE_REFERENCE:
        return ShelfLifeResult(
            available=False,
            message="Shelf-life reference data is not available for this food type.",
            method="N/A",
        )

    if freshness_label == "Spoiled":
        return ShelfLifeResult(
            available=False,
            message="Food appears spoiled. Discard immediately — do not consume.",
            method="N/A",
        )

    # Resolve storage condition
    storage = storage_condition if storage_condition != "unknown" else "room_temp"
    cut_key = whole_or_cut if whole_or_cut in ("whole", "cut") else "whole"

    try:
        min_d, max_d, notes = SHELF_LIFE_REFERENCE[food_key][storage][cut_key]
    except KeyError:
        # Fall back to whole if cut data is missing
        try:
            min_d, max_d, notes = SHELF_LIFE_REFERENCE[food_key][storage]["whole"]
        except KeyError:
            return ShelfLifeResult(
                available=False,
                message="Shelf-life reference data is incomplete for this combination.",
                method="N/A",
            )

    assumptions = (
        f"Storage: {'refrigerated (1–4 °C)' if storage == 'refrigerated' else 'room temperature (~20 °C)'}. "
        f"Condition: {cut_key}. {notes}"
    )
    if storage_condition == "unknown":
        assumptions += " Storage condition was not provided; room-temperature estimate used as a conservative default."

    # Adjust for freshness
    if freshness_label == "Moderately Fresh":
        # Food is partway through its range; estimate mid-to-lower remaining life
        min_d = max(0, min_d // 2)
        max_d = max(0, max_d // 2)
        assumptions += " Adjusted for 'Moderately Fresh' classification (lower half of range)."

    # Deduct elapsed days
    remaining_min = min_d
    remaining_max = max_d
    if days_since_purchase is not None and days_since_purchase > 0:
        remaining_min = max(0, min_d - int(days_since_purchase))
        remaining_max = max(0, max_d - int(days_since_purchase))
        assumptions += f" {int(days_since_purchase)} day(s) elapsed deducted from reference range."

    if remaining_max <= 0:
        return ShelfLifeResult(
            available=True,
            min_days=min_d,
            max_days=max_d,
            remaining_min=0,
            remaining_max=0,
            method="Reference-based estimate (USDA/FDA guidance)",
            assumptions=assumptions,
            message="Based on elapsed time and reference data, quality may be at or past its limit.",
        )

    return ShelfLifeResult(
        available=True,
        min_days=min_d,
        max_days=max_d,
        remaining_min=remaining_min,
        remaining_max=remaining_max,
        method="Reference-based estimate (USDA/FDA guidance)",
        assumptions=assumptions,
        message=f"Estimated {remaining_min}–{remaining_max} day(s) remaining.",
    )


def get_supported_foods() -> list[str]:
    return sorted(SHELF_LIFE_REFERENCE.keys())
