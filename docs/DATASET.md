# Dataset Setup Guide

## Recommended Dataset

**Name:** Fruits fresh and rotten for classification  
**Author:** Sriram Reddy  
**Kaggle URL:** https://www.kaggle.com/datasets/sriramr/fruits-fresh-and-rotten-for-classification  
**License:** See Kaggle dataset page for current terms. This dataset is listed as available for academic use; verify before any commercial or non-academic use.

### What the dataset contains

| Class | Images (approx.) |
|-------|-----------------|
| Fresh apples   | ~1,693 |
| Rotten apples  | ~2,342 |
| Fresh bananas  | ~1,581 |
| Rotten bananas | ~2,224 |
| Fresh oranges  | ~1,466 |
| Rotten oranges | ~1,595 |

**Total: ~10,901 images** split into `train/` and `test/` subdirectories.

### What the dataset does NOT contain

- A "Moderately Fresh" class — the classifier will output Fresh or Spoiled only.
- Cooked foods, dairy, meat, or mixed dishes.
- Multiple fruits in one image.

To add a "Moderately Fresh" class you would need additional labeled images of fruits in intermediate ripeness stages (e.g., banana with some black spots but still edible). These images are not freely available in a ready-made dataset and would need to be collected and labeled manually.

---

## Download Instructions

### Option A — Kaggle CLI (recommended)

```powershell
# Install Kaggle CLI
pip install kaggle

# Set up your API key:
# 1. Go to https://www.kaggle.com/account
# 2. Click "Create New API Token" → downloads kaggle.json
# 3. Place kaggle.json at: C:\Users\<YourName>\.kaggle\kaggle.json

# Download and unzip (run from backend/)
kaggle datasets download -d sriramr/fruits-fresh-and-rotten-for-classification
Expand-Archive -Path fruits-fresh-and-rotten-for-classification.zip -DestinationPath ml\dataset
Remove-Item fruits-fresh-and-rotten-for-classification.zip
```

### Option B — Manual download

1. Log in to Kaggle.
2. Go to https://www.kaggle.com/datasets/sriramr/fruits-fresh-and-rotten-for-classification
3. Click **Download** → downloads a ZIP file.
4. Extract the ZIP so that the structure is:

```
backend/ml/dataset/
├── train/
│   ├── freshapples/
│   ├── rottenapples/
│   ├── freshbananas/
│   ├── rottenbananas/
│   ├── freshoranges/
│   └── rottenoranges/
└── test/
    ├── freshapples/
    ├── rottenapples/
    ├── freshbananas/
    ├── rottenbananas/
    ├── freshoranges/
    └── rottenoranges/
```

---

## Label Remapping

The training script automatically renames Kaggle folder names to canonical labels:

| Kaggle folder name | Canonical label |
|--------------------|----------------|
| freshapples        | apple_fresh    |
| rottenapples       | apple_spoiled  |
| freshbananas       | banana_fresh   |
| rottenbananas      | banana_spoiled |
| freshoranges       | orange_fresh   |
| rottenoranges      | orange_spoiled |

The resulting `labels.json` will be:
```json
{
  "0": "apple_fresh",
  "1": "apple_spoiled",
  "2": "banana_fresh",
  "3": "banana_spoiled",
  "4": "orange_fresh",
  "5": "orange_spoiled"
}
```

---

## Duplicate Check

The training script computes MD5 hashes of all training images and reports any duplicates.
Images of the same physical fruit shot at different times can cause data leakage (inflated accuracy).
If you collect your own images, use the duplicate-check output to identify and remove near-duplicates
before training.

---

## Extending the Dataset

To add more fruit types later:

1. Create new subdirectories under `ml/dataset/train/` and `ml/dataset/test/` named `<food>_fresh` and `<food>_spoiled` (and optionally `<food>_moderately_fresh`).
2. Add a `FOLDER_TO_LABEL` entry in `ml/training/train.py` if needed.
3. Add shelf-life reference data for the new food in `app/services/shelf_life.py`.
4. Re-train and re-evaluate the model.
5. Restart the backend to load the new model.

---

## Accuracy Expectations

On the Kaggle dataset, fine-tuned MobileNetV2 models typically achieve:
- Training accuracy: ~97–99 %
- Test accuracy: ~95–98 %
- Macro F1: ~0.95–0.98

**Do not quote these as guaranteed results.** Actual metrics depend on your hardware, random seed,
augmentation settings, and training duration. Always run `evaluate.py` and report your own measured
numbers.
