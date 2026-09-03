import asyncio
from fastapi import FastAPI, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Core & Configuration Imports
from core.config import settings
from core.limiter import limiter
from api import auth
from api.deps import get_current_user
from schemas.auth import TokenData

# Telemetry & WebSocket Imports
from core.telemetry import metric_collector_thread, ml_inference_loop, telemetry_buffer
from core.ws_manager import manager

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
    # Launches the 15-second ML inference loop for Groq RCA (Day 18)
    asyncio.create_task(ml_inference_loop())
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
        "metrics": list(telemetry_buffer) 
    }

# --- DAY 14 ROUTE: REAL-TIME WEBSOCKET STREAMING ---
@app.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    """
    Day 14 Endpoint: Establishes a persistent, full-duplex WebSocket 
    connection streaming live telemetry metrics every 3 seconds.
    """
    await manager.connect(websocket)
    try:
        while True:
            payload = {
                "event": "TELEMETRY_UPDATE",
                "buffer_size": len(telemetry_buffer),
                "data": list(telemetry_buffer)
            }
            await websocket.send_json(payload)
            await asyncio.sleep(3)
    except WebSocketDisconnect:
        manager.disconnect(websocket)