from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth, gamification, issues, navigation, notifications

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
app.include_router(auth.router, prefix="/api/auth", tags=["Auth & Users"])
app.include_router(issues.router, prefix="/api/issues", tags=["Issues"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(navigation.router, prefix="/api/navigation", tags=["Navigation"])
app.include_router(gamification.router, prefix="/api/gamification", tags=["Gamification"])


@app.get("/")
def root():
    return {"message": "SCIARS Backend Running"}
