# Zero-Trust Security Architecture & Cost Model

## 1. Threat Matrix & Hardening Defenses

| Attack Vector | Potential Impact | Aegis Hardening Defense |
| :--- | :--- | :--- |
| **Docker Socket Hijacking** | Attacker compromises FastAPI container and mounts `docker.sock` to gain root control over EC2 host. | **Docker Socket Proxy:** FastAPI communicates exclusively via `tecnativa/docker-socket-proxy` with `POST=0`, permitting only container restart endpoints. |
| **Log Prompt Injection** | Malicious error log payload (e.g., in HTTP User-Agent) hijacks Groq LLM system prompt. | **Input Sanitizer & Strict Schema:** Strips system delimiters (`<|im_start|>`), limits logs to 2KB, and enforces deterministic JSON output schemas. |
| **Infinite Flapping Loop** | Permanently broken container causes automated healing script to execute infinite restart loops. | **Circuit Breaker Engine:** Restricts automated restarts to max 3 retries per 15 mins. After 3 failures, transitions state to `CRITICAL_HUMAN_REQUIRED`. |
| **API Denial of Service** | Unauthenticated traffic floods backend endpoints, exhausting backend CPU and LLM credits. | **SlowAPI & Supabase JWT:** Enforces rate-limiting on all routes and requires signed JWTs with strict CORS locking to Vercel domain. |

---

## 2. Principle of Least Privilege (PoLP) Enforcement

* **Restricted Container Proxy:** The core FastAPI application never accesses `/var/run/docker.sock` directly. All container control commands pass through `tecnativa/docker-socket-proxy` configured with read-only defaults (`POST=0`).
* **Network Isolation:** No inbound ports (e.g., 80, 443, 8000) are opened in the AWS Security Group. Ingress traffic is managed entirely via an outbound Cloudflare Tunnel (`cloudflared` daemon).
* **Environment Credentials:** Sensitive keys (`GROQ_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY`) are stored in isolated `.env` files and injected strictly at runtime via system environment variables.

---

## 3. Infrastructure Cost Breakdown ($0.00 Free-Tier Stack)

| Service Layer | Provider | Provisioned Resources | Free-Tier Quota / Bounds | Monthly Cost |
| :--- | :--- | :--- | :--- | :--- |
| **Core Compute** | AWS | EC2 t2.micro Instance | 750 Hours/month (12 Months Free) | **$0.00** |
| **Database & Auth** | Supabase | Managed Postgres + Row Level Security | 500 MB Storage / 50K Monthly Active Users | **$0.00** |
| **Frontend Hosting** | Vercel | Next.js 14 App Router Edge Network | 100 GB Bandwidth / Unlimited Deployments | **$0.00** |
| **LLM Inference** | Groq LPU | LLaMA 3 / Mixtral Models | 30 Requests/Minute (Free Tier) | **$0.00** |
| **Ingress Bridge** | Cloudflare | Edge Tunnel (`cloudflared`) | Unlimited Bandwidth & Free SSL Termination | **$0.00** |
| **State Locking** | AWS S3 + DynamoDB | Terraform Remote State & Lock Table | 5 GB S3 + 25 WCU/RCU DynamoDB | **$0.00** |
| **Total Monthly Infra Cost** | | | | **$0.00 / Month** |