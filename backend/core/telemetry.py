import docker
import asyncio
import logging
from collections import deque
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("Aegis-Telemetry")

# 1. Initialize the Sliding Window Ring Buffer (Max 100 entries)
telemetry_buffer = deque(maxlen=100)

# 2. Day 15 Hardening: Connect via Tecnativa Docker Socket Proxy (TCP 2375)
try:
    docker_client = docker.DockerClient(base_url="tcp://127.0.0.1:2375")
except Exception as e:
    logger.error(f"Failed to connect to Docker Socket Proxy: {e}")
    docker_client = None

def fetch_docker_stats():
    """Synchronous helper function to poll Docker stats through the proxy."""
    if not docker_client:
        return []
        
    stats_list = []
    try:
        containers = docker_client.containers.list(filters={"status": "running"})
        for container in containers:
            stats = container.stats(stream=False)
            
            mem_stats = stats.get("memory_stats", {})
            mem_usage = mem_stats.get("usage", 0)
            mem_limit = mem_stats.get("limit", 1) 
            mem_percent = round((mem_usage / mem_limit) * 100, 2) if mem_limit > 0 else 0.0
            
            payload = {
                "container_id": container.short_id,
                "container_name": container.name,
                "memory_usage_mb": round(mem_usage / (1024 * 1024), 2),
                "memory_percent": mem_percent,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            stats_list.append(payload)
    except Exception as e:
        logger.error(f"Docker Proxy API Error: {e}")
        
    return stats_list

async def metric_collector_thread():
    """Asynchronous background loop executed by FastAPI during application startup."""
    if not docker_client:
        logger.error("Docker Proxy client unavailable. Telemetry polling halted.")
        return

    logger.info("Starting Aegis telemetry engine via Docker Socket Proxy (3s interval)...")
    
    while True:
        try:
            # Offload synchronous Docker SDK calls to a worker thread to keep FastAPI responsive
            current_stats = await asyncio.to_thread(fetch_docker_stats)
            
            for payload in current_stats:
                telemetry_buffer.append(payload)
                logger.info(
                    f"[BUFFERED] {payload['container_name']} | "
                    f"Mem: {payload['memory_percent']}% | "
                    f"Size: {len(telemetry_buffer)}/100"
                )
        except Exception as e:
            logger.error(f"Telemetry Task Error: {e}")
        
        await asyncio.sleep(3)