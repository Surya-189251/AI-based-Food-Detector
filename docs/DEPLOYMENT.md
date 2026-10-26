# Deployment Notes

## Camera Access and HTTPS

Browser camera access (the Web `getUserMedia` API) requires a **secure context**:
- ✅ `http://localhost` — always a secure context.
- ✅ `https://` — any HTTPS origin.
- ❌ `http://` on any non-localhost host — camera blocked by browsers.

### Testing on a real phone (same Wi-Fi network)

**Option A — ngrok (recommended for quick testing)**

```powershell
# 1. Download ngrok from https://ngrok.com/download
# 2. Create a free account and run:
ngrok config add-authtoken <your-token>

# 3. Expose the frontend dev server
ngrok http 5173

# ngrok prints an https://xxxx.ngrok-free.app URL
# Open that URL on your phone — camera will work
```

**Option B — Vite built-in HTTPS**

```powershell
# Install the plugin
npm install -D @vitejs/plugin-basic-ssl
```

Add to `frontend/vite.config.js`:
```js
import basicSsl from '@vitejs/plugin-basic-ssl'

export default defineConfig({
  plugins: [react(), basicSsl()],
  server: { port: 5173, host: true },
})
```

```powershell
npm run dev -- --host
```

Your phone will show a certificate warning. Accept it (this is a self-signed cert for development).

**Option C — mkcert (trusted local CA)**

```powershell
# Install mkcert: https://github.com/FiloSottile/mkcert
choco install mkcert        # or winget install mkcert
mkcert -install
mkcert localhost 127.0.0.1  # creates localhost.pem + localhost-key.pem
```

Then configure Vite to use those files (see Vite docs for `server.https`).

---

## Backend Hosting Options

### Development (local)
```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Network-accessible (for phone testing)
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Then access via `http://<your-PC-IP>:8000` (camera won't work without HTTPS, see above).

### Production
Recommended stack:
- **Reverse proxy:** Nginx or Caddy (handles HTTPS/TLS automatically with Caddy)
- **Process manager:** systemd or Supervisor
- **Example Caddy config:**

```caddy
your-domain.com {
    reverse_proxy localhost:8000
}
```

---

## Frontend Production Build

```powershell
cd frontend
npm run build
# Static files output to: frontend/dist/
```

Serve `frontend/dist/` from your backend (add `StaticFiles` mount in `app/main.py`),
from Nginx, or from a CDN.

Set the correct backend URL before building:
```
# frontend/.env
VITE_API_BASE_URL=https://your-backend.example.com
```

---

## Persistent Storage

- **SQLite database:** `backend/data/db/freshcheck.db` — back this up regularly.
- **Uploaded images:** `backend/data/uploads/` — size grows over time; implement periodic cleanup.
- On cloud VMs, mount a persistent volume to `backend/data/`.

---

## CORS

In production, update `ALLOWED_ORIGINS` in `backend/.env` to your exact frontend URL:
```
ALLOWED_ORIGINS=https://your-frontend.example.com
```
Avoid `*` in production.

---

## Environment Variables Checklist

| Variable | Development | Production |
|----------|-------------|------------|
| `DEBUG` | `true` | `false` |
| `ALLOWED_ORIGINS` | `http://localhost:5173` | Your frontend URL |
| `CONFIDENCE_THRESHOLD` | `0.60` | Tune after evaluation |
| `MODEL_VERSION` | `1.0.0` | Update after retraining |

---

## Security Notes (academic prototype)

- No authentication is implemented. This is acceptable for a single-user academic prototype.
- For any shared/public deployment, add authentication (e.g., FastAPI + JWT or session cookies).
- Never log raw image bytes or user secrets.
- Uploaded files are stored with UUID-generated names to prevent path traversal.
- Server-side MIME validation rejects files that don't decode as valid images.
