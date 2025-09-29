"""
SBERT embedding generation for LYNX concepts
Uses sentence-transformers locally (no API costs)
"""

import asyncio
import logging
import os
from typing import List, Dict, Any
import numpy as np
import hashlib
from tqdm import tqdm
import time

try:
    from sentence_transformers import SentenceTransformer
    SBERT_AVAILABLE = True
except ImportError:
    SBERT_AVAILABLE = False
    logging.warning("sentence-transformers not available. Install with: pip install sentence-transformers")

from scripts.ingestion.database import DatabaseManager

logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    """Generates embeddings for concepts using SBERT locally"""
    
    def __init__(self):
        if not SBERT_AVAILABLE:
            raise ImportError("sentence-transformers is required. Install with: pip install sentence-transformers")
        
        # Use the same model as mentioned in memory
        self.model_name = 'all-MiniLM-L6-v2'
        self.model = SentenceTransformer(self.model_name)
        self.dimensions = 384  # all-MiniLM-L6-v2 produces 384-dimensional embeddings
        self.batch_size = 32  # Optimal batch size for SBERT
        self.db = DatabaseManager()
        
    def generate_embedding_id(self, concept_id: str) -> str:
        """Generate a unique embedding ID"""
        content = f"embedding:{concept_id}:{self.model_name}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def prepare_text_for_embedding(self, concept: Dict[str, Any]) -> str:
        """Prepare concept text for embedding generation"""
        # Combine title and summary for richer embeddings
        title = concept.get('title', '')
        summary = concept.get('summary', '')
        category = concept.get('category', '')
        
        # Create a structured text representation
        text_parts = []
        
        if title:
            text_parts.append(f"Title: {title}")
        
        if category:
            text_parts.append(f"Category: {category}")
            
        if summary:
            text_parts.append(f"Summary: {summary}")
        
        combined_text = ' | '.join(text_parts)
        
        # Truncate if too long (SBERT handles up to 512 tokens well)
        max_chars = 2000  # Conservative limit for SBERT
        if len(combined_text) > max_chars:
            combined_text = combined_text[:max_chars] + "..."
        
        return combined_text
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a single text using SBERT"""
        try:
            # SBERT encode method returns numpy array directly
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.astype(np.float32)
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def generate_batch_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for a batch of texts using SBERT"""
        try:
            # SBERT can handle batch processing efficiently
            embeddings = self.model.encode(texts, convert_to_numpy=True, batch_size=self.batch_size)
            
            # Convert to list of individual arrays
            return [embedding.astype(np.float32) for embedding in embeddings]
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise
    
    async def generate_embeddings(self, concepts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate embeddings for all concepts"""
        logger.info(f"Generating embeddings for {len(concepts)} concepts")
        
        # First, store concepts in database
        await self.db.insert_concepts(concepts)
        
        # Check for existing embeddings to avoid regeneration
        existing_concept_ids = set(await self.db.get_existing_concepts())
        concepts_to_process = [
            concept for concept in concepts 
            if concept['id'] in existing_concept_ids
        ]
        
        logger.info(f"Processing {len(concepts_to_process)} concepts for embeddings")
        
        all_embeddings = []
        processed = 0
        
        # Process in batches
        for i in range(0, len(concepts_to_process), self.batch_size):
            batch = concepts_to_process[i:i + self.batch_size]
            
            try:
                # Prepare texts for this batch
                texts = [self.prepare_text_for_embedding(concept) for concept in batch]
                
                logger.info(f"Generating embeddings for batch {i//self.batch_size + 1}/{(len(concepts_to_process) + self.batch_size - 1)//self.batch_size}")
                
                # Generate embeddings (SBERT is synchronous)
                embeddings = self.generate_batch_embeddings(texts)
                
                # Create embedding records
                batch_embeddings = []
                for concept, embedding in zip(batch, embeddings):
                    embedding_record = {
                        'id': self.generate_embedding_id(concept['id']),
                        'concept_id': concept['id'],
                        'embedding': embedding.tolist(),  # Convert to list for JSON storage
                        'model': self.model_name
                    }
                    batch_embeddings.append(embedding_record)
                
                # Store embeddings in database
                await self.db.insert_embeddings(batch_embeddings)
                all_embeddings.extend(batch_embeddings)
                
                processed += len(batch)
                logger.info(f"Processed {processed}/{len(concepts_to_process)} concepts")
                
                # Small delay for database (no API rate limiting needed)
                await asyncio.sleep(0.01)
                
            except Exception as e:
                logger.error(f"Error processing batch {i//self.batch_size + 1}: {e}")
                # Continue with next batch
                continue
        
        logger.info(f"Embedding generation complete: {len(all_embeddings)} embeddings created")
        return all_embeddings
    
    async def compute_similarity_matrix(self, embeddings: List[Dict[str, Any]]) -> np.ndarray:
        """Compute cosine similarity matrix for embeddings"""
        logger.info("Computing similarity matrix...")
        
        # Convert embeddings to numpy array
        embedding_vectors = np.array([emb['embedding'] for emb in embeddings])
        
        # Normalize vectors for cosine similarity
        norms = np.linalg.norm(embedding_vectors, axis=1, keepdims=True)
        normalized_embeddings = embedding_vectors / norms
        
        # Compute cosine similarity matrix
        similarity_matrix = np.dot(normalized_embeddings, normalized_embeddings.T)
        
        logger.info(f"Similarity matrix computed: {similarity_matrix.shape}")
        return similarity_matrix
    
    async def find_similar_concepts(
        self, 
        concept_id: str, 
        embeddings: List[Dict[str, Any]], 
        k: int = 12,
        threshold: float = 0.6
    ) -> List[Dict[str, Any]]:
        """Find k most similar concepts to a given concept"""
        
        # Find the target embedding
        target_embedding = None
        target_index = None
        
        for i, emb in enumerate(embeddings):
            if emb['concept_id'] == concept_id:
                target_embedding = np.array(emb['embedding'])
                target_index = i
                break
        
        if target_embedding is None:
            return []
        
        # Compute similarities with all other embeddings
        similarities = []
        for i, emb in enumerate(embeddings):
            if i == target_index:
                continue
                
            other_embedding = np.array(emb['embedding'])
            
            # Cosine similarity
            similarity = np.dot(target_embedding, other_embedding) / (
                np.linalg.norm(target_embedding) * np.linalg.norm(other_embedding)
            )
            
            if similarity >= threshold:
                similarities.append({
                    'concept_id': emb['concept_id'],
                    'similarity': float(similarity)
                })
        
        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:k]
