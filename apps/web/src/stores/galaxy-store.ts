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
  highlightSearchResults: (nodeIds: string[]) => void;
  clearSearchHighlight: () => void;
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
  highlightSearchResults: (nodeIds) => {
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
  setCameraTarget: (target) => 
    set((state) => ({ 
      camera: { ...state.camera, target } 
    })),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),

  // Advanced Actions
  flyToNode: (nodeId) => {
    console.log('🌌 FlyToNode called with:', nodeId);
    const { nodes } = get();
    console.log('🌌 Available nodes:', nodes.map(n => ({ id: n.id, title: n.title })));
    const node = nodes.find(n => n.id === nodeId);
    if (node) {
      console.log('🌌 Found node:', node.title, 'at position:', node.position);
      // Calculate camera position offset from the node
      const offset = 50; // Distance from the node
      const cameraPosition: [number, number, number] = [
        node.position.x + offset,
        node.position.y + offset * 0.5,
        node.position.z + offset
      ];
      
      console.log('🌌 Setting camera to:', cameraPosition, 'targeting:', [node.position.x, node.position.y, node.position.z]);
      
      set((state) => ({
        camera: {
          ...state.camera,
          position: cameraPosition,
          target: [node.position.x, node.position.y, node.position.z],
        },
        selectedNode: nodeId,
      }));
    } else {
      console.error('🌌 Node not found:', nodeId);
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
