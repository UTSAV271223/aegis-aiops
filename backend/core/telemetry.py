import asyncio
import json
import logging
import time
from collections import deque
from typing import Any

import docker

from ai.anomaly import detect_anomaly
from ai.rca import generate_root_cause_analysis
from core.healing import execute_self_healing
from core.ws_manager import manager


logger = logging.getLogger("Aegis-Telemetry")
logging.basicConfig(level=logging.INFO)


# ============================================================
# CONFIGURATION
# ============================================================

TELEMETRY_INTERVAL_SECONDS = 3
ML_INTERVAL_SECONDS = 15
TELEMETRY_BUFFER_SIZE = 100

# Chaos override durations
CPU_SPIKE_DURATION_SECONDS = 15
CRASH_DURATION_SECONDS = 15
ATTACK_DURATION_SECONDS = 10

# Groq cooldown per container
RCA_COOLDOWN_SECONDS = 600


# ============================================================
# TELEMETRY STATE
# ============================================================

telemetry_buffer = deque(
    maxlen=TELEMETRY_BUFFER_SIZE
)

# Current synthetic Chaos state.
# Key = container name
chaos_overrides: dict[str, dict[str, Any]] = {}

# Prevent repeated RCA calls for the same container.
last_rca_time: dict[str, float] = {}

# One pending debounce task per container.
pending_incidents: dict[str, dict[str, Any]] = {}
incident_tasks: dict[str, asyncio.Task] = {}


# ============================================================
# SNAPSHOT BUILDING
# ============================================================

def _cleanup_expired_overrides() -> None:
    now = time.time()

    expired = [
        name
        for name, override in chaos_overrides.items()
        if override.get("expires_at", 0) <= now
    ]

    for name in expired:
        chaos_overrides.pop(name, None)


def build_latest_snapshot() -> list[dict[str, Any]]:
    """
    Returns the newest metric for every container.

    Active Chaos overrides take precedence over real telemetry
    temporarily so recruiter demonstrations are deterministic.
    """

    _cleanup_expired_overrides()

    latest_by_name: dict[str, dict[str, Any]] = {}

    # Real Docker telemetry
    for metric in telemetry_buffer:
        container_name = metric.get("container_name")

        if container_name:
            latest_by_name[container_name] = dict(metric)

    # Apply active Chaos overrides
    for container_name, override in chaos_overrides.items():

        existing = latest_by_name.get(container_name, {})

        merged = {
            **existing,
            **override.get("metric", {}),
            "container_name": container_name,
        }

        latest_by_name[container_name] = merged

    return list(latest_by_name.values())


async def broadcast_current_snapshot() -> None:
    """
    Send the current telemetry snapshot to all WebSocket clients.
    """

    snapshot = build_latest_snapshot()

    if not snapshot:
        return

    payload = {
        "event": "TELEMETRY_UPDATE",
        "buffer_size": len(telemetry_buffer),
        "data": snapshot,
        "timestamp": time.time(),
    }

    await manager.broadcast_json(payload)


# ============================================================
# CHAOS INJECTION
# ============================================================

async def inject_chaos_event(
    event_type: str,
    target_container: str,
) -> dict[str, Any]:
    """
    Creates a deterministic recruiter-facing Chaos event.

    This intentionally uses a telemetry override instead of
    creating arbitrary Docker containers.

    The Docker Socket Proxy is designed around restricted
    read/restart operations, so creating arbitrary containers
    from the Chaos API would conflict with the hardened design.
    """

    now = time.time()

    if event_type == "spike":

        duration = CPU_SPIKE_DURATION_SECONDS

        metric = {
            "container_id": f"chaos-{target_container}",
            "container_name": target_container,
            "cpu_percent": 98.6,
            "memory_percent": 88.4,
            "memory_usage_mb": 412.0,
            "is_anomaly": True,
            "timestamp": now,
        }

    elif event_type == "crash":

        duration = CRASH_DURATION_SECONDS

        metric = {
            "container_id": f"chaos-{target_container}",
            "container_name": target_container,
            "cpu_percent": 3.0,
            "memory_percent": 94.0,
            "memory_usage_mb": 512.0,
            "is_anomaly": True,
            "log_trace": (
                "FatalError: NullPointerDereference in "
                "main process loop"
            ),
            "timestamp": now,
        }

    elif event_type == "attack":

        duration = ATTACK_DURATION_SECONDS

        metric = {
            "container_id": f"chaos-{target_container}",
            "container_name": target_container,
            "cpu_percent": 91.2,
            "memory_percent": 94.0,
            "memory_usage_mb": 512.0,
            "is_anomaly": True,
            "timestamp": now,
        }

    else:
        raise ValueError(
            f"Unsupported chaos event: {event_type}"
        )

    chaos_overrides[target_container] = {
        "metric": metric,
        "expires_at": now + duration,
    }

    # Immediately update the frontend rather than waiting
    # for the next 3-second collector cycle.
    await broadcast_current_snapshot()

    # Only a service crash becomes an RCA incident.
    if event_type == "crash":

        pending_incidents[target_container] = {
            "container_name": target_container,
            "cpu_percent": metric["cpu_percent"],
            "memory_percent": metric["memory_percent"],
            "log_payload": metric["log_trace"],
            "created_at": now,
        }

        existing_task = incident_tasks.get(target_container)

        if (
            existing_task is None
            or existing_task.done()
        ):
            incident_tasks[target_container] = asyncio.create_task(
                _process_incident_after_debounce(
                    target_container
                )
            )

    return {
        "status": "success",
        "event": event_type.upper(),
        "target": target_container,
        "duration_seconds": duration,
    }


# ============================================================
# RCA INCIDENT PROCESSING
# ============================================================

async def _process_incident_after_debounce(
    container_name: str,
) -> None:
    """
    Waits 3 seconds before processing a crash incident.

    This implements the intended debouncing behavior without
    calling Groq for every normal anomaly sample.
    """

    try:
        await asyncio.sleep(3)

        incident = pending_incidents.pop(
            container_name,
            None
        )

        if incident is None:
            return

        now = time.time()

        previous_call = last_rca_time.get(
            container_name,
            0
        )

        if (
            now - previous_call
            < RCA_COOLDOWN_SECONDS
        ):
            logger.warning(
                f"[RCA COOLDOWN] Skipping RCA for "
                f"{container_name}."
            )
            return

        last_rca_time[container_name] = now

        logger.info(
            f"[DEBOUNCER] 3-second window expired for "
            f"{container_name}. Preparing RCA."
        )

        # ====================================================
        # GROQ RCA
        # ====================================================

        try:

            diagnosis = await asyncio.to_thread(
                generate_root_cause_analysis,
                container_name=incident["container_name"],
                cpu_percent=round(
                    incident["cpu_percent"],
                    2,
                ),
                memory_percent=round(
                    incident["memory_percent"],
                    2,
                ),
                log_payload=incident["log_payload"],
            )

        except Exception as error:

            logger.error(
                f"Groq RCA exception for "
                f"{container_name}: {error}"
            )

            diagnosis = None

        # ====================================================
        # SAFE GROQ FALLBACK
        # ====================================================

        if (
            not isinstance(diagnosis, dict)
            or "error" in diagnosis
        ):

            logger.warning(
                f"[RCA FALLBACK] Groq unavailable for "
                f"{container_name}. Using deterministic "
                f"incident diagnosis."
            )

            diagnosis = {
                "root_cause": (
                    "Simulated fatal service exception "
                    "detected by Aegis Chaos Sandbox."
                ),
                "severity": "CRITICAL",
                "requires_restart": True,
                "recommended_action": (
                    "Restart the affected service and "
                    "continue monitoring telemetry."
                ),
                "source": "AEGIS_LOCAL_FALLBACK",
            }

        # ====================================================
        # LOG DIAGNOSIS
        # ====================================================

        logger.info(
            f"\n[AI DIAGNOSIS - {container_name}]\n"
            f"{json.dumps(diagnosis, indent=2)}\n"
        )

        # ====================================================
        # SELF-HEALING
        # ====================================================

        requires_restart = bool(
            diagnosis.get(
                "requires_restart",
                False
            )
        )

        try:

            healing_result = await asyncio.to_thread(
                execute_self_healing,
                container_name=container_name,
                requires_restart=requires_restart,
            )

            logger.info(
                f"\n[SELF-HEALING ACTION - "
                f"{container_name}]\n"
                f"{json.dumps(healing_result, indent=2)}\n"
            )

        except Exception as error:

            logger.error(
                f"Self-healing failed for "
                f"{container_name}: {error}"
            )

        # Send the diagnosis/incident information to the
        # dashboard as part of the next telemetry message.
        await broadcast_current_snapshot()

    except asyncio.CancelledError:
        raise

    except Exception as error:
        logger.error(
            f"Incident processing failure for "
            f"{container_name}: {error}"
        )

    finally:
        incident_tasks.pop(
            container_name,
            None
        )


# ============================================================
# TELEMETRY COLLECTION
# ============================================================

async def metric_collector_thread() -> None:
    """
    Docker telemetry collector.

    Runs every 3 seconds and streams current metrics.
    """

    logger.info(
        "Starting Aegis telemetry engine via Docker "
        "Socket Proxy (3s interval)..."
    )

    try:

        client = docker.from_env()

        # Confirm connectivity immediately.
        client.ping()

        logger.info(
            "Docker client connected successfully."
        )

    except Exception as error:

        logger.error(
            f"Failed to initialize Docker client: {error}"
        )

        return

    while True:

        try:

            containers = client.containers.list()

            for container in containers:

                try:

                    stats = await asyncio.to_thread(
                        container.stats,
                        stream=False,
                    )

                    # =================================================
                    # CPU
                    # =================================================

                    cpu_stats = stats.get(
                        "cpu_stats",
                        {}
                    )

                    precpu_stats = stats.get(
                        "precpu_stats",
                        {}
                    )

                    current_cpu_usage = (
                        cpu_stats
                        .get("cpu_usage", {})
                        .get("total_usage", 0)
                    )

                    previous_cpu_usage = (
                        precpu_stats
                        .get("cpu_usage", {})
                        .get("total_usage", 0)
                    )

                    cpu_delta = (
                        current_cpu_usage
                        - previous_cpu_usage
                    )

                    current_system_usage = (
                        cpu_stats.get(
                            "system_cpu_usage",
                            0
                        )
                    )

                    previous_system_usage = (
                        precpu_stats.get(
                            "system_cpu_usage",
                            0
                        )
                    )

                    system_delta = (
                        current_system_usage
                        - previous_system_usage
                    )

                    num_cpus = cpu_stats.get(
                        "online_cpus",
                        1
                    ) or 1

                    cpu_percent = 0.0

                    if (
                        system_delta > 0
                        and cpu_delta > 0
                    ):

                        cpu_percent = (
                            cpu_delta
                            / system_delta
                        ) * num_cpus * 100.0

                    # =================================================
                    # MEMORY
                    # =================================================

                    memory_stats = stats.get(
                        "memory_stats",
                        {}
                    )

                    memory_usage = memory_stats.get(
                        "usage",
                        0
                    )

                    memory_limit = memory_stats.get(
                        "limit",
                        0
                    )

                    if memory_limit > 0:

                        memory_percent = (
                            memory_usage
                            / memory_limit
                        ) * 100.0

                    else:

                        memory_percent = 0.0

                    memory_usage_mb = (
                        memory_usage
                        / (1024 * 1024)
                    )

                    # =================================================
                    # ML ANOMALY DETECTION
                    # =================================================

                    is_anomaly = await asyncio.to_thread(
                        detect_anomaly,
                        cpu_percent=round(
                            cpu_percent,
                            2
                        ),
                        memory_percent=round(
                            memory_percent,
                            2
                        ),
                        memory_usage_mb=round(
                            memory_usage_mb,
                            2
                        ),
                    )

                    # =================================================
                    # TELEMETRY PAYLOAD
                    # =================================================

                    metric_payload = {
                        "container_id": (
                            container.id[:12]
                        ),
                        "container_name": (
                            container.name
                        ),
                        "cpu_percent": round(
                            cpu_percent,
                            2
                        ),
                        "memory_percent": round(
                            memory_percent,
                            2
                        ),
                        "memory_usage_mb": round(
                            memory_usage_mb,
                            2
                        ),
                        "is_anomaly": bool(
                            is_anomaly
                        ),
                        "timestamp": time.time(),
                    }

                    telemetry_buffer.append(
                        metric_payload
                    )

                    if is_anomaly:

                        logger.warning(
                            "[ANOMALY DETECTED] "
                            f"{container.name} | "
                            f"CPU={round(cpu_percent, 2)}% | "
                            f"MEM={round(memory_percent, 2)}%"
                        )

                    else:

                        logger.info(
                            "[BUFFERED] "
                            f"{container.name} | "
                            f"CPU={round(cpu_percent, 2)}% | "
                            f"MEM={round(memory_percent, 2)}% | "
                            f"Buffer="
                            f"{len(telemetry_buffer)}/"
                            f"{TELEMETRY_BUFFER_SIZE}"
                        )

                except Exception as container_error:

                    logger.error(
                        f"Error processing container "
                        f"{container.name}: "
                        f"{container_error}"
                    )

        except Exception as loop_error:

            logger.error(
                f"Telemetry collector loop error: "
                f"{loop_error}"
            )

        # =================================================
        # LIVE WEBSOCKET STREAM
        # =================================================

        await broadcast_current_snapshot()

        await asyncio.sleep(
            TELEMETRY_INTERVAL_SECONDS
        )


# ============================================================
# PASSIVE 15-SECOND LOOP
# ============================================================

async def ml_inference_loop() -> None:
    """
    Passive lifecycle loop retained for the architecture.

    Ordinary telemetry anomalies do not independently call
    Groq. Crash incidents are handled through the explicit
    3-second incident pipeline above.
    """

    logger.info(
        "ML inference loop started in passive mode (Day 26)."
    )

    while True:
        await asyncio.sleep(
            ML_INTERVAL_SECONDS
        )


# ============================================================
# SHUTDOWN
# ============================================================

def cancel_incident_tasks() -> None:
    for task in list(incident_tasks.values()):
        if not task.done():
            task.cancel()

    incident_tasks.clear()
    pending_incidents.clear()