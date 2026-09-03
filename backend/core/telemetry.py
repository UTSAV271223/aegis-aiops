import asyncio
import logging
from collections import deque
import docker
from ai.anomaly import detect_anomaly
from ai.rca import generate_root_cause_analysis

logger = logging.getLogger("Aegis-Telemetry")
logging.basicConfig(level=logging.INFO)

# In-memory ring buffer (Capacity: 100 metrics)
telemetry_buffer = deque(maxlen=100)

async def metric_collector_thread():
    """
    Background worker that polls Docker socket via Docker SDK every 3 seconds,
    runs anomaly detection, and buffers the structured telemetry payload.
    """
    logger.info("Starting Aegis telemetry engine via Docker Socket Proxy (3s interval)...")
    
    # Connect via Docker socket proxy/environment
    try:
        client = docker.from_env()
    except Exception as e:
        logger.error(f"Failed to initialize Docker client: {e}")
        return

    while True:
        try:
            containers = client.containers.list()
            for container in containers:
                try:
                    stats = container.stats(stream=False)
                    
                    # Calculate CPU percentage safely from Docker stats raw structures
                    cpu_stats = stats.get("cpu_stats", {})
                    precpu_stats = stats.get("precpu_stats", {})
                    
                    cpu_delta = cpu_stats.get("cpu_usage", {}).get("total_usage", 0) - precpu_stats.get("cpu_usage", {}).get("total_usage", 0)
                    system_delta = cpu_stats.get("system_cpu_usage", 0) - precpu_stats.get("system_cpu_usage", 0)
                    num_cpus = cpu_stats.get("online_cpus", 1)
                    
                    cpu_percent = 0.0
                    if system_delta > 0 and cpu_delta > 0:
                        cpu_percent = (cpu_delta / system_delta) * num_cpus * 100.0

                    # Calculate Memory usage
                    memory_stats = stats.get("memory_stats", {})
                    mem_usage = memory_stats.get("usage", 0)
                    mem_limit = memory_stats.get("limit", 1)
                    memory_percent = (mem_usage / mem_limit) * 100.0
                    memory_usage_mb = mem_usage / (1024 * 1024)

                    # --- DAY 17 AI ANOMALY DETECTION HOOK ---
                    is_anomaly = detect_anomaly(
                        cpu_percent=round(cpu_percent, 2),
                        memory_percent=round(memory_percent, 2),
                        memory_usage_mb=round(memory_usage_mb, 2)
                    )
                    # ----------------------------------------

                    metric_payload = {
                        "container_id": container.id[:12],
                        "container_name": container.name,
                        "cpu_percent": round(cpu_percent, 2),
                        "memory_percent": round(memory_percent, 2),
                        "memory_usage_mb": round(memory_usage_mb, 2),
                        "is_anomaly": is_anomaly
                    }

                    telemetry_buffer.append(metric_payload)
                    
                    if is_anomaly:
                        logger.warning(f"[ANOMALY DETECTED] Container {container.name} flagged by Isolation Forest!")
                    else:
                        logger.info(f"[BUFFERED] {container.name} | Mem: {round(memory_percent, 2)}% | Size: {len(telemetry_buffer)}/100")

                except Exception as container_err:
                    logger.error(f"Error parsing stats for container {container.name}: {container_err}")
                    
        except Exception as loop_err:
            logger.error(f"Telemetry collector loop error: {loop_err}")
            
        await asyncio.sleep(3)


async def ml_inference_loop():
    """
    Day 18: Background worker that polls the ring buffer every 15 seconds.
    If an anomaly is detected, it triggers the Groq LLM for predictive failure analysis.
    """
    logger.info("Starting 15-second ML inference loop for automated RCA...")
    
    while True:
        try:
            # Safely scan the current buffer for any metrics flagged as an anomaly
            current_buffer = list(telemetry_buffer)
            anomalies = [metric for metric in current_buffer if metric.get("is_anomaly") is True]

            if anomalies:
                # Grab the most recent anomaly to analyze
                target = anomalies[-1]
                logger.warning(f"[INFERENCE] Analyzing anomaly for {target['container_name']}...")
                
                # Execute predictive failure analysis via Groq
                diagnosis = generate_root_cause_analysis(
                    container_name=target['container_name'],
                    cpu_percent=target['cpu_percent'],
                    memory_percent=target['memory_percent']
                )
                
                logger.info(f"\n[AI DIAGNOSIS - {target['container_name']}]\n{diagnosis}\n")
                
        except Exception as loop_err:
            logger.error(f"ML Inference Loop Error: {loop_err}")
            
        await asyncio.sleep(15)