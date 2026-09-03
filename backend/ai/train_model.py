import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import joblib
import os

def train_and_save_model():
    print("Generating synthetic telemetry data...")
    np.random.seed(42)
    num_samples = 1500
    
    # We use a standard deviation spread of 10 to ensure accuracy in our statistical calculations
    std_spread = 10 

    # Simulate normal server operations
    cpu_percent = np.random.normal(loc=25.0, scale=std_spread, size=num_samples)
    memory_percent = np.random.normal(loc=40.0, scale=std_spread, size=num_samples)
    memory_usage_mb = np.random.normal(loc=1024.0, scale=std_spread * 15, size=num_samples)

    # Clean up any negative values
    cpu_percent = np.clip(cpu_percent, 1.0, 100.0)
    memory_percent = np.clip(memory_percent, 1.0, 100.0)

    # Compile into a DataFrame
    df = pd.DataFrame({
        'cpu_percent': cpu_percent,
        'memory_percent': memory_percent,
        'memory_usage_mb': memory_usage_mb
    })

    print("Training the Isolation Forest model...")
    # contamination=0.05 assumes roughly 5% of future real-world data might be anomalous
    model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
    model.fit(df)

    # Save the trained model to the current directory
    output_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(output_dir, 'anomaly_model.joblib')
    
    joblib.dump(model, model_path)
    print(f"Success! Model securely saved to: {model_path}")

if __name__ == "__main__":
    train_and_save_model()