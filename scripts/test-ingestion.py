#!/usr/bin/env python3
"""
Quick test of LYNX ingestion pipeline with minimal data
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from scripts.ingestion.wikipedia_ingester import WikipediaIngester
from scripts.ingestion.sbert_embedding_generator import SBERTEmbeddingGenerator
from scripts.ingestion.database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_pipeline():
    """Test the pipeline with minimal data"""
    
    # Check environment
    # Note: No OpenAI API key needed for SBERT!
    
    if not os.getenv('DATABASE_URL'):
        logger.error("❌ DATABASE_URL not set in environment")
        return False
    
    try:
        # Test 1: Database connection
        logger.info("🧪 Testing database connection...")
        db = DatabaseManager()
        await db.update_status('ingesting', 0, 10)
        logger.info("✅ Database connection working")
        
        # Test 2: Wikipedia ingestion (just 5 articles)
        logger.info("🧪 Testing Wikipedia ingestion...")
        wikipedia = WikipediaIngester()
        
        # Get just a few featured articles for testing
        test_articles = [
            "Artificial intelligence",
            "Black hole", 
            "DNA",
            "Quantum mechanics",
            "Leonardo da Vinci"
        ]
        
        concepts = []
        for title in test_articles:
            concept = await wikipedia.get_article_content(title)
            if concept:
                concepts.append(concept)
                logger.info(f"✅ Fetched: {concept['title']}")
        
        if not concepts:
            logger.error("❌ No concepts fetched from Wikipedia")
            return False
        
        logger.info(f"✅ Fetched {len(concepts)} test concepts")
        
        # Test 3: Store concepts in database
        logger.info("🧪 Testing concept storage...")
        await db.insert_concepts(concepts)
        logger.info("✅ Concepts stored in database")
        
        # Test 4: Generate embeddings (all concepts - no API costs with SBERT!)
        logger.info("🧪 Testing SBERT embedding generation...")
        embedding_gen = SBERTEmbeddingGenerator()
        test_concepts = concepts  # All concepts - SBERT is free!
        
        embeddings = await embedding_gen.generate_embeddings(test_concepts)
        logger.info(f"✅ Generated {len(embeddings)} embeddings")
        
        # Test 5: Update final status
        await db.update_status('complete', len(concepts), len(concepts), len(embeddings), 0)
        
        logger.info("🎉 Pipeline test completed successfully!")
        logger.info(f"📊 Results: {len(concepts)} concepts, {len(embeddings)} embeddings")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Pipeline test failed: {e}")
        await db.update_status('error', error_message=str(e))
        return False

if __name__ == '__main__':
    success = asyncio.run(test_pipeline())
    if success:
        print("\n🎉 Test passed! Your LYNX pipeline is working with SBERT.")
        print("\nNext steps:")
        print("1. Check http://localhost:3000/api/status to see updated counts")
        print("2. Try searching for 'artificial intelligence' in the web interface")
        print("3. Run full ingestion with: python scripts/ingestion/main.py --concepts 1000")
        print("4. No OpenAI API costs - SBERT runs locally! 🎆")
    else:
        print("\n❌ Test failed. Check the logs above for issues.")
        sys.exit(1)
