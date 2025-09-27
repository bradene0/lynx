"""
SBERT embedding generation for LYNX concepts
Uses sentence-transformers for local, cost-free embeddings
"""

import asyncio
import logging
import hashlib
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from scripts.ingestion.database import DatabaseManager

logger = logging.getLogger(__name__)

class SBERTEmbeddingGenerator:
    """Generates embeddings for concepts using SBERT locally"""
    
    def __init__(self):
        self.model_name = 'all-MiniLM-L6-v2'
        self.dimensions = 384  # SBERT dimension
        self.batch_size = 32  # Process in batches for efficiency
        self.db = DatabaseManager()
        
        # Load the model
        logger.info(f"Loading SBERT model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        logger.info("✅ SBERT model loaded successfully")
        
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
        
        # SBERT handles longer texts better than OpenAI, but still truncate if extremely long
        max_chars = 5000
        if len(combined_text) > max_chars:
            combined_text = combined_text[:max_chars] + "..."
        
        return combined_text
    
    async def generate_embeddings(self, concepts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate embeddings for all concepts"""
        logger.info(f"Generating SBERT embeddings for {len(concepts)} concepts")
        
        # First, store concepts in database
        await self.db.insert_concepts(concepts)
        
        # Check for existing embeddings to avoid regeneration
        existing_concept_ids = set(await self.db.get_existing_concepts())
        concepts_to_process = [
            concept for concept in concepts 
            if concept['id'] in existing_concept_ids
        ]
        
        logger.info(f"Processing {len(concepts_to_process)} concepts for embeddings")
        
        # Prepare all texts
        texts = [self.prepare_text_for_embedding(concept) for concept in concepts_to_process]
        
        # Generate embeddings in batches
        all_embeddings = []
        
        logger.info("Generating embeddings with SBERT...")
        for i in tqdm(range(0, len(texts), self.batch_size), desc="Processing batches"):
            batch_texts = texts[i:i + self.batch_size]
            batch_concepts = concepts_to_process[i:i + self.batch_size]
            
            # Generate embeddings for this batch
            batch_embeddings = self.model.encode(
                batch_texts,
                batch_size=self.batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True  # Important for cosine similarity
            )
            
            # Create embedding records
            batch_embedding_records = []
            for concept, embedding in zip(batch_concepts, batch_embeddings):
                embedding_record = {
                    'id': self.generate_embedding_id(concept['id']),
                    'concept_id': concept['id'],
                    'embedding': embedding.tolist(),  # Convert to list for JSON storage
                    'model': self.model_name
                }
                batch_embedding_records.append(embedding_record)
            
            # Store embeddings in database
            await self.db.insert_embeddings(batch_embedding_records)
            all_embeddings.extend(batch_embedding_records)
            
            logger.info(f"Processed {min(i + self.batch_size, len(texts))}/{len(texts)} concepts")
        
        logger.info(f"SBERT embedding generation complete: {len(all_embeddings)} embeddings created")
        return all_embeddings
    
    async def compute_similarity_matrix(self, embeddings: List[Dict[str, Any]]) -> np.ndarray:
        """Compute cosine similarity matrix for embeddings"""
        logger.info("Computing similarity matrix...")
        
        # Convert embeddings to numpy array
        embedding_vectors = np.array([emb['embedding'] for emb in embeddings])
        
        # Since we normalized during encoding, we can use dot product for cosine similarity
        similarity_matrix = np.dot(embedding_vectors, embedding_vectors.T)
        
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
            
            # Since embeddings are normalized, dot product = cosine similarity
            similarity = float(np.dot(target_embedding, other_embedding))
            
            if similarity >= threshold:
                similarities.append({
                    'concept_id': emb['concept_id'],
                    'similarity': similarity
                })
        
        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:k]
