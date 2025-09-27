'use client';

import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useGalaxyStore } from '@/stores/galaxy-store';
import { type Concept, type NodePosition, type Edge } from '@lynx/shared';

interface GalaxyData {
  concepts: Concept[];
  positions: NodePosition[];
  edges: Edge[];
}

interface GalaxyNode extends Concept {
  position: NodePosition;
  size: number;
  color: string;
}

// Color mapping for different categories
const CATEGORY_COLORS = {
  'Science & Technology': '#00D4FF', // Cyan
  'History': '#FFB800',              // Gold
  'Arts & Culture': '#FF6B9D',       // Pink
  'Philosophy & Religion': '#9B59B6', // Purple
  'Geography': '#2ECC71',            // Green
  'General': '#95A5A6',              // Gray
} as const;

export function useGalaxyData() {
  const { 
    setNodes, 
    setEdges, 
    setLoading, 
    setError,
    nodes,
    isLoading 
  } = useGalaxyStore();

  // Fetch concepts with positions
  const { data: galaxyData, error, isLoading: queryLoading } = useQuery({
    queryKey: ['galaxy-data'],
    queryFn: async (): Promise<GalaxyData> => {
      // Fetch concepts
      const conceptsResponse = await fetch('/api/concepts');
      if (!conceptsResponse.ok) {
        throw new Error('Failed to fetch concepts');
      }
      const concepts: Concept[] = await conceptsResponse.json();

      // Fetch positions
      const positionsResponse = await fetch('/api/positions');
      if (!positionsResponse.ok) {
        throw new Error('Failed to fetch positions');
      }
      const positions: NodePosition[] = await positionsResponse.json();

      // Fetch edges
      const edgesResponse = await fetch('/api/edges');
      if (!edgesResponse.ok) {
        throw new Error('Failed to fetch edges');
      }
      const edges: Edge[] = await edgesResponse.json();

      return { concepts, positions, edges };
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
  });

  // Transform data when it changes
  useEffect(() => {
    if (queryLoading) {
      setLoading(true);
      return;
    }

    if (error) {
      setError(error.message);
      setLoading(false);
      return;
    }

    if (galaxyData) {
      // Create position lookup
      const positionMap = new Map(
        galaxyData.positions.map(pos => [pos.concept_id, pos])
      );

      // Transform concepts to galaxy nodes
      const galaxyNodes: GalaxyNode[] = galaxyData.concepts
        .map(concept => {
          const position = positionMap.get(concept.id);
          if (!position) return null;

          return {
            ...concept,
            position,
            size: calculateNodeSize(concept),
            color: getCategoryColor(concept.category),
          };
        })
        .filter((node): node is GalaxyNode => node !== null);

      // Transform edges
      const galaxyEdges = galaxyData.edges.map(edge => ({
        ...edge,
        visible: true,
      }));

      setNodes(galaxyNodes);
      setEdges(galaxyEdges);
      setLoading(false);
      setError(null);
    }
  }, [galaxyData, error, queryLoading, setNodes, setEdges, setLoading, setError]);

  return {
    nodes,
    isLoading: queryLoading || isLoading,
    error,
    refetch: () => {
      // This will be handled by React Query
    },
  };
}

function calculateNodeSize(concept: Concept): number {
  // Base size
  let size = 1.0;
  
  // Increase size based on summary length (proxy for importance)
  const summaryLength = concept.summary?.length || 0;
  if (summaryLength > 1000) size *= 1.5;
  else if (summaryLength > 500) size *= 1.2;
  
  // Increase size for certain sources
  if (concept.source === 'wikipedia') size *= 1.1;
  
  return Math.max(0.5, Math.min(3.0, size));
}

function getCategoryColor(category?: string): string {
  if (!category) return CATEGORY_COLORS['General'];
  
  return CATEGORY_COLORS[category as keyof typeof CATEGORY_COLORS] || CATEGORY_COLORS['General'];
}
