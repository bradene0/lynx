'use client';

import { useRef, useEffect } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { useGalaxyStore } from '@/stores/galaxy-store';
import { Vector3 } from 'three';

export function CameraController() {
  const { camera } = useThree();
  const { camera: cameraState } = useGalaxyStore();
  const targetPosition = useRef(new Vector3());
  const targetLookAt = useRef(new Vector3());
  const isAnimating = useRef(false);
  const animationProgress = useRef(0);
  const startPosition = useRef(new Vector3());
  const startLookAt = useRef(new Vector3());

  // Update target when camera state changes
  useEffect(() => {
    if (cameraState.animating) {
      // Start animation
      startPosition.current.copy(camera.position);
      startLookAt.current.copy(targetLookAt.current);
      
      targetPosition.current.set(...cameraState.position);
      targetLookAt.current.set(...cameraState.target);
      
      isAnimating.current = true;
      animationProgress.current = 0;
    }
  }, [cameraState.position, cameraState.target, cameraState.animating, camera]);

  useFrame((state, delta) => {
    if (isAnimating.current) {
      // Smooth animation with easing
      animationProgress.current += delta * 0.8; // Animation speed
      
      if (animationProgress.current >= 1) {
        animationProgress.current = 1;
        isAnimating.current = false;
      }
      
      // Easing function (ease-out)
      const t = 1 - Math.pow(1 - animationProgress.current, 3);
      
      // Interpolate camera position
      camera.position.lerpVectors(startPosition.current, targetPosition.current, t);
      
      // Update camera look-at
      const currentLookAt = new Vector3().lerpVectors(startLookAt.current, targetLookAt.current, t);
      camera.lookAt(currentLookAt);
      camera.updateProjectionMatrix();
    }
  });

  return null;
}
