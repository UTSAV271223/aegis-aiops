import os
from contextlib import asynccontextmanager
from typing import Any

import asyncio

from fastapi import (
    Depends,
    FastAPI,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from api import auth
from api import chaos
from api.deps import get_current_user
from core.config import settings
from core.limiter import limiter
from core.telemetry import (
    build_latest_snapshot,
    cancel_incident_tasks,
    metric_collector_thread,
    ml_inference_loop,
    telemetry_buffer,
)
from core.ws_manager import manager
from schemas.auth import TokenData


def _get_allowed_origins() -> list[str]:
    raw_origins = os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    )

    return [
        origin.strip()
        for origin in raw_origins.split(",")
        if origin.strip()
    ]


@asynccontextmanager
async def lifespan(app: FastAPI):

    metric_task = asyncio.create_task(
        metric_collector_thread()
    )

    ml_task = asyncio.create_task(
        ml_inference_loop()
    )

    try:
        yield

    finally:

        cancel_incident_tasks()

        metric_task.cancel()
        ml_task.cancel()

        await asyncio.gather(
            metric_task,
            ml_task,
            return_exceptions=True,
        )


app = FastAPI(
    title=getattr(
        settings,
        "PROJECT_NAME",
        "Aegis AIOps",
    ),
    version="1.0.0",
    description=(
        "Aegis Autonomous Infrastructure "
        "Telemetry & Self-Healing API"
    ),
    lifespan=lifespan,
)


# ============================================================
# RATE LIMITING
# ============================================================

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_allowed_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROUTERS
# ============================================================

app.include_router(
    auth.router,
    prefix="/api/v1",
)

app.include_router(
    chaos.router,
    prefix="/api/v1/chaos",
    tags=["Chaos"],
)


# ============================================================
# HEALTH
# ============================================================

@app.get(
    "/api/v1/health",
    tags=["Health"],
)
@limiter.limit("10/minute")
async def health_check(
    request: Request,
) -> dict[str, str]:

    return {
        "status": "online",
        "system": "Aegis Telemetry Engine",
    }


# ============================================================
# TELEMETRY BUFFER
# ============================================================

@app.get(
    "/api/v1/telemetry/buffer",
    tags=["Telemetry"],
)
@limiter.limit("30/minute")
async def get_telemetry_buffer(
    request: Request,
    current_user: TokenData = Depends(
        get_current_user
    ),
) -> dict[str, Any]:

    return {
        "buffer_capacity": telemetry_buffer.maxlen,
        "current_size": len(
            telemetry_buffer
        ),
        "metrics": list(
            telemetry_buffer
        ),
    }


# ============================================================
# WEBSOCKET TELEMETRY
# ============================================================

@app.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(
    websocket: WebSocket,
):

    await manager.connect(websocket)

    try:

        # Send current state immediately.
        snapshot = build_latest_snapshot()

        if snapshot:

            await websocket.send_json({
                "event": "TELEMETRY_UPDATE",
                "buffer_size": len(
                    telemetry_buffer
                ),
                "data": snapshot,
            })

        # Keep the connection alive and allow FastAPI to
        # detect browser disconnects.
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:

        manager.disconnect(websocket)

    except Exception as error:

        manager.disconnect(websocket)

        print(
            f"[WebSocket] Connection closed: {error}"
        )