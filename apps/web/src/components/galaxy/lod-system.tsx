'use client';

import { useMemo } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { Vector3 } from 'three';

interface LODNode {
  id: string;
  title: string;
  position: { x: number; y: number; z: number };
  size: number;
  color: string;
  importance?: number;
  category?: string;
}

interface LODSystemProps {
  nodes: LODNode[];
  maxNodes: number;
  children: (visibleNodes: LODNode[]) => React.ReactNode;
}

export function LODSystem({ nodes, maxNodes = 200, children }: LODSystemProps) {
  const { camera } = useThree();
  
  const visibleNodes = useMemo(() => {
    if (nodes.length <= maxNodes) {
      return nodes;
    }
    
    // Get camera position
    const cameraPos = new Vector3().copy(camera.position);
    
    // Calculate distance and importance for each node
    const nodesWithDistance = nodes.map(node => {
      const nodePos = new Vector3(node.position.x, node.position.y, node.position.z);
      const distance = cameraPos.distanceTo(nodePos);
      
      // LOD scoring: closer nodes and more important nodes get higher scores
      const distanceScore = Math.max(0, 1000 - distance) / 1000;
      const importanceScore = node.importance || 0.5;
      const sizeScore = node.size / 2;
      
      const lodScore = (distanceScore * 0.6) + (importanceScore * 0.3) + (sizeScore * 0.1);
      
      return {
        ...node,
        distance,
        lodScore
      };
    });
    
    // Sort by LOD score and take top nodes
    const sortedNodes = nodesWithDistance
      .sort((a, b) => b.lodScore - a.lodScore)
      .slice(0, maxNodes);
    
    return sortedNodes;
  }, [nodes, camera.position, maxNodes]);
  
  return <>{children(visibleNodes)}</>;
}
