'use client';

import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { InstancedMesh, Object3D, Color } from 'three';
import { useGalaxyStore } from '@/stores/galaxy-store';

interface GalaxyNode {
  id: string;
  position: { x: number; y: number; z: number };
  size: number;
  color: string;
}

interface GalaxyNodesProps {
  nodes: GalaxyNode[];
  selectedNode: string | null;
}

export function GalaxyNodes({ nodes, selectedNode }: GalaxyNodesProps) {
  const meshRef = useRef<InstancedMesh>(null);
  const { hoverNode, selectNode } = useGalaxyStore();
  
  const dummy = new Object3D();
  const color = new Color();

  useFrame(() => {
    if (!meshRef.current) return;

    // Update each instance
    nodes.forEach((node, index) => {
      dummy.position.set(node.position.x, node.position.y, node.position.z);
      
      // Scale based on selection/hover state
      const isSelected = selectedNode === node.id;
      const scale = isSelected ? node.size * 1.5 : node.size;
      dummy.scale.setScalar(scale);
      
      dummy.updateMatrix();
      meshRef.current!.setMatrixAt(index, dummy.matrix);
      
      // Set color
      color.set(node.color);
      if (isSelected) {
        color.multiplyScalar(1.5); // Brighten selected nodes
      }
      meshRef.current!.setColorAt(index, color);
    });

    meshRef.current.instanceMatrix.needsUpdate = true;
    if (meshRef.current.instanceColor) {
      meshRef.current.instanceColor.needsUpdate = true;
    }
  });

  const handleClick = (event: any) => {
    event.stopPropagation();
    const instanceId = event.instanceId;
    if (instanceId !== undefined && nodes[instanceId]) {
      selectNode(nodes[instanceId].id);
    }
  };

  const handlePointerOver = (event: any) => {
    event.stopPropagation();
    const instanceId = event.instanceId;
    if (instanceId !== undefined && nodes[instanceId]) {
      hoverNode(nodes[instanceId].id);
      document.body.style.cursor = 'pointer';
    }
  };

  const handlePointerOut = () => {
    hoverNode(null);
    document.body.style.cursor = 'default';
  };

  if (nodes.length === 0) {
    return null;
  }

  return (
    <instancedMesh
      ref={meshRef}
      args={[undefined, undefined, nodes.length]}
      onClick={handleClick}
      onPointerOver={handlePointerOver}
      onPointerOut={handlePointerOut}
    >
      <sphereGeometry args={[1, 16, 16]} />
      <meshPhongMaterial />
    </instancedMesh>
  );
}
