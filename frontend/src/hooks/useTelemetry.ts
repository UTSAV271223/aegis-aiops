import {
  useEffect,
  useRef,
  useState,
} from "react";

export interface TelemetryMetric {
  container_id?: string;
  container_name: string;
  cpu_percent: number;
  memory_percent: number;
  memory_usage_mb?: number;
  is_anomaly?: boolean;
  log_trace?: string;
  timestamp: number;
}

function buildWebSocketUrl(): string {
  const configured =
    process.env.NEXT_PUBLIC_WS_URL ||
    "ws://localhost:8000";

  const base = configured
    .replace(/\/+$/, "")
    .replace(/\/ws\/telemetry$/, "");

  return `${base}/ws/telemetry`;
}

export function useTelemetry() {
  const [isConnected, setIsConnected] =
    useState(false);

  const [telemetry, setTelemetry] =
    useState<TelemetryMetric[]>([]);

  const statusRef = useRef<
    Record<string, "HEALTHY" | "ANOMALY">
  >({});

  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimer:
      ReturnType<typeof setTimeout> | null = null;

    let disposed = false;

    const connect = () => {
      if (disposed) {
        return;
      }

      const wsUrl = buildWebSocketUrl();

      console.log(
        `[WebSocket] Connecting to ${wsUrl}`
      );

      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        if (disposed) {
          ws?.close();
          return;
        }

        console.log(
          "[WebSocket] CONNECTED"
        );

        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        if (disposed) {
          return;
        }

        try {

          const payload = JSON.parse(
            event.data
          );

          if (
            payload.event !==
            "TELEMETRY_UPDATE"
          ) {
            return;
          }

          if (
            !Array.isArray(payload.data)
          ) {
            console.warn(
              "[WebSocket] Invalid telemetry payload",
              payload
            );

            return;
          }

          const metrics =
            payload.data as TelemetryMetric[];

          setTelemetry(metrics);

          metrics.forEach((metric) => {

            if (!metric.container_name) {
              return;
            }

            statusRef.current[
              metric.container_name
            ] = metric.is_anomaly
              ? "ANOMALY"
              : "HEALTHY";
          });

        } catch (error) {

          console.error(
            "[WebSocket] Payload parsing error:",
            error
          );
        }
      };

      ws.onerror = (error) => {

        console.error(
          "[WebSocket] ERROR:",
          error
        );
      };

      ws.onclose = (event) => {

        console.log(
          `[WebSocket] CLOSED code=${event.code}`
        );

        setIsConnected(false);

        if (
          disposed
        ) {
          return;
        }

        if (
          reconnectTimer
        ) {
          clearTimeout(
            reconnectTimer
          );
        }

        reconnectTimer =
          setTimeout(
            connect,
            3000
          );
      };
    };

    connect();

    return () => {

      disposed = true;

      if (
        reconnectTimer
      ) {
        clearTimeout(
          reconnectTimer
        );
      }

      if (
        ws
      ) {
        ws.onclose = null;
        ws.close(
          1000,
          "Component unmounted"
        );
      }
    };
  }, []);

  return {
    isConnected,
    telemetry,
    statusRef,
  };
}