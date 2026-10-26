"""
FreshCheck AI — Evaluation Script
===================================
Evaluates a trained model on the held-out test set and produces:
  - Per-class precision, recall, F1
  - Macro F1 score
  - Confusion matrix (saved as PNG)
  - Full classification report (saved as text)

HOW TO RUN
----------
  cd backend
  python -m ml.evaluation.evaluate \
      --model_path saved_models/freshcheck_model.keras \
      --labels_path saved_models/labels.json \
      --test_dir ml/dataset/test \
      --output_dir ml/evaluation/results
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

IMG_SIZE = (224, 224)
BATCH_SIZE = 32


def evaluate(
    model_path: Path,
    labels_path: Path,
    test_dir: Path,
    output_dir: Path,
) -> None:
    try:
        import tensorflow as tf
        from sklearn.metrics import (
            classification_report,
            confusion_matrix,
            f1_score,
        )
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import seaborn as sns
    except ImportError as exc:
        logger.error("Required package missing: %s\nInstall: pip install scikit-learn matplotlib seaborn", exc)
        raise

    # ---- Load model -------------------------------------------------------
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")
    model = tf.keras.models.load_model(str(model_path))
    logger.info("Model loaded from %s", model_path)

    # ---- Load labels -------------------------------------------------------
    with open(labels_path, "r") as f:
        index_to_label: dict[str, str] = json.load(f)
    class_names = [index_to_label[str(i)] for i in range(len(index_to_label))]

    # ---- Build test generator ----------------------------------------------
    test_datagen = tf.keras.preprocessing.image.ImageDataGenerator(
        preprocessing_function=tf.keras.applications.mobilenet_v2.preprocess_input
    )
    test_gen = test_datagen.flow_from_directory(
        test_dir,
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        shuffle=False,
    )

    # ---- Inference ---------------------------------------------------------
    logger.info("Running inference on %d test images …", test_gen.samples)
    y_pred_probs = model.predict(test_gen, verbose=1)
    y_pred = np.argmax(y_pred_probs, axis=1)
    y_true = test_gen.classes

    # ---- Metrics -----------------------------------------------------------
    macro_f1 = f1_score(y_true, y_pred, average="macro")
    logger.info("Macro F1 score: %.4f", macro_f1)

    report_str = classification_report(
        y_true, y_pred, target_names=class_names, digits=4
    )
    logger.info("Classification report:\n%s", report_str)

    # ---- Save results -------------------------------------------------------
    output_dir.mkdir(parents=True, exist_ok=True)

    report_path = output_dir / "classification_report.txt"
    with open(report_path, "w") as f:
        f.write(f"Macro F1 Score: {macro_f1:.4f}\n\n")
        f.write(report_str)
    logger.info("Report saved → %s", report_path)

    # ---- Confusion matrix --------------------------------------------------
    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(max(6, len(class_names)), max(5, len(class_names) - 1)))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Greens",
        xticklabels=class_names,
        yticklabels=class_names,
        ax=ax,
    )
    ax.set_xlabel("Predicted", fontsize=12)
    ax.set_ylabel("Actual", fontsize=12)
    ax.set_title("FreshCheck AI — Confusion Matrix", fontsize=14)
    plt.tight_layout()
    cm_path = output_dir / "confusion_matrix.png"
    fig.savefig(cm_path, dpi=150)
    plt.close(fig)
    logger.info("Confusion matrix saved → %s", cm_path)

    # ---- Per-class summary JSON -------------------------------------------
    from sklearn.metrics import precision_recall_fscore_support

    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, average=None, labels=list(range(len(class_names)))
    )
    per_class = {
        class_names[i]: {
            "precision": float(precision[i]),
            "recall":    float(recall[i]),
            "f1":        float(f1[i]),
            "support":   int(support[i]),
        }
        for i in range(len(class_names))
    }
    summary = {
        "macro_f1": float(macro_f1),
        "per_class": per_class,
    }
    summary_path = output_dir / "metrics.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    logger.info("Metrics JSON saved → %s", summary_path)
    logger.info("Evaluation complete.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate FreshCheck AI model")
    parser.add_argument("--model_path",  type=Path, default=Path("saved_models/freshcheck_model.keras"))
    parser.add_argument("--labels_path", type=Path, default=Path("saved_models/labels.json"))
    parser.add_argument("--test_dir",    type=Path, default=Path("ml/dataset/test"))
    parser.add_argument("--output_dir",  type=Path, default=Path("ml/evaluation/results"))
    args = parser.parse_args()

    evaluate(
        model_path=args.model_path,
        labels_path=args.labels_path,
        test_dir=args.test_dir,
        output_dir=args.output_dir,
    )
