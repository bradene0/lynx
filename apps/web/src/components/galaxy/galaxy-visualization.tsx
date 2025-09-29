'use client';

import { useRef, useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Stars } from '@react-three/drei';
import { GalaxyNodes } from './galaxy-nodes';
import { GalaxyEdges } from './galaxy-edges';
import { CameraController } from './camera-controller';
import { LODSystem } from './lod-system';
import { useGalaxyStore } from '@/stores/galaxy-store';
import { useGalaxyData } from '@/hooks/use-galaxy-data';

export function GalaxyVisualization() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const nodeClickedRef = useRef(false);
  const { nodes, edges, selectedNode, camera, selectNode } = useGalaxyStore();
  // Re-enable data loading now that database is working
  const { isLoading, error } = useGalaxyData();
  
  // Handle background clicks to deselect nodes
  const handleCanvasClick = (event: any) => {
    // Check if a node was clicked recently
    if (nodeClickedRef.current) {
      nodeClickedRef.current = false; // Reset flag
      return;
    }
    
    selectNode(null);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-galaxy-white">
          Loading galaxy data...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-red-400">
          Error loading galaxy: {error ? String(error) : 'Unknown error'}
        </div>
      </div>
    );
  }

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
        width: '100%',
        height: '100%',
        background: 'transparent',
        userSelect: 'none',
      } as React.CSSProperties}
      onClick={handleCanvasClick}
    >
      {/* Enhanced Lighting System */}
      <ambientLight intensity={0.4} />
      <directionalLight 
        position={[10, 10, 5]} 
        intensity={1.0} 
        castShadow
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
      />
      <pointLight position={[-10, -10, -5]} intensity={0.5} color="#4A90E2" />
      <pointLight position={[5, -5, 10]} intensity={0.4} color="#E94560" />
      <pointLight position={[0, 15, 0]} intensity={0.3} color="#FFD700" />

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

      {/* Camera Controller */}
      <CameraController />

      {/* Galaxy Components with LOD */}
      <LODSystem 
        nodes={nodes} 
        maxNodes={1000}
        enableFrustumCulling={true}
        enableClustering={true}
      >
        {(visibleNodes, lodLevel) => (
          <>
            <GalaxyNodes nodes={visibleNodes} selectedNode={selectedNode} nodeClickedRef={nodeClickedRef} />
            <GalaxyEdges edges={edges} nodes={visibleNodes} />
          </>
        )}
      </LODSystem>

      {/* Camera Controls */}
      <OrbitControls
        enablePan={!camera.animating}
        enableZoom={!camera.animating}
        enableRotate={!camera.animating}
        zoomSpeed={0.6}
        panSpeed={0.8}
        rotateSpeed={0.4}
        minDistance={10}
        maxDistance={1000}
        target={camera.target}
        enableDamping={true}
        dampingFactor={0.05}
        autoRotate={false}
      />
    </Canvas>
  );
}
