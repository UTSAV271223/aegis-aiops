from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from backend.core.config import settings
from backend.api import auth
from backend.api.deps import get_current_user
from backend.schemas.auth import TokenData

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Aegis Autonomous Infrastructure Telemetry & Self-Healing API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")

@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    return {"status": "online", "system": "Aegis Telemetry Engine"}

@app.get("/api/v1/protected-test", tags=["Telemetry"])
async def protected_test(current_user: TokenData = Depends(get_current_user)):
    return {
        "message": "Access Granted to Telemetry Engine",
        "authenticated_user": current_user.username
    }