# CI/CD Pipeline Architecture & Telemetry Engine

## 1. CI/CD Deployment Workflow

Aegis uses automated GitHub Actions workflows to validate unit tests, scan container security vulnerabilities, and trigger blue/green edge updates upon commits to `main`.

```mermaid
flowchart LR
    A["Developer Commit / PR"] --> B["GitHub Actions Runner"]
    
    subgraph BuildAndTest ["Stage 1: CI Pipeline"]
        B --> C1["Run Pytest Suite"]
        B --> C2["ESLint & Next.js Build"]
        B --> C3["Trivy Docker Security Scan"]
    end
    
    subgraph ContainerRegistry ["Stage 2: Artifact Management"]
        C1 & C2 & C3 --> D["Build Docker Multi-Stage Image"]
        D --> E["Push to GitHub Container Registry (GHCR)"]
    end
    
    subgraph Deployment ["Stage 3: Edge Deployment"]
        E --> F["Deploy Frontend to Vercel Edge"]
        E --> G["SSH Webhook to AWS EC2"]
        G --> H["Pull New Image & Docker Compose Restart"]
    end
```

---

## 2. Telemetry, Health Polling & Monitoring Matrix

The platform collects runtime container statistics every 3 seconds via the Docker Socket, buffering metrics locally before running anomaly detection loops.

```mermaid
sequenceDiagram
    autonumber
    participant Docker as Docker Socket Proxy
    participant Buffer as Sliding Window Buffer
    participant Anomaly as Scikit-learn Engine
    participant LLM as Groq LLM
    participant WS as WebSocket Server
    participant UI as Next.js 3D Mesh

    loop Every 3 Seconds
        Buffer->>Docker: Poll CPU, RAM & Net I/O
        Docker-->>Buffer: Return Container Stats
    end

    loop Every 15 Seconds
        Anomaly->>Buffer: Extract Deque History (maxlen=100)
        Anomaly->>Anomaly: Evaluate Isolation Forest Score
        alt Score < Threshold (Anomaly Detected)
            Anomaly->>LLM: Dispatch Compressed Trace Payload
            LLM-->>Anomaly: Return Structured JSON Diagnosis
            Anomaly->>WS: Broadcast Anomaly State Payload
            WS-->>UI: Node Transitions to Pulsing Crimson
        end
    end
```

---

## 3. Monitoring Metrics & SLA Targets

| Target Component | Metric Tracked | Sampling Interval | Anomaly Trigger Threshold | Target SLA / Bound |
| :--- | :--- | :--- | :--- | :--- |
| **FastAPI Backend** | P99 Endpoint Latency | Continuous | > 250 ms over 3 consecutive calls | 99.9% Uptime |
| **Docker Microservices** | RAM Utilization % | 3 Seconds | > 85% sustained for 30s | Memory Cap = 128MB |
| **EC2 Host** | Swap Memory Usage | 10 Seconds | > 80% total swap capacity | Max 2 GB Swap |
| **Isolation Forest ML** | Outlier Anomaly Score | 15 Seconds | Decision Score < -0.15 | Zero False Positives |
| **Groq LLM Pipeline** | Token Ingestion Latency | Event-Driven | > 1.2 Seconds | < 800 ms response time |
| **WebSocket Connection** | Heartbeat Ping/Pong | 5 Seconds | Disconnect > 10 Seconds | Auto-reconnect < 1s |