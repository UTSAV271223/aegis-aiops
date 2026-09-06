import os
import json
from pydantic import BaseModel, Field
from groq import Groq
from dotenv import load_dotenv

# Load environment variables from backend/.env
load_dotenv()


# 1. Define the strict Pydantic Schema for deterministic output
class RCADiagnosis(BaseModel):
    root_cause: str = Field(..., description="A concise explanation of the failure.")
    remediation_steps: str = Field(..., description="Immediate commands or config adjustments.")
    requires_restart: bool = Field(..., description="True if container restart is recommended, else False.")


def generate_root_cause_analysis(
    container_name: str, 
    cpu_percent: float, 
    memory_percent: float, 
    log_payload: str = ""
) -> dict:
    """
    Sends telemetry to Groq using an active model ID from your account 
    and enforces strict JSON output matching the RCADiagnosis schema.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return {"error": "CRITICAL: Groq API key missing. Cannot perform RCA."}

    client = Groq(api_key=api_key)

    prompt = f"""
    You are an expert AIOps engineer. An anomaly was detected in container '{container_name}'.
    
    Telemetry Stats:
    - CPU Usage: {cpu_percent}%
    - Memory Usage: {memory_percent}%
    
    Captured Log Traces:
    {log_payload if log_payload else "No log trace available."}
    
    You MUST output your response in valid JSON format matching this exact schema:
    {{
      "root_cause": "string",
      "remediation_steps": "string",
      "requires_restart": boolean
    }}
    
    Output ONLY the raw JSON object. Do not include markdown formatting, backticks, or conversational text.
    """

    try:
        completion = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system", 
                    "content": "You are an autonomous AIOps platform. You only output strict, deterministic JSON."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1024, # Increased from 250 to prevent incomplete JSON truncation
            response_format={"type": "json_object"}
        )
        
        # Parse the raw string into a Python dictionary
        raw_json = completion.choices[0].message.content
        parsed_data = json.loads(raw_json)
        
        # Validate through Pydantic
        diagnosis = RCADiagnosis(**parsed_data)
        
        return diagnosis.model_dump()
        
    except Exception as e:
        return {"error": f"Failed to generate RCA JSON: {str(e)}"}