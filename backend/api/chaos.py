from fastapi import APIRouter
from pydantic import BaseModel, Field

from core.telemetry import inject_chaos_event


router = APIRouter()


class ChaosRequest(BaseModel):
    target_container: str = Field(
        default="aegis-edge-tunnel",
        min_length=1,
        max_length=100,
    )


@router.post("/spike")
async def trigger_cpu_spike(
    payload: ChaosRequest,
):
    """
    Simulates a high CPU event for the recruiter dashboard.
    """

    return await inject_chaos_event(
        event_type="spike",
        target_container=payload.target_container,
    )


@router.post("/crash")
async def trigger_service_crash(
    payload: ChaosRequest,
):
    """
    Simulates a fatal service exception and schedules
    debounced RCA + self-healing.
    """

    return await inject_chaos_event(
        event_type="crash",
        target_container=payload.target_container,
    )


@router.post("/attack")
async def trigger_traffic_attack(
    payload: ChaosRequest,
):
    """
    Simulates an abnormal traffic/resource event.
    """

    return await inject_chaos_event(
        event_type="attack",
        target_container=payload.target_container,
    )