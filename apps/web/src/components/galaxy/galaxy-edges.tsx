'use client';

import { useMemo } from 'react';
import { BufferGeometry, Vector3, LineBasicMaterial } from 'three';

interface GalaxyEdge {
  id: string;
  source_id: string;
  target_id: string;
  weight: number;
  visible: boolean;
}

interface GalaxyEdgesProps {
  edges: GalaxyEdge[];
}

export function GalaxyEdges({ edges }: GalaxyEdgesProps) {
  const { geometry, material } = useMemo(() => {
    const visibleEdges = edges.filter(edge => edge.visible);
    
    if (visibleEdges.length === 0) {
      return { geometry: null, material: null };
    }

    const points: Vector3[] = [];
    
    // For now, we'll create dummy positions
    // In the real implementation, we'll get positions from the nodes
    visibleEdges.forEach(edge => {
      // TODO: Get actual node positions
      const sourcePos = new Vector3(
        Math.random() * 200 - 100,
        Math.random() * 200 - 100,
        Math.random() * 200 - 100
      );
      const targetPos = new Vector3(
        Math.random() * 200 - 100,
        Math.random() * 200 - 100,
        Math.random() * 200 - 100
      );
      
      points.push(sourcePos, targetPos);
    });

    const geometry = new BufferGeometry().setFromPoints(points);
    const material = new LineBasicMaterial({
      color: 0x533483,
      opacity: 0.3,
      transparent: true,
    });

    return { geometry, material };
  }, [edges]);

  if (!geometry || !material) {
    return null;
  }

  return (
    <lineSegments geometry={geometry} material={material} />
  );
}
