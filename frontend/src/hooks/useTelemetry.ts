// frontend/hooks/useTelemetry.ts
import { useEffect, useRef } from 'react';

// Define the shape of our incoming telemetry data
export interface NodeStatus {
  [containerName: string]: 'healthy' | 'anomaly' | 'recovering' | 'down';
}

export function useTelemetry() {
  // We use a ref to hold the latest statuses. 
  // Changing this will NOT trigger a React component re-render!
  const nodeStatuses = useRef<NodeStatus>({
    'sentinelflow_control_plane': 'healthy',
    'aegis-edge-tunnel': 'healthy',
    'aegis-socket-proxy': 'healthy',
    'groq-llm-engine': 'healthy',
    'supabase-postgres': 'healthy',
  });

  useEffect(() => {
    // Replace with your actual FastAPI WebSocket URL
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://127.0.0.1:8000/ws/telemetry';
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        // Assume the backend sends: { container: "aegis-edge-tunnel", status: "anomaly" }
        // Update the ref directly. 
        if (data.container && data.status) {
          nodeStatuses.current[data.container] = data.status;
        }
      } catch (err) {
        console.error('WebSocket payload parsing error:', err);
      }
    };

    ws.onerror = (err) => console.error('WebSocket Error:', err);
    
    return () => {
      ws.close();
    };
  }, []);

  return nodeStatuses;
}