# Local Setup, Production Deployment & Operations Guide

## 1. Prerequisites & System Requirements

Ensure the following runtimes and tools are installed locally before proceeding:

* **Python:** v3.11 or higher
* **Node.js:** v18.0 or higher (`npm` v9+)
* **Docker Desktop:** Running locally with daemon enabled
* **AWS CLI:** Configured with active credentials (`aws configure`)
* **Terraform:** v1.5+ (for Infrastructure as Code deployment)

---

## 2. Local Development Quick Start

### Step 1: Backend Setup
1. Clone the repository and navigate to the root folder:
   ```bash
   git clone [https://github.com/UTSAV271223/aegis-aiops.git](https://github.com/UTSAV271223/aegis-aiops.git)
   cd aegis-aiops
   ```

2. Create and activate a Python virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables (`.env` in root):
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   SUPABASE_URL=your_supabase_url_here
   SUPABASE_KEY=your_supabase_anon_key_here
   ```

5. Launch the FastAPI server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

---

### Step 2: Frontend Setup
1. Open a second terminal tab and navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install Node dependencies:
   ```bash
   npm install
   ```

3. Configure local environment variables (`.env.local` in `frontend/`):
   ```env
   NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
   NEXT_PUBLIC_SUPABASE_URL=your_supabase_url_here
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key_here
   ```

4. Launch the Next.js development server:
   ```bash
   npm run dev
   ```

5. Open `http://localhost:3000` in your browser to view the 3D Command Center.

---

## 3. Infrastructure as Code (IaC) Deployment

To provision the AWS t2.micro EC2 instance, S3 state backend, and DynamoDB lock table via Terraform:

```bash
cd infra/terraform
terraform init
terraform plan
terraform apply -auto-approve
```

---

## 4. Production Cloudflare Tunnel Setup

To expose the backend securely without purchasing a custom SSL certificate or opening inbound EC2 ports:

1. Install the `cloudflared` daemon on the AWS EC2 instance:
   ```bash
   sudo wget -q [https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb](https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb)
   sudo dpkg -i cloudflared-linux-amd64.deb
   ```

2. Authenticate and create a secure tunnel:
   ```bash
   cloudflared tunnel login
   cloudflared tunnel create aegis-backend-tunnel
   ```

3. Route traffic to the local FastAPI port (`http://localhost:8000`) and run the daemon as a system service:
   ```bash
   cloudflared tunnel run aegis-backend-tunnel
   ```

---

## 5. Recruiter Chaos Sandbox Testing Guide

To demonstrate autonomous failure detection and recovery:

1. Open the web interface at `http://localhost:3000` (or live Vercel URL).
2. Locate the **Recruiter Chaos Sandbox** header panel.
3. **Simulate Metric Anomaly:** Click **"Simulate CPU Spike"**. The Scikit-learn Isolation Forest model detects the resource anomaly within 15 seconds, turning the node yellow.
4. **Inject Fatal Crash:** Click **"Inject Fatal Crash"**. The system captures the stack trace, triggers the 3-second Log Debouncer, sends the payload to Groq LLM for diagnosis, turns the 3D node crimson, and automatically triggers a container restart to return the node to glowing cyan.