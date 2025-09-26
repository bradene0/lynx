"""
Graph construction and layout computation for LYNX
Builds kNN similarity graph and computes node positions using ForceAtlas2
"""

import asyncio
import logging
import hashlib
from typing import List, Dict, Any, Tuple
import numpy as np
import networkx as nx
from sklearn.neighbors import NearestNeighbors
from fa2 import ForceAtlas2
import random

from scripts.ingestion.database import DatabaseManager

logger = logging.getLogger(__name__)

class GraphBuilder:
    """Builds knowledge graph and computes layout positions"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.k_neighbors = 12  # kNN parameter
        self.similarity_threshold = 0.6
        self.max_neighbors = 20  # Cap for performance
        
    def generate_edge_id(self, source_id: str, target_id: str, edge_type: str) -> str:
        """Generate a unique edge ID"""
        content = f"edge:{source_id}:{target_id}:{edge_type}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def build_similarity_graph(
        self, 
        concepts: List[Dict[str, Any]], 
        embeddings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Build kNN similarity graph from embeddings"""
        logger.info("Building similarity graph...")
        
        # Create mapping from concept_id to embedding
        embedding_map = {emb['concept_id']: emb for emb in embeddings}
        
        # Filter concepts that have embeddings
        valid_concepts = [
            concept for concept in concepts 
            if concept['id'] in embedding_map
        ]
        
        logger.info(f"Building graph for {len(valid_concepts)} concepts with embeddings")
        
        # Prepare embedding matrix
        embedding_vectors = []
        concept_ids = []
        
        for concept in valid_concepts:
            embedding = embedding_map[concept['id']]
            embedding_vectors.append(embedding['embedding'])
            concept_ids.append(concept['id'])
        
        embedding_matrix = np.array(embedding_vectors)
        
        # Build kNN index
        logger.info("Computing k-nearest neighbors...")
        nbrs = NearestNeighbors(
            n_neighbors=min(self.k_neighbors + 1, len(embedding_vectors)),  # +1 because it includes self
            metric='cosine',
            algorithm='brute'  # More accurate for high-dimensional data
        ).fit(embedding_matrix)
        
        # Find neighbors for each concept
        distances, indices = nbrs.kneighbors(embedding_matrix)
        
        edges = []
        
        for i, concept_id in enumerate(concept_ids):
            # Skip self (first neighbor)
            neighbor_distances = distances[i][1:]
            neighbor_indices = indices[i][1:]
            
            for j, (distance, neighbor_idx) in enumerate(zip(neighbor_distances, neighbor_indices)):
                # Convert cosine distance to similarity
                similarity = 1.0 - distance
                
                if similarity >= self.similarity_threshold:
                    neighbor_id = concept_ids[neighbor_idx]
                    
                    edge = {
                        'id': self.generate_edge_id(concept_id, neighbor_id, 'similarity'),
                        'source_id': concept_id,
                        'target_id': neighbor_id,
                        'weight': float(similarity),
                        'edge_type': 'similarity'
                    }
                    edges.append(edge)
        
        logger.info(f"Created {len(edges)} similarity edges")
        return edges
    
    async def build_category_graph(self, concepts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build edges between concepts in the same category"""
        logger.info("Building category-based edges...")
        
        # Group concepts by category
        category_groups = {}
        for concept in concepts:
            category = concept.get('category', 'General')
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(concept)
        
        edges = []
        
        for category, category_concepts in category_groups.items():
            if len(category_concepts) < 2:
                continue
                
            logger.info(f"Creating category edges for {category}: {len(category_concepts)} concepts")
            
            # Create edges between concepts in the same category
            # Use a lower weight than similarity edges
            for i, concept1 in enumerate(category_concepts):
                for j, concept2 in enumerate(category_concepts[i+1:], i+1):
                    # Random sampling to avoid too many edges
                    if random.random() < 0.1:  # 10% chance
                        edge = {
                            'id': self.generate_edge_id(concept1['id'], concept2['id'], 'category'),
                            'source_id': concept1['id'],
                            'target_id': concept2['id'],
                            'weight': 0.3,  # Lower weight than similarity
                            'edge_type': 'category'
                        }
                        edges.append(edge)
        
        logger.info(f"Created {len(edges)} category edges")
        return edges
    
    async def build_graph(
        self, 
        concepts: List[Dict[str, Any]], 
        embeddings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Build complete knowledge graph"""
        logger.info("Building complete knowledge graph...")
        
        # Build similarity edges
        similarity_edges = await self.build_similarity_graph(concepts, embeddings)
        
        # Build category edges
        category_edges = await self.build_category_graph(concepts)
        
        # Combine all edges
        all_edges = similarity_edges + category_edges
        
        # Store edges in database
        await self.db.insert_edges(all_edges)
        
        logger.info(f"Graph construction complete: {len(all_edges)} total edges")
        return all_edges
    
    async def compute_positions(
        self, 
        concepts: List[Dict[str, Any]], 
        edges: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Compute 3D positions using ForceAtlas2 algorithm"""
        logger.info("Computing node positions with ForceAtlas2...")
        
        # Create NetworkX graph
        G = nx.Graph()
        
        # Add nodes
        for concept in concepts:
            G.add_node(concept['id'], **concept)
        
        # Add edges
        for edge in edges:
            G.add_edge(
                edge['source_id'], 
                edge['target_id'], 
                weight=edge['weight'],
                edge_type=edge['edge_type']
            )
        
        logger.info(f"Created NetworkX graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        
        # Use ForceAtlas2 for layout
        forceatlas2 = ForceAtlas2(
            # Behavior alternatives
            outboundAttractionDistribution=True,  # Dissuade hubs
            linLogMode=False,  # NOT in LinLog mode
            adjustSizes=False,  # Prevent overlap (NOT IMPLEMENTED)
            edgeWeightInfluence=1.0,  # Use edge weights
            
            # Performance
            jitterTolerance=1.0,  # Tolerance
            barnesHutOptimize=True,
            barnesHutTheta=1.2,
            multiThreaded=False,  # NOT IMPLEMENTED
            
            # Tuning
            scalingRatio=2.0,
            strongGravityMode=False,
            gravity=1.0,
            
            # Log
            verbose=True
        )
        
        # Get initial positions (random)
        pos = nx.spring_layout(G, dim=2, k=1, iterations=50)
        
        # Convert to the format expected by ForceAtlas2
        positions = [[pos[node][0], pos[node][1]] for node in G.nodes()]
        
        # Run ForceAtlas2
        logger.info("Running ForceAtlas2 layout algorithm...")
        positions = forceatlas2.forceatlas2_networkx_layout(
            G, pos=None, iterations=1000
        )
        
        # Convert 2D positions to 3D and add some Z variation
        position_records = []
        node_list = list(G.nodes())
        
        for i, node_id in enumerate(node_list):
            if node_id in positions:
                x, y = positions[node_id]
                
                # Add Z dimension based on node properties
                concept = next(c for c in concepts if c['id'] == node_id)
                category = concept.get('category', 'General')
                
                # Assign Z levels by category for visual separation
                z_levels = {
                    'Science & Technology': 20,
                    'History': 0,
                    'Arts & Culture': -20,
                    'Philosophy & Religion': 10,
                    'Geography': -10,
                    'General': 5
                }
                
                base_z = z_levels.get(category, 0)
                z = base_z + random.uniform(-5, 5)  # Add some variation
                
                # Scale positions for better visualization
                scale_factor = 100
                x *= scale_factor
                y *= scale_factor
                
                position_record = {
                    'concept_id': node_id,
                    'x': float(x),
                    'y': float(y),
                    'z': float(z),
                    'cluster_id': category  # Use category as cluster for now
                }
                position_records.append(position_record)
        
        # Store positions in database
        await self.db.insert_positions(position_records)
        
        logger.info(f"Position computation complete: {len(position_records)} positions computed")
        return position_records
    
    async def detect_communities(self, concepts: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> Dict[str, str]:
        """Detect communities in the graph for clustering"""
        logger.info("Detecting communities...")
        
        # Create NetworkX graph
        G = nx.Graph()
        
        # Add nodes and edges
        for concept in concepts:
            G.add_node(concept['id'])
        
        for edge in edges:
            if edge['edge_type'] == 'similarity':  # Only use similarity edges
                G.add_edge(edge['source_id'], edge['target_id'], weight=edge['weight'])
        
        # Use Louvain community detection
        try:
            import community as community_louvain
            partition = community_louvain.best_partition(G)
            logger.info(f"Detected {len(set(partition.values()))} communities")
            return partition
        except ImportError:
            logger.warning("Community detection library not available, using categories")
            # Fallback to categories
            partition = {}
            for concept in concepts:
                partition[concept['id']] = concept.get('category', 'General')
            return partition
