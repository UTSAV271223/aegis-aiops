'use client';

import React, { useState } from 'react';
import { ShieldAlert, Zap, ServerCrash } from 'lucide-react';

export default function ChaosSandbox() {
  // This state Remembers which button was clicked
  const [activeAction, setActiveAction] = useState<string | null>(null);

  // This function handles the click event
  const handleAction = (actionType: string) => {
    setActiveAction(actionType);
    
    // Resets the button back to normal after 1.5 seconds
    setTimeout(() => {
      setActiveAction(null);
    }, 1500);
  };

  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-2 mr-2">
        <span className="h-2 w-2 rounded-full bg-red-500 animate-pulse" />
        <span className="text-xs font-mono text-neutral-400 uppercase tracking-wider">
          Chaos Sandbox:
        </span>
      </div>

      <button
        onClick={() => handleAction('spike')}
        disabled={activeAction !== null}
        className="flex items-center gap-2 px-3 py-1.5 text-xs font-mono rounded bg-red-950/40 border border-red-800/50 text-red-400 hover:bg-red-900/50 transition-all cursor-pointer disabled:opacity-50 shadow-lg shadow-red-950/20"
      >
        <Zap className="w-3 h-3" />
        {activeAction === 'spike' ? 'Simulating Spike...' : 'Simulate CPU Spike'}
      </button>

      <button
        onClick={() => handleAction('crash')}
        disabled={activeAction !== null}
        className="flex items-center gap-2 px-3 py-1.5 text-xs font-mono rounded bg-amber-950/40 border border-amber-800/50 text-amber-400 hover:bg-amber-900/50 transition-all cursor-pointer disabled:opacity-50 shadow-lg shadow-amber-950/20"
      >
        <ServerCrash className="w-3 h-3" />
        {activeAction === 'crash' ? 'Triggering Failure...' : 'Inject Service Failure'}
      </button>
    </div>
  );
}