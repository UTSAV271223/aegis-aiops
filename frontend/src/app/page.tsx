'use client';

import dynamic from 'next/dynamic';
import { useTelemetry } from '@/hooks/useTelemetry';

import ChaosSandbox from '@/components/ChaosSandbox';
import LiveTelemetry from '@/components/LiveTelemetry';
import CostVerification from '@/components/CostVerification';

// ============================================================
// 3D TOPOLOGY
// ============================================================

const TopologyMesh = dynamic(
  () => import('@/components/TopologyMesh'),
  {
    ssr: false,

    loading: () => (
      <div className="flex h-full min-h-[500px] items-center justify-center">
        <p className="font-mono text-sm text-cyan-400 animate-pulse">
          Initializing 3D Topology Canvas...
        </p>
      </div>
    ),
  }
);


// ============================================================
// COMMAND CENTER
// ============================================================

export default function CommandCenter() {

  // ONE WebSocket / telemetry hook for the whole page.
  const {
    isConnected,
    telemetry,
    statusRef,
  } = useTelemetry();


  return (
    <main className="flex min-h-screen flex-col gap-4 bg-neutral-950 p-4">

      {/* ======================================================
          HEADER
      ====================================================== */}

      <header
        className="
          glass-panel
          z-10
          flex
          min-h-20
          w-full
          items-center
          justify-between
          p-4
        "
      >

        {/* Brand */}

        <div className="shrink-0">

          <h1
            className="
              text-2xl
              font-bold
              tracking-widest
              text-cyan-400
              drop-shadow-md
            "
          >
            AEGIS <span className="text-white">AIOPS</span>
          </h1>

          <p
            className="
              text-xs
              uppercase
              tracking-widest
              text-neutral-400
            "
          >
            Command Center
          </p>

        </div>


        {/* Chaos + Cost Controls */}

        <div className="flex items-center gap-4">
          <ChaosSandbox />
          <CostVerification />
        </div>

      </header>


      {/* ======================================================
          MAIN COMMAND CENTER
      ====================================================== */}

      <div className="relative flex min-h-0 flex-1 gap-4">


        {/* ====================================================
            LEFT — 3D TOPOLOGY
        ==================================================== */}

        <section
          className="
            glass-panel
            relative
            flex
            min-h-[500px]
            min-w-0
            flex-1
            flex-col
            overflow-hidden
          "
        >

          {/* Topology label */}

          <div
            className="
              pointer-events-none
              absolute
              left-4
              top-3
              z-10
              flex
              items-center
              gap-2
            "
          >

            <span
              className={`
                h-2
                w-2
                rounded-full
                ${
                  isConnected
                    ? 'bg-emerald-500 animate-ping'
                    : 'bg-red-500'
                }
              `}
            />

            <span
              className="
                text-xs
                font-mono
                uppercase
                tracking-wider
                text-neutral-400
              "
            >
              3D Infrastructure Topology
            </span>

          </div>


          {/* Three.js */}

          <div className="min-h-0 flex-1">

            <TopologyMesh
              statusRef={statusRef}
            />

          </div>

        </section>


        {/* ====================================================
            RIGHT — LIVE TELEMETRY
        ==================================================== */}

        <section
          className="
            glass-panel
            flex
            w-96
            shrink-0
            flex-col
            overflow-hidden
          "
        >

          <LiveTelemetry
            telemetry={telemetry}
            isConnected={isConnected}
          />

        </section>

      </div>

    </main>
  );
}