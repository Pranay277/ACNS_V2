# SCIARS Deployment Guide (P2-11)

How to run the platform in production. Everything here is additive to the
existing `README.md` setup instructions — development workflows are unchanged.

---

## 1. Production checklist

| # | Item | Enforced |
|---|------|----------|
| 1 | `ENVIRONMENT=production` | `main.py` fails closed if `CORS_ALLOWED_ORIGINS` is unset |
| 2 | `CORS_ALLOWED_ORIGINS` set to the real frontend origin(s) | `main.py` |
| 3 | `FRONTEND_BASE_URL` = production origin (SMS issue links) | SMS service |
| 4 | `backend/serviceAccountKey.json` present (gitignored) | `start.sh` / compose mount |
| 5 | Firebase **Authentication → Email/Password** enabled | Firebase console |
| 6 | TLS terminated in front of the frontend (HTTPS) | reverse proxy (below) |
| 7 | Exact-pinned backend deps + audited frontend deps | `requirements.txt`, CI |

---

## 2. Environment variables

Backend (`backend/.env`) — copy from `.env.example`:

- `ENVIRONMENT=production`
- `CORS_ALLOWED_ORIGINS=https://app.example.com` (comma-separated; **never `*`**)
- `TEXTBEE_API_KEY`, `TEXTBEE_DEVICE_ID` (SMS gateway)
- `FRONTEND_BASE_URL=https://app.example.com` (no trailing slash)
- `LOG_LEVEL=INFO` (or `DEBUG`); optional `LOG_FORMAT=json` for structured logs
- Optional: `FRESH_AUTH_MAX_AGE_SECONDS` (default `300`), `RATE_LIMIT_*`,
  `SMS_ABUSE_*`

Frontend (`frontend/.env`) — copy from `.env.example`:

- `VITE_API_URL` — `/api` when served behind the Nginx proxy (compose), or the
  deployed backend origin, e.g. `https://api.example.com/api`
- `VITE_FIREBASE_*` — Firebase web app config

---

## 3. Option A — Docker Compose (recommended single-host)

```bash
cd ACNS_v2
cp backend/.env.example backend/.env      # fill in production values
docker compose up --build -d
```

- Frontend → `http://<host>/` (Nginx serves the SPA, proxies `/api` to backend)
- Backend → `http://<host>:8000` (API docs at `/docs`)
- Firebase credentials are mounted read-only from `backend/serviceAccountKey.json`

## 4. Option B — Manual / VM

Backend:

```bash
cd ACNS_v2/backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
ENVIRONMENT=production ./start.sh          # validates config, then uvicorn
```

Frontend:

```bash
cd ACNS_v2/frontend
npm ci
npm run build                              # outputs dist/
```

Serve `dist/` with any static host (Nginx, Caddy, Netlify, Vercel). Point
`VITE_API_URL` at the backend before building.

---

## 5. HTTPS (TLS)

The backend and the compose Nginx container speak HTTP; terminate TLS at the
edge. Example Caddy `Caddyfile` (auto-issues/rotates certs via Let's Encrypt):

```caddyfile
app.example.com {
    reverse_proxy localhost:80          # the Nginx frontend container
}
```

or with Nginx + `certbot`, proxy to the frontend origin. After TLS:

- `CORS_ALLOWED_ORIGINS=https://app.example.com`
- `FRONTEND_BASE_URL=https://app.example.com`
- `VITE_API_URL=/api` (same-origin via the proxy — no CORS traffic at all)

---

## 6. Security operations

- **Token revocation (P2-03):** deactivating an account, resetting a password,
  or changing an email revokes that user's Firebase refresh tokens. Their next
  API call returns 401 and the frontend forces a clean re-login.
- **Fresh-auth guard (P2-03):** deactivate / activate / change-email /
  reset-password / delete require the admin to have signed in within the last
  `FRESH_AUTH_MAX_AGE_SECONDS`. The UI shows a "confirm your identity" prompt.
- **Log hygiene (P2-07):** phone numbers are masked in logs; SMS bodies,
  passwords, and tokens are never logged. Set `LOG_FORMAT=json` for
  machine-parseable structured logs.
- **Password policy (P2-08):** supervisor credentials require ≥ 8 characters
  with upper, lower, digit, and a special character — enforced server-side and
  mirrored in the UI.

---

## 7. CI / supply chain

`.github/workflows/ci.yml` runs on every push/PR:

- Backend: exact-pin install → `pytest` → `pip-audit -r requirements.txt`
- Frontend: `npm ci` → `npm run build` → `npm audit --omit=dev`

Auth-dependent tests skip when `serviceAccountKey.json` is absent (it is
gitignored by design). To run the full suite in CI, provide the service account
as a repository secret and write it to `ACNS_v2/backend/serviceAccountKey.json`
before the test step.

## 8. Health check

```bash
curl -f http://<host>/   # {"message":"SCIARS Backend Running"}
curl -f http://<host>:8000/docs   # interactive API docs
```
