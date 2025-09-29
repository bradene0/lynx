import { create } from 'zustand';
import { type Concept, type NodePosition, type Edge } from '@lynx/shared';

interface GalaxyNode extends Concept {
  position: NodePosition;
  size: number;
  color: string;
  highlighted?: boolean;
}

interface GalaxyEdge extends Edge {
  visible: boolean;
}

interface CameraState {
  position: [number, number, number];
  target: [number, number, number];
  zoom: number;
  animating?: boolean;
}

interface GalaxyStore {
  // Data
  nodes: GalaxyNode[];
  edges: GalaxyEdge[];
  // UI State
  selectedNode: string | null;
  hoveredNode: string | null;
  searchResults: string[];
  camera: CameraState;
  isLoading: boolean;
  error: string | null;
  edgeThreshold: 'high' | 'medium' | 'low';
  
  // Actions
  setNodes: (nodes: GalaxyNode[]) => void;
  setEdges: (edges: GalaxyEdge[]) => void;
  selectNode: (nodeId: string | null) => void;
  hoverNode: (nodeId: string | null) => void;
  setCameraPosition: (position: [number, number, number]) => void;
  setCameraTarget: (target: [number, number, number]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setEdgeThreshold: (threshold: 'high' | 'medium' | 'low') => void;
  flyToNode: (nodeId: string) => void;
  
  // Search Operations
  highlightSearchResults: (nodeIds: string[]) => void;
  clearSearchHighlight: () => void;
  
  // Galaxy Operations
  showWormholes: (nodeId: string) => void;
  resetView: () => void;
}

export const useGalaxyStore = create<GalaxyStore>((set, get) => ({
  // Initial State
  nodes: [],
  edges: [],
  selectedNode: null,
  hoveredNode: null,
  searchResults: [],
  camera: {
    position: [0, 0, 100],
    target: [0, 0, 0],
    zoom: 1,
  },
  isLoading: false,
  error: null,
  edgeThreshold: 'medium',

  // Basic Actions
  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),
  selectNode: (nodeId) => set({ selectedNode: nodeId }),
  hoverNode: (nodeId) => set({ hoveredNode: nodeId }),
  setSearchResults: (nodeIds: string[]) => set({ searchResults: nodeIds }),
  highlightSearchResults: (nodeIds: string[]) => {
    console.log('✨ Highlighting nodes:', nodeIds); // Debug log
    set({ searchResults: nodeIds });
    // Update nodes to show highlight state
    set((state) => {
      const updatedNodes = state.nodes.map(node => ({
        ...node,
        highlighted: nodeIds.includes(node.id)
      }));
      console.log('✨ Updated nodes with highlighting:', updatedNodes.filter(n => n.highlighted)); // Debug log
      return { nodes: updatedNodes };
    });
  },
  clearSearchHighlight: () => {
    set({ searchResults: [] });
    set((state) => ({
      nodes: state.nodes.map(node => ({
        ...node,
        highlighted: false
      }))
    }));
  },
  setCameraPosition: (position) =>
    set((state) => ({
      camera: { ...state.camera, position }
    })),
  setCameraTarget: (target) => 
    set((state) => ({ 
      camera: { ...state.camera, target } 
    })),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  setEdgeThreshold: (threshold) => set({ edgeThreshold: threshold }),

  // Advanced Actions
  flyToNode: (nodeId) => {
    const { nodes } = get();
    const node = nodes.find(n => n.id === nodeId);
    if (node) {
      // Calculate smooth camera position offset from the node
      const offset = 60; // Distance from the node
      const angle = Math.random() * Math.PI * 2; // Random angle for variety
      const cameraPosition: [number, number, number] = [
        node.position.x + Math.cos(angle) * offset,
        node.position.y + offset * 0.3,
        node.position.z + Math.sin(angle) * offset
      ];
      
      set((state) => ({
        camera: {
          ...state.camera,
          position: cameraPosition,
          target: [node.position.x, node.position.y, node.position.z],
          animating: true, // Flag for smooth animation
        },
        selectedNode: nodeId,
      }));
      
      // Clear animation flag after animation completes
      setTimeout(() => {
        set((state) => ({
          camera: {
            ...state.camera,
            animating: false,
          }
        }));
      }, 1500); // 1.5 second animation
    }
  },

  highlightPath: (path: string[]) => {
    set((state) => ({
      edges: state.edges.map(edge => ({
        ...edge,
        visible: path.includes(edge.source_id) && path.includes(edge.target_id),
      })),
    }));
  },

  showWormholes: (nodeId) => {
    const { edges } = get();
    const wormholeEdges = edges.filter(edge => 
      (edge.source_id === nodeId || edge.target_id === nodeId) &&
      edge.edge_type === 'similarity' &&
      edge.weight > 0.8
    );
    
    set((state) => ({
      edges: state.edges.map(edge => ({
        ...edge,
        visible: wormholeEdges.some(w => w.id === edge.id),
      })),
    }));
  },

  resetView: () => {
    set({
      selectedNode: null,
      hoveredNode: null,
      searchResults: [],
      camera: {
        position: [0, 0, 100],
        target: [0, 0, 0],
        zoom: 1,
      },
      edges: get().edges.map(edge => ({ ...edge, visible: true })),
    });
  },
}));
