#!/usr/bin/env python3
"""
Build similarity edges between concepts using SBERT embeddings
"""

import os
import sys
import asyncio
import logging
import numpy as np
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict, Tuple
import uuid

# Load environment variables
load_dotenv()

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from scripts.ingestion.database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimilarityEdgeBuilder:
    def __init__(self):
        self.db = DatabaseManager()
    
    async def get_concepts_with_embeddings(self) -> List[Dict]:
        """Get all concepts with their SBERT embeddings"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        c.id, c.title, c.category,
                        e.embedding
                    FROM concepts c
                    JOIN embeddings e ON c.id = e.concept_id
                    ORDER BY c.created_at
                """)
                
                results = []
                for row in cur.fetchall():
                    concept_id, title, category, embedding_str = row
                    
                    # Parse embedding from string representation
                    # Remove brackets and split by comma
                    embedding_clean = embedding_str.strip('[]')
                    embedding_values = [float(x.strip()) for x in embedding_clean.split(',')]
                    embedding_array = np.array(embedding_values)
                    
                    results.append({
                        'id': concept_id,
                        'title': title,
                        'category': category or 'General',
                        'embedding': embedding_array
                    })
                
                logger.info(f"Loaded {len(results)} concepts with embeddings")
                return results
    
    def calculate_cosine_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings"""
        # Normalize the embeddings
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # Calculate cosine similarity
        similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
        return float(similarity)
    
    def build_edges(self, concepts: List[Dict], min_similarity: float = 0.3) -> List[Dict]:
        """Build edges between concepts based on similarity"""
        edges = []
        
        logger.info(f"Building edges with minimum similarity: {min_similarity}")
        
        for i, concept1 in enumerate(concepts):
            for j, concept2 in enumerate(concepts):
                if i >= j:  # Skip self and duplicate pairs
                    continue
                
                similarity = self.calculate_cosine_similarity(
                    concept1['embedding'], 
                    concept2['embedding']
                )
                
                if similarity >= min_similarity:
                    edge = {
                        'id': str(uuid.uuid4()),
                        'source_id': concept1['id'],
                        'target_id': concept2['id'],
                        'weight': similarity,
                        'edge_type': 'similarity'
                    }
                    edges.append(edge)
                    
                    logger.info(
                        f"Edge: {concept1['title']} ↔ {concept2['title']} "
                        f"(similarity: {similarity:.3f})"
                    )
        
        logger.info(f"Created {len(edges)} similarity edges")
        return edges
    
    async def store_edges(self, edges: List[Dict]) -> int:
        """Store edges in the database"""
        if not edges:
            logger.warning("No edges to store")
            return 0
        
        # Clear existing similarity edges
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM edges WHERE edge_type = 'similarity'")
                logger.info("Cleared existing similarity edges")
        
        # Insert new edges
        return await self.db.insert_edges(edges)
    
    async def build_all_similarity_edges(self):
        """Main function to build all similarity edges"""
        logger.info("🔗 Building similarity edges between concepts...")
        
        # Get concepts with embeddings
        concepts = await self.get_concepts_with_embeddings()
        
        if len(concepts) < 2:
            logger.error("Need at least 2 concepts to build edges")
            return
        
        # Build edges with different thresholds
        thresholds = {
            'high': 0.7,      # Only very similar concepts
            'medium': 0.5,    # Moderately similar concepts  
            'low': 0.3        # More exploratory connections
        }
        
        all_edges = []
        
        for threshold_name, threshold_value in thresholds.items():
            logger.info(f"\n--- Building {threshold_name} similarity edges (threshold: {threshold_value}) ---")
            threshold_edges = self.build_edges(concepts, threshold_value)
            
            # Add threshold info to edges
            for edge in threshold_edges:
                edge['threshold_level'] = threshold_name
            
            all_edges.extend(threshold_edges)
        
        # Remove duplicates (keep highest threshold version)
        unique_edges = {}
        for edge in all_edges:
            key = f"{edge['source_id']}-{edge['target_id']}"
            reverse_key = f"{edge['target_id']}-{edge['source_id']}"
            
            # Use the key that comes first alphabetically for consistency
            edge_key = key if key < reverse_key else reverse_key
            
            if edge_key not in unique_edges or edge['weight'] > unique_edges[edge_key]['weight']:
                unique_edges[edge_key] = edge
        
        final_edges = list(unique_edges.values())
        logger.info(f"\n🎯 Final unique edges: {len(final_edges)}")
        
        # Store edges in database
        stored_count = await self.store_edges(final_edges)
        
        logger.info(f"✅ Successfully stored {stored_count} similarity edges")
        
        # Print summary
        logger.info("\n📊 Edge Summary:")
        for edge in final_edges:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT title FROM concepts WHERE id = %s", (edge['source_id'],))
                    source_title = cur.fetchone()[0]
                    cur.execute("SELECT title FROM concepts WHERE id = %s", (edge['target_id'],))
                    target_title = cur.fetchone()[0]
                    
                    logger.info(
                        f"  {source_title} ↔ {target_title} "
                        f"(similarity: {edge['weight']:.3f}, level: {edge.get('threshold_level', 'unknown')})"
                    )

async def main():
    builder = SimilarityEdgeBuilder()
    await builder.build_all_similarity_edges()

if __name__ == '__main__':
    asyncio.run(main())
