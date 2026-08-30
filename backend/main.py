import asyncio
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.core.config import settings
from backend.core.limiter import limiter
from backend.api import auth
from backend.api.deps import get_current_user
from backend.schemas.auth import TokenData

# Import the collector thread AND the new ring buffer
from backend.core.telemetry import metric_collector_thread, telemetry_buffer

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Aegis Autonomous Infrastructure Telemetry & Self-Healing API"
)

# Attach SlowAPI Rate Limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS for Vercel Frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Authentication Router
app.include_router(auth.router, prefix="/api/v1")

# --- STARTUP EVENT ---
@app.on_event("startup")
async def startup_event():
    # Launches the 3-second Docker SDK metric collector in the background
    asyncio.create_task(metric_collector_thread())
# ---------------------

# --- CORE ROUTES ---
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

# --- DAY 13 ROUTE ---
@app.get("/api/v1/telemetry/buffer", tags=["Telemetry"])
@limiter.limit("30/minute")
async def get_telemetry_buffer(request: Request, current_user: TokenData = Depends(get_current_user)):
    """
    Day 13 Verification Route: Inspects the in-memory ring buffer.
    """
    return {
        "buffer_capacity": 100,
        "current_size": len(telemetry_buffer),
        # Convert the deque to a standard Python list so FastAPI can return it as JSON
        "metrics": list(telemetry_buffer) 
    }