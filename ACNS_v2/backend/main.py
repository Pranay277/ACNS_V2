from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.logging import configure_logging
from features.auth.router import router as auth_router
from features.gamification.router import router as gamification_router
from features.issues.router import router as issues_router
from features.navigation.router import router as navigation_router
from features.notifications.router import router as notifications_router
from features.supervisors.router import router as supervisors_router

configure_logging()

app = FastAPI()

# CORS (IMPORTANT for frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later restrict
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
