# FreshCheck AI
## AI-Based Food Freshness Detection and Shelf-Life Prediction Using Image Processing

An academic college project demonstrating MobileNetV2 transfer learning for visible fruit freshness classification.

---

## ⚠️ Important Notices

- This tool assesses **visible** freshness only. It **cannot** detect bacteria, toxins, or internal spoilage.
- No pre-trained model weights are included. You must train the model (see [Training](#training)) before real predictions work.
- Without trained weights the app is fully functional but returns **"Model not configured"** for all scans.
- Shelf-life estimates are **reference-based** (USDA/FDA guidance), not model-predicted.

---

## Project Structure

```
AI based Food Detector/
├── backend/
│   ├── app/
│   │   ├── main.py              ← FastAPI entry point
│   │   ├── config.py            ← Settings (env vars)
│   │   ├── database.py          ← SQLite init & helpers
│   │   ├── routers/
│   │   │   ├── health.py        ← GET  /api/health
│   │   │   ├── foods.py         ← GET  /api/foods
│   │   │   ├── analysis.py      ← POST /api/analyze
│   │   │   └── history.py       ← GET/DELETE /api/history
│   │   ├── services/
│   │   │   ├── model_service.py ← ML model loader & predictor
│   │   │   └── shelf_life.py    ← Shelf-life reference estimator
│   │   └── utils/
│   │       └── image_processing.py ← Pillow + OpenCV preprocessing
│   ├── ml/
│   │   ├── training/train.py    ← Training script
│   │   └── evaluation/evaluate.py ← Evaluation script
│   ├── saved_models/            ← Place trained .keras + labels.json here
│   ├── data/
│   │   ├── uploads/             ← Uploaded images (auto-created)
│   │   └── db/freshcheck.db     ← SQLite database (auto-created)
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/               ← Home, Scan, History, About
│   │   ├── components/          ← Navbar, Footer, CameraCapture, ResultsCard
│   │   └── utils/               ← api.js, helpers.js, constants.js
│   ├── package.json
│   ├── vite.config.js
│   └── .env.example
├── docs/
│   ├── DATASET.md               ← Dataset setup guide
│   └── DEPLOYMENT.md            ← Deployment / HTTPS notes
└── README.md
```

---

## Prerequisites

| Tool | Minimum version | Install |
|------|----------------|---------|
| Python | 3.11 | https://www.python.org/downloads/ |
| Node.js | 18 LTS | https://nodejs.org/ |
| npm | 9+ | Included with Node.js |
| Git | any | https://git-scm.com/ |

---

## Quick Start — Windows PowerShell

### 1. Backend setup

```powershell
# Navigate to the backend folder
cd "backend"

# Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# If you see an execution policy error, run first:
# Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

# Install dependencies
pip install -r requirements.txt

# Copy environment file
Copy-Item .env.example .env

# Start the backend (development mode)
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend is now at http://localhost:8000
API docs at http://localhost:8000/docs

### 2. Frontend setup (new PowerShell window)

```powershell
# Navigate to the frontend folder
cd "frontend"

# Install Node packages
npm install

# Copy environment file
Copy-Item .env.example .env

# Start the frontend dev server
npm run dev
```

Frontend is now at http://localhost:5173

Open http://localhost:5173 in your browser.

---

## Training the Model

Without training, the app returns "Model not configured" for all scans.
See **[docs/DATASET.md](docs/DATASET.md)** for full dataset download and setup instructions.

### Quick steps

```powershell
# From the backend/ folder with venv active:

# 1. Download the dataset (see docs/DATASET.md)
#    Place it so that: backend/ml/dataset/train/ exists

# 2. Train (about 20–40 minutes on CPU; faster on GPU)
python -m ml.training.train --dataset_dir ml/dataset --output_dir saved_models --epochs 20

# 3. Evaluate
python -m ml.evaluation.evaluate `
    --model_path saved_models/freshcheck_model.keras `
    --labels_path saved_models/labels.json `
    --test_dir ml/dataset/test `
    --output_dir ml/evaluation/results

# 4. Restart the backend — it will load the new model automatically
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

---

## Testing the Camera on a Real Phone

Browser camera access requires **HTTPS or localhost**. On localhost (your laptop), it works
automatically. To test on a phone on the same Wi-Fi network:

**Option A — ngrok (easiest)**
```powershell
# Install ngrok: https://ngrok.com/download
# In a separate terminal:
ngrok http 5173
# Use the https://xxxx.ngrok-free.app URL on your phone
```

**Option B — Vite HTTPS + mkcert**
```powershell
npm install -D @vitejs/plugin-basic-ssl
# Add plugin to vite.config.js (see docs/DEPLOYMENT.md)
npm run dev -- --host
# Accept the self-signed certificate warning on your phone
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | App and model status |
| GET | `/api/foods` | Supported food categories |
| POST | `/api/analyze` | Analyse an image |
| GET | `/api/history` | Retrieve analysis history |
| DELETE | `/api/history/{id}` | Delete one record |
| DELETE | `/api/history` | Clear all history |
| GET | `/uploads/{filename}` | Serve uploaded images |

Full interactive docs: http://localhost:8000/docs

---

## What Is and Is Not Working

### ✅ Working now (no training required)
- Complete frontend with all 4 pages
- Camera capture (live viewfinder, capture, retake, front/rear switch)
- Image upload with client + server validation
- Image quality checks (blur, brightness, dimensions, EXIF rotation)
- Shelf-life reference estimation (USDA/FDA)
- SQLite history (create, view, delete individual, clear all)
- All API endpoints (health, foods, analyze, history)
- Graceful degradation when model is missing

### ⚠️ Requires training data + model weights
- Real freshness classification (returns "Model not configured" until trained)
- Confidence scores based on actual training
- Evaluation metrics, confusion matrix, F1 scores

### 📝 Things not tested in this environment
- Physical phone camera behaviour (requires a real device + HTTPS)
- GPU-accelerated training (tested on CPU logic only)
- Training on the actual Kaggle dataset (requires Kaggle account + download)

---

## Commands Reference

```powershell
# Activate backend venv
.\backend\venv\Scripts\Activate.ps1

# Run backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Run frontend
npm --prefix frontend run dev

# Train model
python -m ml.training.train

# Evaluate model
python -m ml.evaluation.evaluate

# Build frontend for production
npm --prefix frontend run build
```

---

## License & Dataset Attribution

- Application code: MIT License (academic use)
- Training dataset: "Fruits fresh and rotten for classification" — Sriram Reddy, Kaggle
  https://www.kaggle.com/datasets/sriramr/fruits-fresh-and-rotten-for-classification
  Check the Kaggle dataset page for current license terms before any non-academic use.
- Shelf-life reference data: USDA FoodKeeper App / FDA Food Safety guidelines (public domain)
