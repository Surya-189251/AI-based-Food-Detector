This folder is for trained model files.

Place these two files here after training:
  - freshcheck_model.keras   (trained Keras model)
  - labels.json              (class index → label name mapping)

Run the training script first:
  cd backend
  python -m ml.training.train --dataset_dir ml/dataset --output_dir saved_models

See docs/DATASET.md for full instructions.
