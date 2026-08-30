import docker
import asyncio
import logging
from collections import deque
from datetime import datetime

# Configure terminal logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Aegis-Telemetry")

# ---------------------------------------------------------
# DAY 13: THE IN-MEMORY SLIDING WINDOW BUFFER
# Automatically drops the oldest record when exceeding 100 items,
# preventing memory leaks on the 1GB AWS t2.micro host.
# ---------------------------------------------------------
telemetry_buffer = deque(maxlen=100)

# Initialize Docker client
try:
    docker_client = docker.from_env()
    logger.info("Successfully connected to Docker Daemon.")
except Exception as e:
    logger.error(f"Failed to connect to Docker daemon: {e}")
    docker_client = None

async def metric_collector_thread():
    """
    Background thread: Polls Docker container metrics every 3 seconds
    and stores them in a highly efficient ring buffer.
    """
    if not docker_client:
        logger.warning("Telemetry collector disabled: No Docker client.")
        return

    logger.info("Starting Aegis telemetry buffer engine (3s interval)...")
    
    while True:
        try:
            containers = docker_client.containers.list(filters={"status": "running"})
            
            for container in containers:
                stats = container.stats(stream=False)
                
                # Safely extract memory metrics from the raw Docker payload
                mem_stats = stats.get("memory_stats", {})
                mem_usage = mem_stats.get("usage", 0)
                mem_limit = mem_stats.get("limit", 1)  # Default to 1 to prevent division by zero
                mem_percent = round((mem_usage / mem_limit) * 100, 2) if mem_limit > 0 else 0.0
                
                # Construct the standardized telemetry payload
                payload = {
                    "container_id": container.short_id,
                    "container_name": container.name,
                    "memory_usage_mb": round(mem_usage / (1024 * 1024), 2),
                    "memory_percent": mem_percent,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Append to the sliding window (O(1) time complexity)
                telemetry_buffer.append(payload)
                logger.info(f"[BUFFERED] {container.name} | Mem: {mem_percent}% | Buffer Size: {len(telemetry_buffer)}/100")
                
        except Exception as e:
            logger.error(f"Telemetry Engine Error: {e}")
        
        # Strict 3-second circuit breaker sleep
        await asyncio.sleep(3)