#!/usr/bin/env bash
# SCIARS backend startup (P2-11).
#
# Verifies the production-critical settings before launching Uvicorn so a
# misconfigured deployment fails fast at boot instead of at first request.
#
#   ./start.sh                 # production defaults (0.0.0.0:8000, LOG_LEVEL=INFO)
#   LOG_LEVEL=DEBUG ./start.sh # override log verbosity
set -euo pipefail

cd "$(dirname "$0")"

if [[ "${ENVIRONMENT:-}" != "production" ]]; then
  echo "start.sh is for production. Run 'ENVIRONMENT=production ./start.sh' or use uvicorn directly for development." >&2
  exit 1
fi

if [[ -z "${CORS_ALLOWED_ORIGINS:-}" ]]; then
  echo "CORS_ALLOWED_ORIGINS must be set in production (comma-separated origins). See .env.example." >&2
  exit 1
fi

if [[ ! -f "serviceAccountKey.json" ]]; then
  echo "serviceAccountKey.json is missing. Place the Firebase service account here (gitignored)." >&2
  exit 1
fi

export LOG_LEVEL="${LOG_LEVEL:-INFO}"

echo "Starting SCIARS backend (ENVIRONMENT=production) on :8000 ..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers "${UVICORN_WORKERS:-2}"
