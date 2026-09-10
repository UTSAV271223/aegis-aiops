'use client';

import React, { useMemo, useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Text, Float, Line } from '@react-three/drei';
import * as THREE from 'three';

type NodeStatus = 'HEALTHY' | 'ANOMALY' | 'RECOVERING' | 'DOWN';

type StatusRef = React.MutableRefObject<Record<string, NodeStatus>>;

/* ============================================================
   FIXED TOPOLOGY NODES & BASE COLORS
============================================================ */
const NODES = [
  {
    id: 'aegis-edge-tunnel',
    name: 'aegis-edge-tunnel',
    position: [-3, 1, 0] as [number, number, number],
    color: '#06b6d4', // Cyan
  },
  {
    id: 'sentinelflow_control_plane',
    name: 'sentinelflow_control_plane',
    position: [0, 2, -1] as [number, number, number],
    color: '#10b981', // Emerald Green
  },
  {
    id: 'aegis-socket-proxy',
    name: 'aegis-socket-proxy',
    position: [3, 1, 0] as [number, number, number],
    color: '#3b82f6', // Vibrant Blue
  },
  {
    id: 'groq-llm-engine',
    name: 'groq-llm-engine',
    position: [-2, -2, 1] as [number, number, number],
    color: '#a855f7', // Purple
  },
  {
    id: 'supabase-postgres',
    name: 'supabase-postgres',
    position: [2, -2, 1] as [number, number, number],
    color: '#f59e0b', // Amber / Yellow
  },
];

/* ============================================================
   NETWORK CONNECTIONS
============================================================ */
const CONNECTIONS = [
  [0, 1],
  [1, 2],
  [1, 3],
  [1, 4],
] as const;

/* ============================================================
   DYNAMIC STATUS OVERRIDE COLORS
============================================================ */
const ANOMALY_COLOR = new THREE.Color('#ef4444');
const RECOVERING_COLOR = new THREE.Color('#f59e0b');
const DOWN_COLOR = new THREE.Color('#78716c');

/* ============================================================
   NODE COMPONENT
============================================================ */
interface NodeMeshProps {
  id: string;
  name: string;
  position: [number, number, number];
  baseColor: string;
  statusRef?: StatusRef;
}

function NodeMesh({ id, name, position, baseColor, statusRef }: NodeMeshProps) {
  // Separate ref for wireframe rotation so text stays facing forward
  const meshGroupRef = useRef<THREE.Group>(null);
  const materialRef = useRef<THREE.MeshBasicMaterial>(null);
  const outerMaterialRef = useRef<THREE.MeshBasicMaterial>(null);

  const originalColor = useMemo(() => new THREE.Color(baseColor), [baseColor]);

  useFrame((_state, delta) => {
    // Only rotate the inner wireframe geometry
    if (meshGroupRef.current) {
      meshGroupRef.current.rotation.y += delta * 0.35;
    }

    if (!statusRef?.current || !materialRef.current || !outerMaterialRef.current) {
      return;
    }

    const status = statusRef.current[id] ?? 'HEALTHY';
    let targetColor = originalColor;

    if (status === 'ANOMALY') {
      targetColor = ANOMALY_COLOR;
    } else if (status === 'RECOVERING') {
      targetColor = RECOVERING_COLOR;
    } else if (status === 'DOWN') {
      targetColor = DOWN_COLOR;
    }

    materialRef.current.color.lerp(targetColor, 0.08);
    outerMaterialRef.current.color.lerp(targetColor, 0.08);
  });

  return (
    <Float speed={1.5} rotationIntensity={0.2} floatIntensity={0.3}>
      <group position={position}>
        {/* ROTATING WIREFRAME MESHES */}
        <group ref={meshGroupRef}>
          {/* CORE */}
          <mesh>
            <icosahedronGeometry args={[0.5, 2]} />
            <meshBasicMaterial
              ref={materialRef}
              color={originalColor}
              wireframe
              transparent
              opacity={0.95}
            />
          </mesh>

          {/* OUTER GLOW */}
          <mesh>
            <sphereGeometry args={[0.68, 24, 24]} />
            <meshBasicMaterial
              ref={outerMaterialRef}
              color={originalColor}
              wireframe
              transparent
              opacity={0.14}
            />
          </mesh>
        </group>

        {/* STATIC FRONT-FACING LABEL */}
        <Text
          position={[0, -0.95, 0]}
          fontSize={0.24}
          color="#e5e5e5"
          anchorX="center"
          anchorY="middle"
        >
          {name}
        </Text>
      </group>
    </Float>
  );
}

/* ============================================================
   TOPOLOGY CANVAS
============================================================ */
interface TopologyMeshProps {
  statusRef?: StatusRef;
}

export default function TopologyMesh({ statusRef }: TopologyMeshProps) {
  const connectionPoints = useMemo(
    () =>
      CONNECTIONS.map(([start, end]) => [
        new THREE.Vector3(...NODES[start].position),
        new THREE.Vector3(...NODES[end].position),
      ]),
    []
  );

  return (
    <div className="w-full h-full min-h-[500px]">
      <Canvas
        dpr={[1, 1.5]}
        camera={{
          position: [0, 0, 9],
          fov: 48,
          near: 0.1,
          far: 100,
        }}
      >
        <color attach="background" args={['#0a0a0a']} />
        <ambientLight intensity={0.7} />
        <pointLight position={[5, 5, 5]} intensity={1} />

        {/* NODES */}
        {NODES.map((node) => (
          <NodeMesh
            key={node.id}
            id={node.id}
            name={node.name}
            position={node.position}
            baseColor={node.color}
            statusRef={statusRef}
          />
        ))}

        {/* NETWORK CONNECTIONS */}
        {connectionPoints.map(([start, end], index) => (
          <Line
            key={`connection-${index}`}
            points={[start, end]}
            color="#334155"
            lineWidth={1}
          />
        ))}

        <OrbitControls
          enableZoom
          enableRotate
          enablePan
          minDistance={5}
          maxDistance={15}
          target={[0, 0, 0]}
        />
      </Canvas>
    </div>
  );
}