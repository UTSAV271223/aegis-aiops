import docker
import asyncio
import logging
from collections import deque
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Aegis-Telemetry")

# 1. Initialize the Sliding Window Ring Buffer
telemetry_buffer = deque(maxlen=100)

try:
    docker_client = docker.from_env()
except Exception as e:
    logger.error(f"Failed to connect to Docker: {e}")
    docker_client = None

async def metric_collector_thread():
    if not docker_client:
        return

    logger.info("Starting Aegis telemetry buffer engine (3s interval)...")
    
    while True:
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
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # 2. Append payload to the buffer
                telemetry_buffer.append(payload)
                logger.info(f"[BUFFERED] {container.name} | Mem: {mem_percent}% | Size: {len(telemetry_buffer)}/100")
                
        except Exception as e:
            logger.error(f"Telemetry Error: {e}")
        
        await asyncio.sleep(3)