'use client';

import React, {
  useState,
} from 'react';

import {
  Activity,
  ServerCrash,
  ShieldAlert,
  Zap,
} from 'lucide-react';

type ChaosAction =
  | 'spike'
  | 'crash'
  | 'attack';

export default function ChaosSandbox() {

  const [
    activeAction,
    setActiveAction,
  ] = useState<ChaosAction | null>(null);

  const [
    message,
    setMessage,
  ] = useState('');

  const API_BASE_URL = (
    process.env.NEXT_PUBLIC_API_URL ||
    'http://localhost:8000'
  ).replace(/\/+$/, '');

  const triggerChaos = async (
    actionType: ChaosAction
  ) => {

    if (activeAction !== null) {
      return;
    }

    setActiveAction(actionType);
    setMessage('');

    try {

      const response = await fetch(
        `${API_BASE_URL}/api/v1/chaos/${actionType}`,
        {
          method: 'POST',
          headers: {
            'Content-Type':
              'application/json',
          },
          body: JSON.stringify({
            target_container:
              'aegis-edge-tunnel',
          }),
        }
      );

      const data =
        await response.json()
          .catch(() => ({}));

      if (!response.ok) {

        throw new Error(
          data?.detail ||
            `HTTP ${response.status}`
        );
      }

      console.log(
        '[Chaos]',
        data
      );

      setMessage(
        `${String(
          actionType
        ).toUpperCase()} initiated`
      );

    } catch (error) {

      console.error(
        '[Chaos]',
        error
      );

      setMessage(
        error instanceof Error
          ? error.message
          : 'Chaos request failed'
      );

    } finally {

      setTimeout(() => {
        setActiveAction(null);
        setMessage('');
      }, 1500);
    }
  };

  return (
    <div className="flex items-center gap-3">

      <div className="flex items-center gap-2 mr-2">

        <Activity className="h-4 w-4 text-red-500 animate-pulse" />

        <span className="text-xs font-mono text-neutral-400 uppercase tracking-wider">
          Chaos Sandbox:
        </span>

      </div>

      <button
        type="button"
        onClick={() =>
          triggerChaos('spike')
        }
        disabled={
          activeAction !== null
        }
        className={`flex items-center gap-2 px-3 py-1.5 text-xs font-mono rounded border transition-all cursor-pointer disabled:opacity-50 shadow-lg ${
          activeAction === 'spike'
            ? 'bg-blue-900/50 border-blue-500 text-blue-300'
            : 'bg-blue-950/40 border-blue-800/50 text-blue-400 hover:bg-blue-900/50'
        }`}
      >
        <Zap className="w-3 h-3" />

        {activeAction === 'spike'
          ? 'Spiking CPU...'
          : 'Simulate CPU Spike'}
      </button>

      <button
        type="button"
        onClick={() =>
          triggerChaos('crash')
        }
        disabled={
          activeAction !== null
        }
        className={`flex items-center gap-2 px-3 py-1.5 text-xs font-mono rounded border transition-all cursor-pointer disabled:opacity-50 shadow-lg ${
          activeAction === 'crash'
            ? 'bg-amber-900/50 border-amber-500 text-amber-300'
            : 'bg-amber-950/40 border-amber-800/50 text-amber-400 hover:bg-amber-900/50'
        }`}
      >
        <ServerCrash className="w-3 h-3" />

        {activeAction === 'crash'
          ? 'Triggering Failure...'
          : 'Inject Service Failure'}
      </button>

      <button
        type="button"
        onClick={() =>
          triggerChaos('attack')
        }
        disabled={
          activeAction !== null
        }
        className={`flex items-center gap-2 px-3 py-1.5 text-xs font-mono rounded border transition-all cursor-pointer disabled:opacity-50 shadow-lg ${
          activeAction === 'attack'
            ? 'bg-red-900/50 border-red-500 text-red-300'
            : 'bg-red-950/40 border-red-800/50 text-red-400 hover:bg-red-900/50'
        }`}
      >
        <ShieldAlert className="w-3 h-3" />

        {activeAction === 'attack'
          ? 'Attacking...'
          : 'Simulate Attack'}
      </button>

      {message && (
        <span className="text-[10px] font-mono text-neutral-500">
          {message}
        </span>
      )}

    </div>
  );
}