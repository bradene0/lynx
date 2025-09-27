"""
Embedding generation using SBERT for LYNX
"""

import numpy as np
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """Initialize the embedding generator with SBERT model"""
        self.model_name = model_name
        logger.info(f"Loading SBERT model: {model_name}")
        self.model = SentenceTransformer(model_name)
        logger.info("✅ SBERT model loaded successfully")
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a single text"""
        try:
            # Clean the text
            cleaned_text = text.strip().replace('\n', ' ')
            
            # Generate embedding
            embedding = self.model.encode(cleaned_text)
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            # Return zero vector as fallback
            return np.zeros(384)  # MiniLM has 384 dimensions
    
    def generate_batch_embeddings(self, texts: list) -> list:
        """Generate embeddings for multiple texts efficiently"""
        try:
            # Clean texts
            cleaned_texts = [text.strip().replace('\n', ' ') for text in texts]
            
            # Generate embeddings in batch (more efficient)
            embeddings = self.model.encode(cleaned_texts, show_progress_bar=True)
            
            return embeddings.tolist()
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            # Return zero vectors as fallback
            return [np.zeros(384).tolist() for _ in texts]
