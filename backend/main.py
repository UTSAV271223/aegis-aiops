import asyncio # <-- NEW IMPORT
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.core.config import settings
from backend.core.limiter import limiter
from backend.api import auth
from backend.api.deps import get_current_user
from backend.schemas.auth import TokenData
from backend.core.telemetry import metric_collector_thread # <-- NEW IMPORT

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Aegis Autonomous Infrastructure Telemetry & Self-Healing API"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")

# --- NEW STARTUP EVENT ---
@app.on_event("startup")
async def startup_event():
    # Fire and forget the background polling task alongside the API
    asyncio.create_task(metric_collector_thread())
# -------------------------

@app.get("/api/v1/health", tags=["Health"])
@limiter.limit("10/minute")
async def health_check(request: Request):
    return {"status": "online", "system": "Aegis Telemetry Engine"}

@app.get("/api/v1/protected-test", tags=["Telemetry"])
@limiter.limit("20/minute")
async def protected_test(request: Request, current_user: TokenData = Depends(get_current_user)):
    return {
        "message": "Access Granted to Telemetry Engine",
        "authenticated_user": current_user.username
    }