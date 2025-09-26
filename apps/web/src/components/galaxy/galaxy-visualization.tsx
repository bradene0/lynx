'use client';

import { useRef, useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Stars } from '@react-three/drei';
import { GalaxyNodes } from './galaxy-nodes';
import { GalaxyEdges } from './galaxy-edges';
import { useGalaxyStore } from '@/stores/galaxy-store';

export function GalaxyVisualization() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { nodes, edges, selectedNode, camera } = useGalaxyStore();

  useEffect(() => {
    // Initialize galaxy data when component mounts
    // This will be replaced with actual data loading
    console.log('Galaxy visualization mounted');
  }, []);

  return (
    <Canvas
      ref={canvasRef}
      camera={{
        position: [0, 0, 100],
        fov: 75,
        near: 0.1,
        far: 10000,
      }}
      style={{
        width: '100vw',
        height: '100vh',
        background: 'transparent',
      }}
    >
      {/* Lighting */}
      <ambientLight intensity={0.2} />
      <pointLight position={[10, 10, 10]} intensity={0.5} />

      {/* Background Stars */}
      <Stars
        radius={1000}
        depth={50}
        count={5000}
        factor={4}
        saturation={0}
        fade
        speed={1}
      />

      {/* Galaxy Components */}
      <GalaxyNodes nodes={nodes} selectedNode={selectedNode} />
      <GalaxyEdges edges={edges} />

      {/* Camera Controls */}
      <OrbitControls
        enablePan={true}
        enableZoom={true}
        enableRotate={true}
        zoomSpeed={0.6}
        panSpeed={0.8}
        rotateSpeed={0.4}
        minDistance={10}
        maxDistance={1000}
        target={camera.target}
      />
    </Canvas>
  );
}
