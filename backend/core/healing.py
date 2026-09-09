import time
import logging
import os
import docker

logger = logging.getLogger("Aegis-Healing")

# In-memory tracking store: { container_name: {"strikes": int, "last_attempt": float} }
CIRCUIT_BREAKER_STORE = {}
MAX_STRIKES = 3
COOLDOWN_PERIOD_SECONDS = 900  # 15-minute sliding window


def execute_self_healing(container_name: str, requires_restart: bool) -> dict:
    """
    Executes automated container recovery via Docker Socket Proxy 
    using a strict 3-strike circuit breaker threshold.
    """
    if not requires_restart:
        return {
            "status": "NO_ACTION",
            "message": "AI diagnosis indicates container restart is not required."
        }

    current_time = time.time()
    record = CIRCUIT_BREAKER_STORE.get(container_name, {"strikes": 0, "last_attempt": 0})

    # Reset strike counter if the 15-minute cooldown window has passed
    if current_time - record["last_attempt"] > COOLDOWN_PERIOD_SECONDS:
        record["strikes"] = 0

    # Evaluate Circuit Breaker threshold
    if record["strikes"] >= MAX_STRIKES:
        logger.error(
            f"[CIRCUIT BREAKER TRIPPED] Container '{container_name}' reached {MAX_STRIKES} failed attempts! "
            f"Automated recovery halted."
        )
        return {
            "status": "CIRCUIT_BREAKER_TRIPPED",
            "message": f"Container exceeded {MAX_STRIKES} restart attempts within 15 minutes.",
            "escalation": "CRITICAL_HUMAN_REQUIRED"
        }

    # Execute container restart over Docker Socket Proxy (Dynamic Host Resolution)
    try:
        docker_host = os.getenv("DOCKER_HOST", "tcp://aegis-socket-proxy:2375")
        client = docker.DockerClient(base_url=docker_host)
        container = client.containers.get(container_name)

        next_strike = record["strikes"] + 1
        logger.warning(
            f"[SELF-HEALING] Restarting container '{container_name}' (Strike {next_strike}/{MAX_STRIKES})..."
        )
        container.restart(timeout=10)

        # Update strike counter and timestamp
        record["strikes"] = next_strike
        record["last_attempt"] = current_time
        CIRCUIT_BREAKER_STORE[container_name] = record

        return {
            "status": "RESTART_SUCCESS",
            "message": f"Successfully restarted container '{container_name}'.",
            "strikes_used": record["strikes"]
        }

    except Exception as e:
        logger.error(f"[SELF-HEALING FAILED] Container '{container_name}': {str(e)}")
        return {"status": "RESTART_FAILED", "error": str(e)}