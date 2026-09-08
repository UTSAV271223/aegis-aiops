'use client';

import dynamic from 'next/dynamic';
import { useTelemetry } from '@/hooks/useTelemetry';
import ChaosSandbox from '@/components/ChaosSandbox'; // <-- Import the new ChaosSandbox component

// Dynamic import with SSR disabled for 3D WebGL Canvas
const TopologyMesh = dynamic(() => import('@/components/TopologyMesh'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full">
      <p className="text-cyan-400 font-mono text-sm animate-pulse">
        Initializing 3D Topology Canvas...
      </p>
    </div>
  ),
});

export default function CommandCenter() {
  // Initialize the live WebSocket ref for non-blocking UI telemetry updates
  const nodeStatusesRef = useTelemetry();

  return (
    <main className="flex min-h-screen flex-col p-4 bg-neutral-950">
      
      {/* HEADER: Recruiter Chaos Sandbox Active Panel */}
      <header className="glass-panel flex justify-between items-center p-4 mb-4 h-20 w-full z-10">
        <div>
          <h1 className="text-2xl font-bold tracking-widest text-cyan-400 drop-shadow-md">
            AEGIS <span className="text-white">AIOPS</span>
          </h1>
          <p className="text-xs text-neutral-400 uppercase tracking-widest">Command Center</p>
        </div>
        
        {/* Render the Interactive Chaos Sandbox */}
        <ChaosSandbox />
      </header>

      {/* MAIN VIEWPORT */}
      <div className="flex flex-1 gap-4 h-full relative">
        
        {/* LEFT: 3D Topology Mesh Map */}
        <section className="glass-panel flex-1 flex flex-col relative overflow-hidden min-h-[500px]">
          <div className="absolute top-3 left-4 z-10 flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-ping" />
            <span className="text-xs font-mono text-neutral-400 uppercase tracking-wider">
              3D Infrastructure Topology
            </span>
          </div>
          <TopologyMesh statusRef={nodeStatusesRef} />
        </section>

        {/* RIGHT: Telemetry & Alert Stream Placeholder */}
        <aside className="glass-panel w-96 flex flex-col p-4">
          <h2 className="text-sm font-bold text-neutral-300 uppercase tracking-wider mb-4 border-b border-neutral-800 pb-2">
            Live Telemetry
          </h2>
          <div className="flex-1 flex items-center justify-center border border-dashed border-neutral-800 rounded">
             <p className="text-xs text-neutral-600 font-mono">Awaiting WebSocket Data...</p>
          </div>
        </aside>

      </div>
    </main>
  );
}