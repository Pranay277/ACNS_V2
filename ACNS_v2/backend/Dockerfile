# SCIARS backend — production image (P2-11).
#
# Build:      docker build -t sciars-backend .
# Run:        docker run --env-file .env -v "$PWD/serviceAccountKey.json:/app/serviceAccountKey.json:ro" -p 8000:8000 sciars-backend
#
# Environment is injected at runtime (never baked in): ENVIRONMENT,
# CORS_ALLOWED_ORIGINS, TEXTBEE_*, FRONTEND_BASE_URL, LOG_LEVEL, etc. come from
# `--env-file` / compose. The Firebase service account JSON is mounted read-only
# because it is gitignored and must never be layered into an image.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencies first — exact pins from requirements.txt (P2-05) make the layer
# reproducible, and this ordering keeps the layer cached across code changes.
COPY requirements.txt ./
RUN pip install --no-cache-dir --requirement requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--proxy-headers", "--forwarded-allow-ips=*"]
