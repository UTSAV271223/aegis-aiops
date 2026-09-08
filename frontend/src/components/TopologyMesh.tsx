'use client';

import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Text, Float, Line } from '@react-three/drei';
import * as THREE from 'three';

// Defined node coordinates in 3D space
const NODES = [
  { id: 'aegis-edge-tunnel', name: 'aegis-edge-tunnel', pos: [-3, 1, 0], color: '#06b6d4' },
  { id: 'sentinelflow_control_plane', name: 'sentinelflow_control_plane', pos: [0, 2, -1], color: '#10b981' },
  { id: 'aegis-socket-proxy', name: 'aegis-socket-proxy', pos: [3, 1, 0], color: '#3b82f6' },
  { id: 'groq-llm-engine', name: 'groq-llm-engine', pos: [-2, -2, 1], color: '#a855f7' },
  { id: 'supabase-postgres', name: 'supabase-postgres', pos: [2, -2, 1], color: '#f59e0b' },
];

// Node-to-node topology connections
const CONNECTIONS: [number, number][] = [
  [0, 1], // Edge Tunnel -> Control Plane
  [1, 2], // Control Plane -> Socket Proxy
  [1, 3], // Control Plane -> Groq LLM
  [1, 4], // Control Plane -> Supabase DB
];

// Global status colors for anomalies/recovery
const STATUS_COLORS = {
  anomaly: new THREE.Color('#ef4444'),    // Red
  recovering: new THREE.Color('#f59e0b'), // Amber
  down: new THREE.Color('#78716c'),       // Gray
};

interface NodeMeshProps {
  id: string;
  name: string;
  pos: [number, number, number];
  color: string;
  statusRef?: React.MutableRefObject<any>;
}

function NodeMesh({ id, name, pos, color, statusRef }: NodeMeshProps) {
  const groupRef = useRef<THREE.Group>(null);
  
  // Create refs for the specific materials we want to mutate
  const innerMaterialRef = useRef<THREE.MeshStandardMaterial>(null);
  const outerMaterialRef = useRef<THREE.MeshBasicMaterial>(null);

  // Memoize the original base color so we don't recreate it every frame
  const baseColor = useMemo(() => new THREE.Color(color), [color]);

  useFrame((state, delta) => {
    // Subtle rotation pulse for interactive polish
    if (groupRef.current) {
      groupRef.current.rotation.y += delta * 0.5;
    }

    // Direct GPU color manipulation via WebSocket status tracking
    if (statusRef?.current && innerMaterialRef.current && outerMaterialRef.current) {
      const currentStatus = statusRef.current[id] || 'healthy';
      
      // Determine the target color (fallback to original base color if healthy)
      let targetColor = baseColor;
      if (currentStatus !== 'healthy' && STATUS_COLORS[currentStatus as keyof typeof STATUS_COLORS]) {
        targetColor = STATUS_COLORS[currentStatus as keyof typeof STATUS_COLORS];
      }

      // .lerp() creates a smooth transition between the current color and target color
      innerMaterialRef.current.color.lerp(targetColor, 0.05);
      innerMaterialRef.current.emissive.lerp(targetColor, 0.05);
      outerMaterialRef.current.color.lerp(targetColor, 0.05);
    }
  });

  return (
    <Float speed={2} rotationIntensity={0.5} floatIntensity={0.5}>
      <group position={pos} ref={groupRef}>
        {/* Core Glowing Sphere */}
        <mesh>
          <icosahedronGeometry args={[0.5, 2]} />
          <meshStandardMaterial
            ref={innerMaterialRef}
            color={baseColor}
            emissive={baseColor}
            emissiveIntensity={0.6}
            roughness={0.2}
            wireframe
          />
        </mesh>

        {/* Outer Wireframe Ring */}
        <mesh>
          <sphereGeometry args={[0.65, 16, 16]} />
          <meshBasicMaterial 
            ref={outerMaterialRef} 
            color={baseColor} 
            wireframe 
            transparent 
            opacity={0.15} 
          />
        </mesh>

        {/* 3D Floating Text Label */}
        <Text
          position={[0, -0.9, 0]}
          fontSize={0.25}
          color="#e5e5e5"
          anchorX="center"
          anchorY="middle"
          font="https://fonts.gstatic.com/s/roboto/v18/KFOmCnqEu92Fr1Mu4mxM.woff"
        >
          {name}
        </Text>
      </group>
    </Float>
  );
}

// Ensure the parent accepts statusRef and passes it down
export default function TopologyMesh({ statusRef }: { statusRef?: React.MutableRefObject<any> }) {
  return (
    <div className="w-full h-full min-h-[450px]">
      <Canvas camera={{ position: [0, 0, 8], fov: 50 }}>
        <color attach="background" args={['#0a0a0a']} />
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} intensity={1} color="#ffffff" />
        <pointLight position={[-10, -10, -10]} intensity={0.5} color="#06b6d4" />

        {/* Render 3D Topology Nodes */}
        {NODES.map((node) => (
          <NodeMesh
            key={node.id}
            id={node.id} // Passed ID to match telemetry payload
            name={node.name}
            pos={node.pos as [number, number, number]}
            color={node.color}
            statusRef={statusRef} // Pass down the live ref
          />
        ))}

        {/* Render Interconnecting Network Lines */}
        {CONNECTIONS.map(([startIdx, endIdx], idx) => (
          <Line
            key={idx}
            points={[NODES[startIdx].pos, NODES[endIdx].pos]}
            color="#334155"
            lineWidth={1.5}
            dashed
            dashScale={10}
          />
        ))}

        {/* Interactive Mouse Rotation and Zoom */}
        <OrbitControls enableZoom enableRotate maxDistance={15} minDistance={4} />
      </Canvas>
    </div>
  );
}