import { create } from 'zustand';
import { type Concept, type NodePosition, type Edge } from '@lynx/shared';

interface GalaxyNode extends Concept {
  position: NodePosition;
  size: number;
  color: string;
}

interface GalaxyEdge extends Edge {
  visible: boolean;
}

interface CameraState {
  position: [number, number, number];
  target: [number, number, number];
  zoom: number;
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
  
  // Loading States
  isLoading: boolean;
  error: string | null;
  
  // Actions
  setNodes: (nodes: GalaxyNode[]) => void;
  setEdges: (edges: GalaxyEdge[]) => void;
  selectNode: (nodeId: string | null) => void;
  hoverNode: (nodeId: string | null) => void;
  setSearchResults: (nodeIds: string[]) => void;
  setCameraTarget: (target: [number, number, number]) => void;
  flyToNode: (nodeId: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  
  // Galaxy Operations
  highlightPath: (path: string[]) => void;
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

  // Basic Actions
  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),
  selectNode: (nodeId) => set({ selectedNode: nodeId }),
  hoverNode: (nodeId) => set({ hoveredNode: nodeId }),
  setSearchResults: (nodeIds) => set({ searchResults: nodeIds }),
  setCameraTarget: (target) => 
    set((state) => ({ 
      camera: { ...state.camera, target } 
    })),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),

  // Advanced Actions
  flyToNode: (nodeId) => {
    const { nodes } = get();
    const node = nodes.find(n => n.id === nodeId);
    if (node) {
      set((state) => ({
        camera: {
          ...state.camera,
          target: [node.position.x, node.position.y, node.position.z],
        },
        selectedNode: nodeId,
      }));
    }
  },

  highlightPath: (path) => {
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
