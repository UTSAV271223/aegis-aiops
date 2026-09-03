import joblib
import os
import pandas as pd

# Safely locate and load the model file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'anomaly_model.joblib')

try:
    model = joblib.load(MODEL_PATH)
except FileNotFoundError:
    model = None
    print("CRITICAL: anomaly_model.joblib not found. Run train_model.py first.")

def detect_anomaly(cpu_percent: float, memory_percent: float, memory_usage_mb: float) -> bool:
    """
    Evaluates incoming metrics against the trained model.
    Returns True if an anomaly is detected, False otherwise.
    """
    if model is None:
        return False  # Fail open to prevent crashing the telemetry pipeline
        
    data = pd.DataFrame([{
        'cpu_percent': cpu_percent,
        'memory_percent': memory_percent,
        'memory_usage_mb': memory_usage_mb
    }])
    
    # predict() returns 1 for normal data and -1 for anomalies
    prediction = model.predict(data)
    
    return prediction[0] == -1