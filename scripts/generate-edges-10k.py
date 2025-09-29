#!/usr/bin/env python3
"""
Advanced Edge Generation System for LYNX 10K
Generates semantic similarity edges using SBERT embeddings
"""

import os
import sys
import asyncio
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Set
from datetime import datetime
import uuid
from dotenv import load_dotenv
from tqdm import tqdm
import time

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from scripts.ingestion.database import DatabaseManager
from scripts.ingestion.embedding_generator import EmbeddingGenerator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EdgeGenerator:
    """Advanced edge generation for 10K scale with performance optimization"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.embedder = EmbeddingGenerator()
        
        # Edge generation parameters
        self.similarity_threshold = 0.6  # Minimum cosine similarity
        self.max_edges_per_node = 12     # kNN parameter (k=12)
        self.batch_size = 100            # Process embeddings in batches
        self.edge_types = {
            'semantic': 'similarity',    # SBERT semantic similarity
            'citation': 'citation',      # Future: citation links
            'category': 'category'       # Future: same category links
        }
    
    async def get_embeddings_data(self) -> List[Dict]:
        """Fetch all embeddings with concept metadata"""
        logger.info("📊 Fetching embeddings and concept data...")
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                # Get embeddings with concept info
                cur.execute("""
                    SELECT e.id, e.concept_id, e.embedding, e.model,
                           c.title, c.category, c.source
                    FROM embeddings e
                    JOIN concepts c ON e.concept_id = c.id
                    ORDER BY c.category, c.title
                """)
                
                results = cur.fetchall()
        
        embeddings_data = []
        for row in results:
            emb_id, concept_id, embedding_json, model, title, category, source = row
            
            # Parse embedding vector
            if isinstance(embedding_json, str):
                import json
                embedding_vector = json.loads(embedding_json)
            else:
                embedding_vector = embedding_json
            
            embeddings_data.append({
                'embedding_id': emb_id,
                'concept_id': concept_id,
                'embedding': np.array(embedding_vector, dtype=np.float32),
                'model': model,
                'title': title,
                'category': category,
                'source': source
            })
        
        logger.info(f"✅ Loaded {len(embeddings_data)} embeddings")
        return embeddings_data
    
    def compute_similarity_matrix_batch(self, embeddings: List[np.ndarray], batch_idx: int, total_batches: int) -> np.ndarray:
        """Compute cosine similarity matrix for a batch of embeddings"""
        logger.debug(f"🧮 Computing similarity matrix for batch {batch_idx + 1}/{total_batches}")
        
        # Stack embeddings into matrix
        embedding_matrix = np.vstack(embeddings)
        
        # Normalize for cosine similarity
        norms = np.linalg.norm(embedding_matrix, axis=1, keepdims=True)
        normalized_embeddings = embedding_matrix / (norms + 1e-8)  # Add small epsilon to avoid division by zero
        
        # Compute cosine similarity matrix
        similarity_matrix = np.dot(normalized_embeddings, normalized_embeddings.T)
        
        return similarity_matrix
    
    def find_top_k_similar(self, similarity_matrix: np.ndarray, k: int, threshold: float) -> List[List[Tuple[int, float]]]:
        """Find top-k most similar concepts for each concept"""
        logger.debug(f"🔍 Finding top-{k} similar concepts (threshold: {threshold})")
        
        n_concepts = similarity_matrix.shape[0]
        top_k_results = []
        
        for i in range(n_concepts):
            # Get similarities for concept i (excluding self)
            similarities = similarity_matrix[i].copy()
            similarities[i] = -1  # Exclude self-similarity
            
            # Find indices of top-k similar concepts above threshold
            valid_indices = np.where(similarities >= threshold)[0]
            
            if len(valid_indices) > 0:
                # Sort by similarity (descending) and take top-k
                sorted_indices = valid_indices[np.argsort(similarities[valid_indices])[::-1]]
                top_k_indices = sorted_indices[:k]
                
                # Create list of (index, similarity) tuples
                top_k_for_concept = [(int(idx), float(similarities[idx])) for idx in top_k_indices]
            else:
                top_k_for_concept = []
            
            top_k_results.append(top_k_for_concept)
        
        return top_k_results
    
    async def generate_semantic_edges(self, embeddings_data: List[Dict]) -> List[Dict]:
        """Generate semantic similarity edges using SBERT embeddings"""
        logger.info(f"🔗 Generating semantic edges for {len(embeddings_data)} concepts...")
        
        if len(embeddings_data) == 0:
            logger.warning("⚠️ No embeddings data available")
            return []
        
        # Extract embeddings
        embeddings = [item['embedding'] for item in embeddings_data]
        
        # Compute similarity matrix in batches for memory efficiency
        batch_size = min(self.batch_size, len(embeddings))
        n_batches = (len(embeddings) + batch_size - 1) // batch_size
        
        logger.info(f"📊 Processing {len(embeddings)} embeddings in {n_batches} batches of {batch_size}")
        
        # For now, compute full similarity matrix (optimize later for very large datasets)
        similarity_matrix = self.compute_similarity_matrix_batch(embeddings, 0, 1)
        
        # Find top-k similar concepts for each concept
        top_k_results = self.find_top_k_similar(
            similarity_matrix, 
            self.max_edges_per_node, 
            self.similarity_threshold
        )
        
        # Generate edge records
        edges = []
        edge_count = 0
        
        logger.info("🔗 Creating edge records...")
        for i, similar_concepts in enumerate(tqdm(top_k_results, desc="Generating edges")):
            source_concept = embeddings_data[i]
            
            for target_idx, similarity in similar_concepts:
                target_concept = embeddings_data[target_idx]
                
                # Create bidirectional edges (but avoid duplicates)
                if source_concept['concept_id'] < target_concept['concept_id']:  # Lexicographic ordering to avoid duplicates
                    edge = {
                        'id': str(uuid.uuid4()),
                        'source_id': source_concept['concept_id'],
                        'target_id': target_concept['concept_id'],
                        'weight': float(similarity),
                        'edge_type': 'semantic',
                        'created_at': datetime.now()
                    }
                    edges.append(edge)
                    edge_count += 1
        
        logger.info(f"✅ Generated {len(edges)} semantic edges")
        
        # Log statistics
        if edges:
            weights = [e['weight'] for e in edges]
            logger.info(f"📊 Edge weight statistics:")
            logger.info(f"   • Min similarity: {min(weights):.3f}")
            logger.info(f"   • Max similarity: {max(weights):.3f}")
            logger.info(f"   • Mean similarity: {np.mean(weights):.3f}")
            logger.info(f"   • Edges per concept (avg): {len(edges) * 2 / len(embeddings_data):.1f}")
        
        return edges
    
    async def clear_existing_edges(self):
        """Clear existing edges to regenerate fresh"""
        logger.info("🗑️ Clearing existing edges...")
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM edges")
                conn.commit()
                
        logger.info("✅ Existing edges cleared")
    
    async def insert_edges(self, edges: List[Dict]) -> int:
        """Insert edges into database with batch processing"""
        if not edges:
            logger.warning("⚠️ No edges to insert")
            return 0
        
        logger.info(f"💾 Inserting {len(edges)} edges into database...")
        
        # Prepare edge data for insertion
        edge_data = []
        for edge in edges:
            edge_data.append((
                edge['id'],
                edge['source_id'],
                edge['target_id'],
                edge['weight'],
                edge['edge_type']
            ))
        
        # Insert in batches
        batch_size = 1000
        inserted_count = 0
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                for i in range(0, len(edge_data), batch_size):
                    batch = edge_data[i:i + batch_size]
                    
                    cur.executemany("""
                        INSERT INTO edges (id, source_id, target_id, weight, edge_type)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, batch)
                    
                    inserted_count += len(batch)
                    if i % 5000 == 0:  # Progress update every 5000 edges
                        logger.info(f"   📊 Inserted {inserted_count}/{len(edge_data)} edges...")
                
                conn.commit()
        
        logger.info(f"✅ Successfully inserted {inserted_count} edges")
        return inserted_count
    
    async def generate_all_edges(self, clear_existing: bool = True):
        """Main function to generate all edges"""
        start_time = time.time()
        logger.info("🚀 Starting comprehensive edge generation...")
        
        try:
            # Step 1: Clear existing edges if requested
            if clear_existing:
                await self.clear_existing_edges()
            
            # Step 2: Load embeddings data
            embeddings_data = await self.get_embeddings_data()
            
            if not embeddings_data:
                logger.error("❌ No embeddings found. Run embedding generation first.")
                return
            
            # Step 3: Generate semantic edges
            semantic_edges = await self.generate_semantic_edges(embeddings_data)
            
            # Step 4: Insert edges into database
            if semantic_edges:
                inserted_count = await self.insert_edges(semantic_edges)
                
                # Step 5: Generate statistics
                await self.generate_edge_statistics()
                
                elapsed_time = time.time() - start_time
                logger.info(f"🎉 Edge generation complete!")
                logger.info(f"📊 Final Statistics:")
                logger.info(f"   • Total concepts: {len(embeddings_data)}")
                logger.info(f"   • Total edges: {inserted_count}")
                logger.info(f"   • Average edges per concept: {inserted_count * 2 / len(embeddings_data):.1f}")
                logger.info(f"   • Processing time: {elapsed_time:.1f} seconds")
                logger.info(f"   • Edges per second: {inserted_count / elapsed_time:.1f}")
            else:
                logger.warning("⚠️ No edges generated")
                
        except Exception as e:
            logger.error(f"💥 Edge generation failed: {e}")
            raise
    
    async def generate_edge_statistics(self):
        """Generate and log edge statistics"""
        logger.info("📊 Generating edge statistics...")
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                # Basic edge statistics
                cur.execute("SELECT COUNT(*) FROM edges")
                total_edges = cur.fetchone()[0]
                
                # Weight distribution
                cur.execute("""
                    SELECT MIN(weight), MAX(weight), AVG(weight), STDDEV(weight)
                    FROM edges
                """)
                min_w, max_w, avg_w, std_w = cur.fetchone()
                
                # Edges by type
                cur.execute("""
                    SELECT edge_type, COUNT(*) 
                    FROM edges 
                    GROUP BY edge_type
                """)
                edge_types = cur.fetchall()
                
                # Top connected concepts
                cur.execute("""
                    SELECT c.title, c.category, COUNT(*) as edge_count
                    FROM edges e
                    JOIN concepts c ON (e.source_id = c.id OR e.target_id = c.id)
                    GROUP BY c.id, c.title, c.category
                    ORDER BY edge_count DESC
                    LIMIT 10
                """)
                top_connected = cur.fetchall()
        
        logger.info(f"📈 Edge Statistics:")
        logger.info(f"   • Total edges: {total_edges}")
        logger.info(f"   • Weight range: {min_w:.3f} - {max_w:.3f}")
        logger.info(f"   • Average weight: {avg_w:.3f} (±{std_w:.3f})")
        
        logger.info(f"🏷️ Edges by type:")
        for edge_type, count in edge_types:
            logger.info(f"   • {edge_type}: {count}")
        
        logger.info(f"🌟 Top connected concepts:")
        for title, category, count in top_connected:
            logger.info(f"   • {title} ({category}): {count} edges")

async def main():
    """Main execution function"""
    generator = EdgeGenerator()
    await generator.generate_all_edges(clear_existing=True)

if __name__ == '__main__':
    asyncio.run(main())
