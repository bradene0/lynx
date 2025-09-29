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

// Enhanced color mapping with richer, more vibrant colors
const CATEGORY_COLORS = {
  // Main Wikipedia categories (1000+ concepts each)
  'Science & Technology': '#00D4FF',        // Bright Cyan - innovation
  'History & Philosophy': '#FFB000',        // Rich Gold - ancient wisdom  
  'Arts & Culture': '#FF1493',             // Deep Pink - creativity
  'Life Sciences & Medicine': '#32CD32',   // Lime Green - life
  'Mathematics & Physics': '#FF6347',      // Tomato Red - energy
  'Social Sciences & Economics': '#9932CC', // Dark Orchid - social
  
  // Secondary categories (50-100 concepts each)
  'Life Sciences': '#90EE90',              // Light Green - biology
  'Philosophy & Religion': '#DDA0DD',      // Plum - mystical
  'Arts & Literature': '#FF69B4',          // Hot Pink - artistic
  'Social Sciences': '#BA55D3',            // Medium Orchid - social
  'Physical Sciences': '#FFA500',          // Orange - physics
  'History & Culture': '#DAA520',          // Goldenrod - historical
  'Mathematics & Logic': '#1E90FF',        // Dodger Blue - logic
  'General': '#87CEEB',                    // Sky Blue - neutral
  
  // Academic arXiv categories (80-100 concepts each)
  'Academic - Artificial Intelligence': '#00FFFF',     // Aqua - AI
  'Academic - Machine Learning': '#00CED1',            // Dark Turquoise - ML
  'Academic - Computer Vision': '#48D1CC',             // Medium Turquoise - vision
  'Academic - Computational Linguistics': '#20B2AA',  // Light Sea Green - NLP
  'Academic - Robotics': '#5F9EA0',                    // Cadet Blue - robotics
  'Academic - Cryptography and Security': '#708090',  // Slate Gray - security
  'Academic - Databases': '#778899',                   // Light Slate Gray - data
  'Academic - Data Structures and Algorithms': '#696969', // Dim Gray - algorithms
  
  // Physics & Math academic
  'Academic - Quantum Physics': '#FF4500',            // Orange Red - quantum
  'Academic - General Physics': '#FF6347',            // Tomato - physics
  'Academic - Condensed Matter': '#CD5C5C',           // Indian Red - matter
  'Academic - Astrophysics': '#DC143C',               // Crimson - space
  'Academic - Number Theory': '#4169E1',              // Royal Blue - numbers
  'Academic - Algebraic Geometry': '#0000FF',         // Blue - geometry
  'Academic - Combinatorics': '#6495ED',              // Cornflower Blue - combinatorics
  
  // Life Sciences academic
  'Academic - Biomolecules': '#228B22',               // Forest Green - bio
  'Academic - Genomics': '#32CD32',                   // Lime Green - genetics
  'Academic - Neurons and Cognition': '#9ACD32',     // Yellow Green - neuro
  
  // Economics academic
  'Academic - Theoretical Economics': '#FFD700',      // Gold - economics
  'Academic - Machine Learning Statistics': '#FFA500', // Orange - stats
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

      // Fetch edges (handle gracefully if none exist)
      let edges: Edge[] = [];
      try {
        const edgesResponse = await fetch('/api/edges');
        if (edgesResponse.ok) {
          edges = await edgesResponse.json();
        } else {
          console.warn('No edges available yet - this is normal for new installations');
        }
      } catch (error) {
        console.warn('Edges API not available:', error);
      }

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
      console.log(`🔍 Debug: ${galaxyData.concepts.length} concepts, ${galaxyData.positions.length} positions, ${galaxyData.edges.length} edges`);
      
      // Create position lookup
      const positionMap = new Map(
        galaxyData.positions.map(pos => [pos.concept_id, pos])
      );

      const galaxyNodes: GalaxyNode[] = galaxyData.concepts
        .map(concept => {
          const position = positionMap.get(concept.id);
          if (!position) {
            console.warn(`⚠️ No position found for concept: ${concept.title}`);
            return null;
          }

          // Calculate importance based on connections (we'll update this when we have more data)
        const baseSize = 1.2;
        const randomVariation = 0.3 + Math.random() * 0.4; // 0.3-0.7 variation
        const importanceSize = baseSize + randomVariation;
        
        const galaxyNode: GalaxyNode = {
          ...concept,
          position,
          size: importanceSize,
          color: CATEGORY_COLORS[concept.category as keyof typeof CATEGORY_COLORS] || CATEGORY_COLORS['General'],
        };
        
        return galaxyNode;
        })
        .filter((node): node is GalaxyNode => node !== null);

      // Transform edges
      const galaxyEdges = galaxyData.edges.map(edge => ({
        ...edge,
        visible: true, // All edges visible by default
      }));

      console.log(`✅ Final result: ${galaxyNodes.length} visible nodes, ${galaxyEdges.length} edges`);
      
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
