"""
FreshCheck AI — Training Script
================================
Trains a MobileNetV2-based binary/multi-class freshness classifier using
transfer learning on a fruits-freshness dataset.

DATASET
-------
Recommended: "Fruits fresh and rotten for classification" by Sriram Reddy
  Kaggle: https://www.kaggle.com/datasets/sriramr/fruits-fresh-and-rotten-for-classification
  License: Open (see Kaggle dataset page for current terms)
  Supported labels: apple_fresh, apple_spoiled, banana_fresh, banana_spoiled,
                    orange_fresh, orange_spoiled  (6 classes)
  Note: The dataset does NOT include a "Moderately Fresh" class.
        The classifier will therefore report only Fresh or Spoiled for these fruits.
        To add Moderately Fresh, you need additional labeled images showing fruit
        in intermediate stages, collected or annotated separately.

Expected directory structure after download and unzip:
  ml/dataset/
    train/
      freshapples/
      rottenapples/
      freshbananas/
      rottenbananas/
      freshoranges/
      rottenoranges/
    test/
      (same structure)

The script renames those folder names to canonical labels:
  freshapples   -> apple_fresh
  rottenapples  -> apple_spoiled
  etc.

HOW TO RUN
----------
  cd backend
  python -m ml.training.train --dataset_dir ml/dataset --output_dir saved_models --epochs 20

Requirements: TensorFlow 2.16+, scikit-learn, numpy, pillow
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import random
import shutil
from collections import defaultdict
from pathlib import Path

import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Label remapping (Kaggle dataset folder names → canonical labels)
# ---------------------------------------------------------------------------
FOLDER_TO_LABEL: dict[str, str] = {
    "freshapples":   "apple_fresh",
    "rottenapples":  "apple_spoiled",
    "freshbananas":  "banana_fresh",
    "rottenbananas": "banana_spoiled",
    "freshoranges":  "orange_fresh",
    "rottenoranges": "orange_spoiled",
    # Allow already-renamed folders
    "apple_fresh":   "apple_fresh",
    "apple_spoiled": "apple_spoiled",
    "banana_fresh":  "banana_fresh",
    "banana_spoiled":"banana_spoiled",
    "orange_fresh":  "orange_fresh",
    "orange_spoiled":"orange_spoiled",
}

IMG_SIZE = (224, 224)
BATCH_SIZE = 32
SEED = 42


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def file_hash(path: Path) -> str:
    """MD5 of file bytes — used for duplicate detection."""
    md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            md5.update(chunk)
    return md5.hexdigest()


def remap_dataset_folders(dataset_dir: Path) -> None:
    """
    Rename Kaggle-style folder names to canonical label names in-place.
    Idempotent — already-renamed folders are skipped.
    """
    for split in ("train", "test"):
        split_dir = dataset_dir / split
        if not split_dir.exists():
            continue
        for folder in list(split_dir.iterdir()):
            canonical = FOLDER_TO_LABEL.get(folder.name.lower())
            if canonical and folder.name != canonical:
                target = split_dir / canonical
                if not target.exists():
                    folder.rename(target)
                    logger.info("Renamed %s → %s", folder, target)


def scan_images(folder: Path) -> list[Path]:
    exts = {".jpg", ".jpeg", ".png", ".webp"}
    return [p for p in folder.rglob("*") if p.suffix.lower() in exts and p.is_file()]


def check_duplicates(image_paths: list[Path]) -> int:
    """Log duplicate count and return number of duplicates found."""
    hashes: dict[str, list[Path]] = defaultdict(list)
    for p in image_paths:
        hashes[file_hash(p)].append(p)
    dupes = {h: paths for h, paths in hashes.items() if len(paths) > 1}
    if dupes:
        logger.warning("%d duplicate image hash(es) found:", len(dupes))
        for h, paths in list(dupes.items())[:5]:
            logger.warning("  %s: %s", h[:8], [str(p) for p in paths])
    return len(dupes)


# ---------------------------------------------------------------------------
# Main training function
# ---------------------------------------------------------------------------

def train(dataset_dir: Path, output_dir: Path, epochs: int, fine_tune_epochs: int) -> None:
    try:
        import tensorflow as tf
        from tensorflow import keras
        from tensorflow.keras import layers
        from tensorflow.keras.applications import MobileNetV2
        from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
        from sklearn.model_selection import StratifiedShuffleSplit
    except ImportError as exc:
        logger.error("Required package missing: %s", exc)
        raise

    tf.random.set_seed(SEED)
    np.random.seed(SEED)
    random.seed(SEED)

    # ---- 1. Remap folders ------------------------------------------------
    remap_dataset_folders(dataset_dir)

    train_dir = dataset_dir / "train"
    test_dir  = dataset_dir / "test"
    if not train_dir.exists():
        raise FileNotFoundError(f"Train directory not found: {train_dir}")

    # ---- 2. Duplicate check on training data -----------------------------
    all_train_images = scan_images(train_dir)
    logger.info("Total training images found: %d", len(all_train_images))
    check_duplicates(all_train_images)

    # ---- 3. Build ImageDataGenerators ------------------------------------
    from tensorflow.keras.preprocessing.image import ImageDataGenerator

    train_datagen = ImageDataGenerator(
        preprocessing_function=tf.keras.applications.mobilenet_v2.preprocess_input,
        rotation_range=20,
        width_shift_range=0.1,
        height_shift_range=0.1,
        shear_range=0.1,
        zoom_range=0.15,
        horizontal_flip=True,
        brightness_range=[0.8, 1.2],
        validation_split=0.15,
    )

    val_datagen = ImageDataGenerator(
        preprocessing_function=tf.keras.applications.mobilenet_v2.preprocess_input,
        validation_split=0.15,
    )

    train_gen = train_datagen.flow_from_directory(
        train_dir,
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        subset="training",
        seed=SEED,
        shuffle=True,
    )

    val_gen = val_datagen.flow_from_directory(
        train_dir,
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        subset="validation",
        seed=SEED,
        shuffle=False,
    )

    num_classes = len(train_gen.class_indices)
    logger.info("Classes (%d): %s", num_classes, train_gen.class_indices)

    # ---- 4. Build model --------------------------------------------------
    base_model = MobileNetV2(
        input_shape=(*IMG_SIZE, 3),
        include_top=False,
        weights="imagenet",
    )
    base_model.trainable = False   # Phase 1: train head only

    inputs  = keras.Input(shape=(*IMG_SIZE, 3))
    x       = base_model(inputs, training=False)
    x       = layers.GlobalAveragePooling2D()(x)
    x       = layers.Dropout(0.3)(x)
    x       = layers.Dense(256, activation="relu")(x)
    x       = layers.Dropout(0.2)(x)
    outputs = layers.Dense(num_classes, activation="softmax")(x)
    model   = keras.Model(inputs, outputs)

    model.compile(
        optimizer=keras.optimizers.Adam(1e-3),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    ckpt_path = str(output_dir / "best_head.keras")

    callbacks_phase1 = [
        EarlyStopping(patience=5, restore_best_weights=True, monitor="val_accuracy"),
        ModelCheckpoint(ckpt_path, save_best_only=True, monitor="val_accuracy"),
        ReduceLROnPlateau(factor=0.5, patience=3, min_lr=1e-6),
    ]

    # ---- 5. Phase 1 training ---------------------------------------------
    logger.info("Phase 1: training head only (%d epochs max) …", epochs)
    model.fit(train_gen, validation_data=val_gen, epochs=epochs, callbacks=callbacks_phase1)

    # ---- 6. Phase 2: fine-tune last 50 layers ----------------------------
    logger.info("Phase 2: fine-tuning last 50 layers (%d epochs max) …", fine_tune_epochs)
    base_model.trainable = True
    for layer in base_model.layers[:-50]:
        layer.trainable = False

    model.compile(
        optimizer=keras.optimizers.Adam(1e-5),   # lower LR for fine-tuning
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    ckpt_path2 = str(output_dir / "best_finetune.keras")
    callbacks_phase2 = [
        EarlyStopping(patience=5, restore_best_weights=True, monitor="val_accuracy"),
        ModelCheckpoint(ckpt_path2, save_best_only=True, monitor="val_accuracy"),
        ReduceLROnPlateau(factor=0.5, patience=3, min_lr=1e-7),
    ]
    model.fit(train_gen, validation_data=val_gen, epochs=fine_tune_epochs, callbacks=callbacks_phase2)

    # ---- 7. Save final model and labels ----------------------------------
    final_path = output_dir / "freshcheck_model.keras"
    model.save(str(final_path))
    logger.info("Model saved → %s", final_path)

    # Class index → label name mapping (index as string for JSON compatibility)
    index_to_label = {str(v): k for k, v in train_gen.class_indices.items()}
    labels_path = output_dir / "labels.json"
    with open(labels_path, "w") as f:
        json.dump(index_to_label, f, indent=2)
    logger.info("Labels saved → %s", labels_path)

    # ---- 8. Quick validation accuracy ------------------------------------
    logger.info("Evaluating on validation set …")
    val_loss, val_acc = model.evaluate(val_gen, verbose=1)
    logger.info("Validation  loss=%.4f  accuracy=%.4f", val_loss, val_acc)

    if test_dir.exists():
        test_datagen = ImageDataGenerator(
            preprocessing_function=tf.keras.applications.mobilenet_v2.preprocess_input
        )
        test_gen = test_datagen.flow_from_directory(
            test_dir,
            target_size=IMG_SIZE,
            batch_size=BATCH_SIZE,
            class_mode="categorical",
            shuffle=False,
        )
        test_loss, test_acc = model.evaluate(test_gen, verbose=1)
        logger.info("Test        loss=%.4f  accuracy=%.4f", test_loss, test_acc)
    else:
        logger.warning("No test/ directory found — skipping test-set evaluation.")

    logger.info("Training complete.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train FreshCheck AI freshness classifier")
    parser.add_argument("--dataset_dir",    type=Path, default=Path("ml/dataset"),   help="Root dataset dir (must contain train/ and optionally test/)")
    parser.add_argument("--output_dir",     type=Path, default=Path("saved_models"), help="Where to write model files")
    parser.add_argument("--epochs",         type=int,  default=20,  help="Max epochs for head-only phase")
    parser.add_argument("--fine_tune_epochs", type=int, default=10, help="Max epochs for fine-tune phase")
    args = parser.parse_args()

    train(
        dataset_dir=args.dataset_dir,
        output_dir=args.output_dir,
        epochs=args.epochs,
        fine_tune_epochs=args.fine_tune_epochs,
    )
