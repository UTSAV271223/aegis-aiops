'use client';

import React, { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Text, Float, Line } from '@react-three/drei';
import * as THREE from 'three';

// Defined node coordinates in 3D space
const NODES = [
  { id: 'edge-tunnel', name: 'aegis-edge-tunnel', pos: [-3, 1, 0], color: '#06b6d4' },
  { id: 'control-plane', name: 'sentinelflow_control_plane', pos: [0, 2, -1], color: '#10b981' },
  { id: 'socket-proxy', name: 'aegis-socket-proxy', pos: [3, 1, 0], color: '#3b82f6' },
  { id: 'groq-engine', name: 'groq-llm-engine', pos: [-2, -2, 1], color: '#a855f7' },
  { id: 'supabase-db', name: 'supabase-postgres', pos: [2, -2, 1], color: '#f59e0b' },
];

// Node-to-node topology connections
const CONNECTIONS: [number, number][] = [
  [0, 1], // Edge Tunnel -> Control Plane
  [1, 2], // Control Plane -> Socket Proxy
  [1, 3], // Control Plane -> Groq LLM
  [1, 4], // Control Plane -> Supabase DB
];

function NodeMesh({ name, pos, color }: { name: string; pos: [number, number, number]; color: string }) {
  const meshRef = useRef<THREE.Mesh>(null);

  // Subtle rotation pulse for interactive polish
  useFrame((state, delta) => {
    if (meshRef.current) {
      meshRef.current.rotation.y += delta * 0.5;
    }
  });

  return (
    <Float speed={2} rotationIntensity={0.5} floatIntensity={0.5}>
      <group position={pos}>
        {/* Core Glowing Sphere */}
        <mesh ref={meshRef}>
          <icosahedronGeometry args={[0.5, 2]} />
          <meshStandardMaterial
            color={color}
            emissive={color}
            emissiveIntensity={0.6}
            roughness={0.2}
            wireframe
          />
        </mesh>

        {/* Outer Wireframe Ring */}
        <mesh>
          <sphereGeometry args={[0.65, 16, 16]} />
          <meshBasicMaterial color={color} wireframe transparent opacity={0.15} />
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

export default function TopologyMesh() {
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
            name={node.name}
            pos={node.pos as [number, number, number]}
            color={node.color}
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