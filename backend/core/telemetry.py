import docker
import asyncio
import logging

# Configure terminal logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Aegis-Telemetry")

# Initialize Docker client (connects to local Docker Desktop daemon)
try:
    docker_client = docker.from_env()
    logger.info("Successfully connected to Docker Daemon.")
except Exception as e:
    logger.error(f"Failed to connect to Docker daemon. Is Docker running? Error: {e}")
    docker_client = None

async def metric_collector_thread():
    """
    Background thread: Polls Docker container metrics every 3 seconds
    to prevent AWS EC2 CPU credit exhaustion.
    """
    if not docker_client:
        logger.warning("Telemetry collector disabled: No Docker client.")
        return

    logger.info("Starting Aegis Docker SDK metric collector thread (3s interval)...")
    
    while True:
        try:
            # Fetch all currently running containers
            containers = docker_client.containers.list(filters={"status": "running"})
            
            for container in containers:
                # stream=False grabs a single instantaneous snapshot of the metrics
                stats = container.stats(stream=False)
                
                # Extract basic identifiers for Day 12 verification
                container_name = container.name
                read_time = stats.get("read")
                
                logger.info(f"[TELEMETRY] Polled {container_name} at {read_time}")
                
        except Exception as e:
            logger.error(f"Telemetry Engine Error: {e}")
        
        # Strict 3-second circuit breaker sleep (Aegis Architecture Requirement)
        await asyncio.sleep(3)