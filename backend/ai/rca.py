import os
from groq import Groq
from core.config import settings

# Initialize Groq client securely using the environment variable
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None

def generate_root_cause_analysis(container_name: str, cpu_percent: float, memory_percent: float, log_payload: str = "") -> str:
    """
    Sends anomalous container telemetry and compressed log payloads to the Groq LLM for predictive failure analysis.
    """
    if not client:
        return "CRITICAL: Groq API key missing. Cannot perform RCA."

    prompt = f"""
    You are an expert AIOps and DevOps engineer. An anomaly was detected in container '{container_name}'.
    
    Telemetry Stats:
    - CPU Usage: {cpu_percent}%
    - Memory Usage: {memory_percent}%
    
    Captured Log Traces (Compressed):
    {log_payload if log_payload else "No log trace available."}
    
    Provide a highly concise, professional diagnosis including:
    1. Likely Root Cause
    2. Immediate Remediation Steps (Commands or config adjustments)
    Keep the response under 150 words.
    """

    try:
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are an autonomous AIOps platform expert specializing in rapid infrastructure incident triage."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=250
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Failed to generate RCA due to AI service error: {str(e)}"