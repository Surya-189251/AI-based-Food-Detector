"""
ML model service.

Loads a Keras model from disk and exposes a single `predict()` entry-point.
If the model file is absent the service degrades gracefully — all predictions
return a "Model not configured" status rather than crashing.

Architecture: MobileNetV2 fine-tuned on a fruits freshness dataset.
Expected labels file: JSON mapping class index (str) -> label string.

Example labels.json:
{
  "0": "apple_fresh",
  "1": "apple_spoiled",
  "2": "banana_fresh",
  "3": "banana_spoiled",
  "4": "orange_fresh",
  "5": "orange_spoiled"
}

Label naming convention: "<food>_<freshness>" where freshness is one of
  fresh | moderately_fresh | spoiled

The model is loaded once at startup and cached in memory.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Label mapping helpers
# ---------------------------------------------------------------------------

FOOD_ALIASES: dict[str, str] = {
    "apple": "apple",
    "banana": "banana",
    "orange": "orange",
}

FRESHNESS_DISPLAY: dict[str, str] = {
    "fresh": "Fresh",
    "moderately_fresh": "Moderately Fresh",
    "spoiled": "Spoiled",
}


def parse_label(raw_label: str) -> tuple[str, str]:
    """
    Split a raw label like "apple_fresh" into (food_type, freshness_key).
    Returns ("unknown", "unknown") if the format is unrecognised.
    """
    parts = raw_label.lower().split("_", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return "unknown", raw_label


# ---------------------------------------------------------------------------
# Prediction result dataclass
# ---------------------------------------------------------------------------

@dataclass
class PredictionResult:
    model_available: bool
    food_type: Optional[str] = None
    food_type_display: Optional[str] = None
    freshness_label: Optional[str] = None        # e.g. "Fresh"
    freshness_key: Optional[str] = None          # e.g. "fresh"
    raw_label: Optional[str] = None
    confidence: Optional[float] = None
    all_scores: dict[str, float] = field(default_factory=dict)
    is_supported: bool = False
    unable_to_assess: bool = False
    message: str = ""
    model_version: str = ""


# ---------------------------------------------------------------------------
# Model singleton
# ---------------------------------------------------------------------------

class FreshCheckModel:
    _instance: Optional["FreshCheckModel"] = None

    def __init__(self):
        self._model = None
        self._labels: dict[str, str] = {}
        self._loaded = False
        self._load_error: Optional[str] = None

    # ------------------------------------------------------------------
    # Singleton access
    # ------------------------------------------------------------------
    @classmethod
    def get_instance(cls) -> "FreshCheckModel":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------
    def load(self) -> None:
        """Attempt to load model and labels from disk. Safe to call multiple times."""
        model_path = settings.MODEL_DIR / settings.MODEL_FILENAME
        labels_path = settings.MODEL_DIR / settings.LABELS_FILENAME

        if not model_path.exists():
            self._load_error = (
                f"Model file not found: {model_path}. "
                "Run the training script first or place a trained .keras file in saved_models/."
            )
            logger.warning(self._load_error)
            return

        if not labels_path.exists():
            self._load_error = (
                f"Labels file not found: {labels_path}. "
                "Ensure labels.json is in saved_models/."
            )
            logger.warning(self._load_error)
            return

        try:
            # Deferred import so the app starts even if TensorFlow isn't installed
            import tensorflow as tf
            self._model = tf.keras.models.load_model(str(model_path))
            with open(labels_path, "r", encoding="utf-8") as f:
                self._labels = json.load(f)
            self._loaded = True
            logger.info(
                "Model loaded from %s with %d classes.", model_path, len(self._labels)
            )
        except Exception as exc:
            self._load_error = f"Failed to load model: {exc}"
            logger.error(self._load_error)

    @property
    def is_ready(self) -> bool:
        return self._loaded and self._model is not None

    @property
    def load_error(self) -> Optional[str]:
        return self._load_error

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------
    def predict(self, preprocessed: np.ndarray) -> PredictionResult:
        """
        Run inference on a preprocessed array (shape 1×H×W×3).
        Returns a PredictionResult with all relevant fields populated.
        """
        if not self.is_ready:
            return PredictionResult(
                model_available=False,
                message=self._load_error or "Model not configured.",
                model_version=settings.MODEL_VERSION,
            )

        try:
            raw_probs = self._model.predict(preprocessed, verbose=0)[0]
        except Exception as exc:
            return PredictionResult(
                model_available=False,
                message=f"Inference error: {exc}",
                model_version=settings.MODEL_VERSION,
            )

        best_idx = int(np.argmax(raw_probs))
        best_prob = float(raw_probs[best_idx])
        raw_label = self._labels.get(str(best_idx), "unknown")

        all_scores = {
            self._labels.get(str(i), str(i)): float(p)
            for i, p in enumerate(raw_probs)
        }

        food_type, freshness_key = parse_label(raw_label)
        freshness_display = FRESHNESS_DISPLAY.get(freshness_key, freshness_key.replace("_", " ").title())

        is_supported = food_type in FOOD_ALIASES
        unable = best_prob < settings.CONFIDENCE_THRESHOLD or not is_supported

        if not is_supported:
            message = (
                f"The food in this image ('{food_type}') is not in the supported category list. "
                "FreshCheck AI currently supports: apples, bananas, and oranges. "
                "Please photograph one of these fruits individually against a clear background."
            )
        elif unable:
            message = (
                f"Model confidence ({best_prob:.0%}) is below the threshold "
                f"({settings.CONFIDENCE_THRESHOLD:.0%}). "
                "Please ensure one supported fruit is clearly visible, well-lit, and in focus."
            )
        else:
            message = ""

        return PredictionResult(
            model_available=True,
            food_type=food_type if is_supported else None,
            food_type_display=food_type.title() if is_supported else None,
            freshness_label=freshness_display if not unable else None,
            freshness_key=freshness_key if not unable else None,
            raw_label=raw_label,
            confidence=best_prob,
            all_scores=all_scores,
            is_supported=is_supported,
            unable_to_assess=unable,
            message=message,
            model_version=settings.MODEL_VERSION,
        )


# Module-level singleton
model_service = FreshCheckModel.get_instance()
