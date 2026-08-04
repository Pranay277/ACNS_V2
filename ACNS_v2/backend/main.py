from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import (
    CORS_ALLOWED_ORIGINS,
    DEFAULT_CORS_ORIGINS,
    DEV_ENVIRONMENTS,
    ENVIRONMENT,
)
from core.logging import configure_logging
from features.auth.router import router as auth_router
from features.gamification.router import router as gamification_router
from features.issues.router import router as issues_router
from features.navigation.router import router as navigation_router
from features.notifications.router import router as notifications_router
from features.supervisors.router import router as supervisors_router

configure_logging()

app = FastAPI()

# CORS — allow-list only. The wildcard "*" is never used with credentials.
# Origins come from CORS_ALLOWED_ORIGINS (backend/.env, comma-separated). In
# development/local the local Vite origins are used as a default so the
# frontend keeps working; in production the variable is mandatory (fail-closed).
if CORS_ALLOWED_ORIGINS:
    cors_origins = CORS_ALLOWED_ORIGINS
elif ENVIRONMENT in DEV_ENVIRONMENTS:
    cors_origins = list(DEFAULT_CORS_ORIGINS)
else:
    raise RuntimeError(
        "CORS_ALLOWED_ORIGINS must be set in the production environment "
        "(comma-separated list, e.g. "
        "CORS_ALLOWED_ORIGINS=https://app.example.com). Refusing to start with "
        "an open or empty CORS configuration."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router, prefix="/api/auth", tags=["Auth & Users"])
app.include_router(issues_router, prefix="/api/issues", tags=["Issues"])
app.include_router(notifications_router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(navigation_router, prefix="/api/navigation", tags=["Navigation"])
app.include_router(gamification_router, prefix="/api/gamification", tags=["Gamification"])
app.include_router(supervisors_router, prefix="/api/supervisors", tags=["Supervisors"])


@app.get("/")
def root():
    return {"message": "SCIARS Backend Running"}
