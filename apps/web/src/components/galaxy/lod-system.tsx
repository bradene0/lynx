'use client';

import { useMemo, useRef, useCallback } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { Vector3, Frustum, Matrix4 } from 'three';

interface LODNode {
  id: string;
  title: string;
  position: { x: number; y: number; z: number };
  size: number;
  color: string;
  importance?: number;
  category?: string;
}

interface LODLevel {
  distance: number;
  maxNodes: number;
  minSize: number;
  clusterRadius?: number;
}

interface LODSystemProps {
  nodes: LODNode[];
  maxNodes?: number;
  enableFrustumCulling?: boolean;
  enableClustering?: boolean;
  lodLevels?: LODLevel[];
  children: (visibleNodes: LODNode[], lodLevel: number) => React.ReactNode;
}

// Default LOD configuration for 10K+ nodes
const DEFAULT_LOD_LEVELS: LODLevel[] = [
  { distance: 100, maxNodes: 500, minSize: 1.0 },      // Close: High detail
  { distance: 300, maxNodes: 300, minSize: 1.2 },      // Medium: Balanced
  { distance: 600, maxNodes: 150, minSize: 1.5 },      // Far: Low detail
  { distance: 1200, maxNodes: 75, minSize: 2.0, clusterRadius: 50 }, // Very far: Clusters
  { distance: Infinity, maxNodes: 30, minSize: 3.0, clusterRadius: 100 } // Extreme: Major clusters
];

export function LODSystem({ 
  nodes, 
  maxNodes = 300,
  enableFrustumCulling = true,
  enableClustering = true,
  lodLevels = DEFAULT_LOD_LEVELS,
  children 
}: LODSystemProps) {
  const { camera } = useThree();
  const frustumRef = useRef(new Frustum());
  const matrixRef = useRef(new Matrix4());
  
  // Memoized frustum culling
  const frustumCulledNodes = useMemo(() => {
    if (!enableFrustumCulling) return nodes;
    
    // Update frustum
    matrixRef.current.multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse);
    frustumRef.current.setFromProjectionMatrix(matrixRef.current);
    
    // Filter nodes within view frustum
    return nodes.filter(node => {
      const nodePos = new Vector3(node.position.x, node.position.y, node.position.z);
      return frustumRef.current.containsPoint(nodePos);
    });
  }, [nodes, camera.projectionMatrix, camera.matrixWorldInverse, enableFrustumCulling]);
  
  // Advanced clustering for distant views
  const clusterNodes = useCallback((nodes: LODNode[], clusterRadius: number): LODNode[] => {
    if (!enableClustering || !clusterRadius) return nodes;
    
    const clusters: { [key: string]: LODNode[] } = {};
    const clustered: LODNode[] = [];
    
    // Group nodes by spatial proximity
    nodes.forEach(node => {
      const clusterKey = `${Math.floor(node.position.x / clusterRadius)}_${Math.floor(node.position.y / clusterRadius)}_${Math.floor(node.position.z / clusterRadius)}`;
      
      if (!clusters[clusterKey]) {
        clusters[clusterKey] = [];
      }
      clusters[clusterKey].push(node);
    });
    
    // Create cluster representatives
    Object.values(clusters).forEach(clusterNodes => {
      if (clusterNodes.length === 1) {
        clustered.push(clusterNodes[0]);
      } else {
        // Create cluster representative
        const avgPos = clusterNodes.reduce(
          (acc, node) => ({
            x: acc.x + node.position.x / clusterNodes.length,
            y: acc.y + node.position.y / clusterNodes.length,
            z: acc.z + node.position.z / clusterNodes.length
          }),
          { x: 0, y: 0, z: 0 }
        );
        
        const maxImportance = Math.max(...clusterNodes.map(n => n.importance || 0.5));
        const avgSize = clusterNodes.reduce((acc, n) => acc + n.size, 0) / clusterNodes.length;
        
        // Use most important node as representative
        const representative = clusterNodes.reduce((prev, current) => 
          (current.importance || 0.5) > (prev.importance || 0.5) ? current : prev
        );
        
        clustered.push({
          ...representative,
          position: avgPos,
          size: Math.min(avgSize * 1.5, 3.0), // Slightly larger for clusters
          importance: maxImportance,
          title: `${representative.title} (+${clusterNodes.length - 1} more)`
        });
      }
    });
    
    return clustered;
  }, [enableClustering]);
  
  // Main LOD calculation
  const { visibleNodes, currentLodLevel } = useMemo(() => {
    const cameraPos = new Vector3().copy(camera.position);
    const cameraDistance = cameraPos.length(); // Distance from origin
    
    // Determine LOD level based on camera distance
    let lodLevel = 0;
    for (let i = 0; i < lodLevels.length; i++) {
      if (cameraDistance <= lodLevels[i].distance) {
        lodLevel = i;
        break;
      }
      lodLevel = i;
    }
    
    const currentLod = lodLevels[lodLevel];
    let workingNodes = frustumCulledNodes;
    
    // Apply clustering if specified for this LOD level
    if (currentLod.clusterRadius) {
      workingNodes = clusterNodes(workingNodes, currentLod.clusterRadius);
    }
    
    // Filter by minimum size
    workingNodes = workingNodes.filter(node => node.size >= currentLod.minSize);
    
    // Calculate LOD scores
    const nodesWithScores = workingNodes.map(node => {
      const nodePos = new Vector3(node.position.x, node.position.y, node.position.z);
      const distance = cameraPos.distanceTo(nodePos);
      
      // Enhanced scoring algorithm
      const distanceScore = Math.max(0, (2000 - distance) / 2000);
      const importanceScore = node.importance || 0.5;
      const sizeScore = Math.min(node.size / 3, 1);
      const categoryBonus = node.category?.includes('Academic') ? 0.1 : 0;
      
      // Adaptive scoring based on LOD level
      const distanceWeight = Math.max(0.4, 0.8 - lodLevel * 0.1);
      const importanceWeight = Math.min(0.5, 0.2 + lodLevel * 0.1);
      
      const lodScore = 
        (distanceScore * distanceWeight) + 
        (importanceScore * importanceWeight) + 
        (sizeScore * 0.2) + 
        categoryBonus;
      
      return {
        ...node,
        distance,
        lodScore
      };
    });
    
    // Sort and limit nodes
    const finalNodes = nodesWithScores
      .sort((a, b) => b.lodScore - a.lodScore)
      .slice(0, Math.min(currentLod.maxNodes, maxNodes));
    
    return {
      visibleNodes: finalNodes,
      currentLodLevel: lodLevel
    };
  }, [
    frustumCulledNodes, 
    camera.position, 
    lodLevels, 
    maxNodes, 
    clusterNodes
  ]);
  
  return <>{children(visibleNodes, currentLodLevel)}</>;
}
