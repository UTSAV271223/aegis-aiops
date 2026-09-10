'use client';

import React from 'react';

import type { TelemetryMetric } from '@/hooks/useTelemetry';


interface LiveTelemetryProps {
  telemetry: TelemetryMetric[];
  isConnected: boolean;
}


function formatNumber(
  value: number | undefined
): string {
  if (
    typeof value !== 'number' ||
    Number.isNaN(value)
  ) {
    return '0.00';
  }

  return value.toFixed(2);
}


export default function LiveTelemetry({
  telemetry,
  isConnected,
}: LiveTelemetryProps) {

  return (
    <aside className="w-full h-full flex flex-col p-4">

      {/* =====================================================
          HEADER
      ===================================================== */}

      <div className="flex items-center justify-between mb-4">

        <h2 className="text-xs font-mono text-neutral-400">
          LIVE TELEMETRY FEED
        </h2>

        <span
          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
            isConnected
              ? 'bg-green-500/20 text-green-400'
              : 'bg-red-500/20 text-red-400'
          }`}
        >
          {isConnected
            ? '● LIVE WSS'
            : '● OFFLINE'}
        </span>

      </div>


      {/* =====================================================
          TELEMETRY CONTENT
      ===================================================== */}

      <div className="flex-1 overflow-y-auto space-y-2">

        {!isConnected && (
          <p className="text-xs text-neutral-600 mt-10 text-center font-mono animate-pulse">
            Connecting to telemetry stream...
          </p>
        )}


        {isConnected &&
          telemetry.length === 0 && (
            <p className="text-xs text-neutral-600 mt-10 text-center font-mono">
              Waiting for telemetry...
            </p>
          )}


        {telemetry.map(
          (metric, index) => {

            const anomaly =
              metric.is_anomaly === true;

            return (
              <div
                key={
                  `${metric.container_id ?? metric.container_name}-${index}`
                }
                className={`rounded border p-2 font-mono text-xs ${
                  anomaly
                    ? 'border-red-500/30 bg-red-500/5'
                    : 'border-white/10 bg-white/5'
                }`}
              >

                {/* Container name + status */}

                <div className="flex items-center justify-between gap-2 mb-1">

                  <span
                    className="text-blue-400 truncate"
                    title={metric.container_name}
                  >
                    {metric.container_name}
                  </span>

                  <span
                    className={
                      anomaly
                        ? 'text-red-400'
                        : 'text-green-400'
                    }
                  >
                    {anomaly
                      ? 'ANOMALY'
                      : 'HEALTHY'}
                  </span>

                </div>


                {/* CPU */}

                <div className="text-neutral-400">
                  CPU:{' '}
                  {formatNumber(
                    metric.cpu_percent
                  )}
                  %
                </div>


                {/* Memory */}

                <div className="text-neutral-400">
                  RAM:{' '}
                  {formatNumber(
                    metric.memory_percent
                  )}
                  %
                </div>


                {/* Memory MB */}

                {typeof metric.memory_usage_mb ===
                  'number' && (
                    <div className="text-neutral-500">
                      MEM:{' '}
                      {formatNumber(
                        metric.memory_usage_mb
                      )}
                      {' '}MB
                    </div>
                  )}


                {/* Optional log */}

                {metric.log_trace && (
                  <div className="mt-2 text-red-300/80 break-words">
                    {metric.log_trace}
                  </div>
                )}

              </div>
            );
          }
        )}

      </div>

    </aside>
  );
}