'use client';

import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { InstancedMesh, Object3D, Color } from 'three';
import { useGalaxyStore } from '@/stores/galaxy-store';

interface GalaxyNode {
  id: string;
  title: string;
  position: { x: number; y: number; z: number };
  size: number;
  color: string;
  highlighted?: boolean;
}

interface GalaxyNodesProps {
  nodes: GalaxyNode[];
  selectedNode: string | null;
  nodeClickedRef: React.MutableRefObject<boolean>;
}

export function GalaxyNodes({ nodes, selectedNode, nodeClickedRef }: GalaxyNodesProps) {
  const meshRef = useRef<InstancedMesh>(null);
  const glowMeshRef = useRef<InstancedMesh>(null);
  const { hoverNode, selectNode } = useGalaxyStore();
  
  const dummy = new Object3D();
  const color = new Color();
  const glowColor = new Color();

  useFrame((state) => {
    if (!meshRef.current) return;

    // Update each instance
    nodes.forEach((node, index) => {
      dummy.position.set(node.position.x, node.position.y, node.position.z);
      
      // Add subtle rotation for planet-like effect
      dummy.rotation.y = state.clock.elapsedTime * 0.1 + index * 0.1;
      dummy.rotation.x = Math.sin(state.clock.elapsedTime * 0.05 + index) * 0.1;
      
      // Scale based on selection/hover/highlight state
      const isSelected = selectedNode === node.id;
      const isHighlighted = node.highlighted;
      
      // Visual feedback for highlighted nodes
      
      let scale = node.size;
      if (isSelected) {
        // Add pulsing effect to selected nodes
        const pulse = 1 + Math.sin(state.clock.elapsedTime * 3) * 0.1;
        scale *= 1.5 * pulse; // Selected nodes are largest with pulse
      } else if (isHighlighted) {
        scale *= 1.2; // Highlighted nodes are slightly larger
      }
      
      dummy.scale.setScalar(scale);
      dummy.updateMatrix();
      meshRef.current!.setMatrixAt(index, dummy.matrix);
      
      // Set color - keep original color, don't change it
      color.set(node.color);
      
      // Note: Glow effect will be handled by separate glow spheres
      // Keep the original node color intact
      
      meshRef.current!.setColorAt(index, color);
      
      // Update glow spheres
      if (glowMeshRef.current) {
        if (isSelected || isHighlighted) {
          // Position glow sphere at same location but larger and softer
          dummy.scale.setScalar(scale * 2.5); // Bigger, softer glow
          dummy.updateMatrix();
          glowMeshRef.current.setMatrixAt(index, dummy.matrix);
          
          // Set glow color - much more subtle
          if (isSelected) {
            glowColor.set('#87CEEB'); // Soft sky blue for selected
          } else if (isHighlighted) {
            glowColor.set('#FFD700'); // Gold for highlighted
          }
          glowColor.multiplyScalar(0.15); // Much more subtle
          glowMeshRef.current.setColorAt(index, glowColor);
        } else {
          // No glow - make it invisible
          dummy.scale.setScalar(0.001); // Almost invisible
          dummy.updateMatrix();
          glowMeshRef.current.setMatrixAt(index, dummy.matrix);
          glowColor.set('#000000');
          glowColor.multiplyScalar(0);
          glowMeshRef.current.setColorAt(index, glowColor);
        }
      }
    });

    meshRef.current.instanceMatrix.needsUpdate = true;
    if (meshRef.current.instanceColor) {
      meshRef.current.instanceColor.needsUpdate = true;
    }
    
    if (glowMeshRef.current) {
      glowMeshRef.current.instanceMatrix.needsUpdate = true;
      if (glowMeshRef.current.instanceColor) {
        glowMeshRef.current.instanceColor.needsUpdate = true;
      }
    }
  });

  const handleClick = (event: any) => {
    console.log('🪐 Node click event:', event);
    console.log('🪐 Instance ID:', event.instanceId);
    console.log('🪐 Available nodes:', nodes.length);
    
    // Set flag to prevent canvas click handler
    nodeClickedRef.current = true;
    
    // Stop event propagation
    event.stopPropagation();
    
    const instanceId = event.instanceId;
    
    if (instanceId !== undefined && nodes[instanceId]) {
      const clickedNodeId = nodes[instanceId].id;
      console.log('🪐 Clicking node:', clickedNodeId, nodes[instanceId].title);
      
      // Toggle selection: if already selected, deselect; otherwise select
      if (selectedNode === clickedNodeId) {
        console.log('🪐 Deselecting node');
        selectNode(null); // Deselect
      } else {
        console.log('🪐 Selecting node');
        selectNode(clickedNodeId); // Select new node
      }
    } else {
      console.log('🪐 No valid node found for instance:', instanceId);
    }
  };
  
  // Handle clicking on empty space to deselect
  const handleBackgroundClick = () => {
    selectNode(null);
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
    <group>
      {/* Main node spheres */}
      <instancedMesh
        ref={meshRef}
        args={[undefined, undefined, nodes.length]}
        onClick={handleClick}
        onPointerOver={handlePointerOver}
        onPointerOut={handlePointerOut}
      >
        <sphereGeometry args={[1, 32, 32]} />
        <meshStandardMaterial 
          metalness={0.3}
          roughness={0.4}
          emissive={0x111111}
          emissiveIntensity={0.1}
        />
      </instancedMesh>
      
      {/* Glow effect spheres */}
      <instancedMesh
        ref={glowMeshRef}
        args={[undefined, undefined, nodes.length]}
        renderOrder={-1} // Render behind main spheres
      >
        <sphereGeometry args={[1, 12, 12]} />
        <meshBasicMaterial 
          transparent 
          opacity={0.6}
          blending={2} // Additive blending for glow effect
          depthWrite={false} // Don't write to depth buffer for softer effect
        />
      </instancedMesh>
      
      {/* Note: Background click handled by galaxy visualization component */}
    </group>
  );
}
