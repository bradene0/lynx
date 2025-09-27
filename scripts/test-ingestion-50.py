#!/usr/bin/env python3
"""
LYNX Test Ingestion Pipeline - 50 concepts
Quick test to verify the pipeline works before scaling to 1000
"""

import os
import sys
import asyncio
import logging
import requests
import time
import json
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict
import uuid
from datetime import datetime

# Load environment variables
load_dotenv()

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from scripts.ingestion.database import DatabaseManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestIngestion:
    def __init__(self):
        self.db = DatabaseManager()
        
        # Test concepts - diverse but smaller set
        self.test_concepts = [
            'Artificial Intelligence', 'Machine Learning', 'Deep Learning', 'Neural Networks', 'Computer Vision',
            'Quantum Computing', 'Quantum Mechanics', 'Black Hole', 'Neutron Star', 'Dark Matter',
            'DNA', 'RNA', 'Protein', 'Evolution', 'Genetics',
            'Leonardo da Vinci', 'Michelangelo', 'Renaissance', 'Baroque', 'Impressionism',
            'Democracy', 'Philosophy', 'Ethics', 'Aristotle', 'Plato',
            'Calculus', 'Linear Algebra', 'Statistics', 'Probability', 'Graph Theory',
            'Climate Change', 'Renewable Energy', 'Solar Power', 'Photosynthesis', 'Ecosystem',
            'World War II', 'Industrial Revolution', 'Roman Empire', 'Ancient Egypt', 'Medieval Europe',
            'Psychology', 'Neuroscience', 'Cognitive Science', 'Sociology', 'Anthropology',
            'Chemistry', 'Physics', 'Biology', 'Mathematics', 'Computer Science'
        ]

    async def get_wikipedia_concepts(self) -> List[Dict]:
        """Get Wikipedia concepts for testing"""
        logger.info(f"🌍 Fetching {len(self.test_concepts)} test concepts from Wikipedia...")
        
        concepts = []
        
        for concept_title in self.test_concepts:
            try:
                # Wikipedia API call
                search_url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + concept_title.replace(' ', '_')
                response = requests.get(search_url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'extract' in data and len(data['extract']) > 50:
                        # Determine category based on concept
                        category = self.categorize_concept(concept_title)
                        
                        concept = {
                            'id': str(uuid.uuid4()),
                            'title': data['title'],
                            'summary': data['extract'][:1500],  # Limit summary length
                            'category': category,
                            'source': 'wikipedia',
                            'source_url': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                            'created_at': datetime.now()
                        }
                        concepts.append(concept)
                        logger.info(f"✅ Added: {concept['title']} ({category})")
                    else:
                        logger.warning(f"⚠️ Insufficient content for: {concept_title}")
                else:
                    logger.warning(f"⚠️ Wikipedia API error for {concept_title}: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ Error fetching {concept_title}: {e}")
            
            # Rate limiting - Wikipedia allows 100 requests/second
            time.sleep(0.2)
        
        logger.info(f"🎯 Successfully fetched {len(concepts)} concepts")
        return concepts

    def categorize_concept(self, title: str) -> str:
        """Simple categorization based on concept title"""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['ai', 'artificial', 'machine', 'computer', 'neural', 'deep']):
            return 'Science & Technology'
        elif any(word in title_lower for word in ['quantum', 'black hole', 'neutron', 'dark matter', 'physics']):
            return 'Physical Sciences'
        elif any(word in title_lower for word in ['dna', 'rna', 'protein', 'evolution', 'biology']):
            return 'Life Sciences'
        elif any(word in title_lower for word in ['leonardo', 'michelangelo', 'renaissance', 'art']):
            return 'Arts & Culture'
        elif any(word in title_lower for word in ['democracy', 'philosophy', 'aristotle', 'plato']):
            return 'Philosophy & Religion'
        elif any(word in title_lower for word in ['calculus', 'algebra', 'statistics', 'mathematics']):
            return 'Mathematics & Logic'
        elif any(word in title_lower for word in ['war', 'revolution', 'empire', 'history']):
            return 'History & Culture'
        elif any(word in title_lower for word in ['psychology', 'neuroscience', 'sociology']):
            return 'Social Sciences'
        else:
            return 'General'

    async def generate_simple_embeddings(self, concepts: List[Dict]) -> List[Dict]:
        """Generate simple embeddings without SBERT for testing"""
        logger.info("🧠 Generating simple test embeddings...")
        
        embeddings = []
        
        for concept in concepts:
            try:
                # Create a simple hash-based embedding for testing
                import hashlib
                text = f"{concept['title']}. {concept['summary']}"
                hash_obj = hashlib.md5(text.encode())
                
                # Convert hash to a 384-dimensional vector (matching SBERT dimensions)
                hash_bytes = hash_obj.digest()
                # Repeat and normalize to create 384 dimensions
                embedding_list = []
                for i in range(384):
                    byte_val = hash_bytes[i % len(hash_bytes)]
                    normalized_val = (byte_val - 127.5) / 127.5  # Normalize to [-1, 1]
                    embedding_list.append(normalized_val)
                
                embedding = {
                    'concept_id': concept['id'],
                    'embedding': embedding_list,
                    'model': 'test-hash-embedding',
                    'created_at': datetime.now()
                }
                embeddings.append(embedding)
                
            except Exception as e:
                logger.error(f"❌ Error generating embedding for {concept['title']}: {e}")
        
        logger.info(f"✅ Generated {len(embeddings)} test embeddings")
        return embeddings

    async def generate_positions(self, concepts: List[Dict]) -> List[Dict]:
        """Generate 3D positions for concepts"""
        logger.info("🌌 Generating 3D positions...")
        
        positions = []
        
        # Simple grid-based positioning for test
        import math
        grid_size = math.ceil(math.sqrt(len(concepts)))
        
        for i, concept in enumerate(concepts):
            x = (i % grid_size) * 50 - (grid_size * 25)
            y = (i // grid_size) * 50 - (grid_size * 25)
            z = 0  # Keep it simple for test
            
            position = {
                'concept_id': concept['id'],
                'x': x,
                'y': y,
                'z': z,
                'cluster_id': concept['category'].replace(' ', '_').lower()
            }
            positions.append(position)
        
        logger.info(f"✅ Generated {len(positions)} positions")
        return positions

    async def run_test_ingestion(self):
        """Main test pipeline"""
        logger.info("🚀 Starting LYNX Test Ingestion Pipeline...")
        logger.info(f"🎯 Target: {len(self.test_concepts)} test concepts")
        
        try:
            # Step 1: Fetch concepts
            concepts = await self.get_wikipedia_concepts()
            
            # Step 2: Store concepts
            logger.info("💾 Storing concepts in database...")
            stored_count = await self.db.insert_concepts(concepts)
            logger.info(f"✅ Stored {stored_count} concepts")
            
            # Step 3: Generate simple embeddings
            embeddings = await self.generate_simple_embeddings(concepts)
            embedding_count = await self.db.insert_embeddings(embeddings)
            logger.info(f"✅ Stored {embedding_count} embeddings")
            
            # Step 4: Generate positions
            positions = await self.generate_positions(concepts)
            position_count = await self.db.insert_positions(positions)
            logger.info(f"✅ Stored {position_count} positions")
            
            logger.info("🎉 LYNX Test Ingestion Complete!")
            logger.info(f"📊 Final Stats:")
            logger.info(f"   • Concepts: {stored_count}")
            logger.info(f"   • Embeddings: {embedding_count}")
            logger.info(f"   • Positions: {position_count}")
            logger.info(f"   • Categories: {len(set(c['category'] for c in concepts))}")
            
            logger.info("💡 Next steps:")
            logger.info("   1. Check the frontend - you should see 50 concepts!")
            logger.info("   2. Test search, selection, and navigation")
            logger.info("   3. Run full 1000-concept ingestion when ready")
            
        except Exception as e:
            logger.error(f"💥 Test pipeline failed: {e}")
            raise

async def main():
    ingestion = TestIngestion()
    await ingestion.run_test_ingestion()

if __name__ == '__main__':
    asyncio.run(main())
