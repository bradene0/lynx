'use client';

import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { 
  BufferGeometry, 
  Vector3, 
  Color,
  LineBasicMaterial,
  Float32BufferAttribute,
  ShaderMaterial
} from 'three';

interface GalaxyEdge {
  id: string;
  source_id: string;
  target_id: string;
  weight: number;
  edge_type: string;
  threshold_level?: string;
}

interface GalaxyNode {
  id: string;
  title: string;
  position: { x: number; y: number; z: number };
  color: string;
}

interface GalaxyEdgesProps {
  edges: GalaxyEdge[];
  nodes: GalaxyNode[];
  thresholdLevel?: 'high' | 'medium' | 'low';
}

// Simple vertex shader for gradients
const vertexShader = `
  attribute vec3 customColor;
  varying vec3 vColor;
  
  void main() {
    vColor = customColor;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

// Fragment shader with transparency
const fragmentShader = `
  varying vec3 vColor;
  
  void main() {
    gl_FragColor = vec4(vColor, 0.15); // Very transparent
  }
`;

export function GalaxyEdges({ edges, nodes, thresholdLevel = 'medium' }: GalaxyEdgesProps) {
  const materialRef = useRef<ShaderMaterial>(null);
  
  const { geometry, material } = useMemo(() => {
    // Filter edges based on threshold level
    const thresholdMap = {
      'high': 0.25,
      'medium': 0.15,
      'low': 0.05
    };
    
    const minWeight = thresholdMap[thresholdLevel];
    const visibleEdges = edges.filter(edge => edge.weight >= minWeight);
    
    if (visibleEdges.length === 0 || nodes.length === 0) {
      return { geometry: null, material: null };
    }

    // Create node position lookup
    const nodePositions = new Map<string, Vector3>();
    const nodeColors = new Map<string, Color>();
    
    nodes.forEach(node => {
      nodePositions.set(node.id, new Vector3(node.position.x, node.position.y, node.position.z));
      nodeColors.set(node.id, new Color(node.color));
    });
    

    // Create gradient line segments
    const segmentPoints: Vector3[] = [];
    const segmentColors: number[] = [];
    
    visibleEdges.forEach(edge => {
      const sourcePos = nodePositions.get(edge.source_id);
      const targetPos = nodePositions.get(edge.target_id);
      const sourceColor = nodeColors.get(edge.source_id);
      const targetColor = nodeColors.get(edge.target_id);
      
      if (sourcePos && targetPos && sourceColor && targetColor) {
        // Create multiple segments for smooth gradient
        const segments = 10;
        
        for (let i = 0; i < segments; i++) {
          const t1 = i / segments;
          const t2 = (i + 1) / segments;
          
          // Create two points for this segment
          const point1 = new Vector3().lerpVectors(sourcePos, targetPos, t1);
          const point2 = new Vector3().lerpVectors(sourcePos, targetPos, t2);
          
          // Create colors for both points
          const color1 = new Color().lerpColors(sourceColor, targetColor, t1);
          const color2 = new Color().lerpColors(sourceColor, targetColor, t2);
          
          segmentPoints.push(point1, point2);
          segmentColors.push(
            color1.r, color1.g, color1.b,
            color2.r, color2.g, color2.b
          );
        }
      }
    });

    if (segmentPoints.length === 0) {
      return { geometry: null, material: null };
    }

    const geometry = new BufferGeometry();
    geometry.setFromPoints(segmentPoints);
    geometry.setAttribute('customColor', new Float32BufferAttribute(segmentColors, 3));
    
    const material = new ShaderMaterial({
      vertexShader,
      fragmentShader,
      transparent: true,
      depthWrite: false,
      blending: 2, // Additive blending for glow effect
    });

    return { geometry, material };
  }, [edges, nodes, thresholdLevel]);
  
  // Add subtle animation to the lines
  useFrame((state) => {
    if (materialRef.current) {
      // Very subtle opacity breathing effect
      const opacity = 0.15 + Math.sin(state.clock.elapsedTime * 0.3) * 0.05;
      materialRef.current.uniforms = materialRef.current.uniforms || {};
    }
  });

  if (!geometry || !material) {
    return null;
  }

  return (
    <lineSegments geometry={geometry} material={material} />
  );
}
