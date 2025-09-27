#!/usr/bin/env python3
"""
Quick 50-concept ingestion - proven concepts that work
"""

import os
import sys
import asyncio
import logging
import requests
import requests.utils
import time
from pathlib import Path
from dotenv import load_dotenv
import uuid
from datetime import datetime

# Load environment variables
load_dotenv()

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from scripts.ingestion.database import DatabaseManager
from scripts.ingestion.embeddings import EmbeddingGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def quick_ingestion():
    """Quick 50-concept ingestion with proven working concepts"""
    
    db = DatabaseManager()
    embedder = EmbeddingGenerator()
    
    # Proven working concepts from our previous runs
    proven_concepts = [
        'Artificial Intelligence', 'Machine Learning', 'Deep Learning', 'Computer Vision', 'Robotics',
        'Quantum Computing', 'Blockchain', 'Internet of Things', 'Cybersecurity', 'Biotechnology',
        'CRISPR', 'Nanotechnology', 'Solar Power', 'Climate Change', 'Evolution',
        'DNA', 'RNA', 'Protein', 'Neuroscience', 'Psychology',
        'Democracy', 'Globalization', 'Human Rights', 'Social Justice', 'Feminism',
        'Renaissance', 'Leonardo da Vinci', 'Michelangelo', 'Shakespeare', 'Mozart',
        'Calculus', 'Linear Algebra', 'Statistics', 'Game Theory', 'Cryptography',
        'Black Hole', 'Neutron Star', 'Big Bang', 'Relativity', 'Thermodynamics',
        'Photosynthesis', 'Ecosystem', 'Biodiversity', 'Genetics', 'Immunology',
        'Philosophy', 'Ethics', 'Aristotle', 'Plato', 'Kant'
    ]
    
    logger.info(f"🚀 Quick ingestion of {len(proven_concepts)} proven concepts")
    
    headers = {
        'User-Agent': 'LYNX Knowledge Explorer/1.0 (https://github.com/user/lynx; contact@example.com)',
        'Accept': 'application/json'
    }
    
    concepts = []
    
    # Fetch concepts quickly (no delays since we know these work)
    for i, title in enumerate(proven_concepts):
        try:
            encoded_title = requests.utils.quote(title.replace(' ', '_'))
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'extract' in data and len(data['extract']) > 50:
                    
                    # Categorize
                    category = 'General'
                    if any(word in title.lower() for word in ['ai', 'machine', 'computer', 'robot', 'cyber']):
                        category = 'Science & Technology'
                    elif any(word in title.lower() for word in ['quantum', 'black hole', 'relativity', 'thermo']):
                        category = 'Physical Sciences'
                    elif any(word in title.lower() for word in ['dna', 'rna', 'protein', 'bio', 'neuro', 'photo']):
                        category = 'Life Sciences'
                    elif any(word in title.lower() for word in ['leonardo', 'shakespeare', 'mozart', 'renaissance']):
                        category = 'Arts & Culture'
                    elif any(word in title.lower() for word in ['democracy', 'human rights', 'social', 'feminism']):
                        category = 'Social Sciences'
                    elif any(word in title.lower() for word in ['calculus', 'algebra', 'statistics', 'game theory']):
                        category = 'Mathematics & Logic'
                    elif any(word in title.lower() for word in ['philosophy', 'ethics', 'aristotle', 'plato']):
                        category = 'Philosophy & Religion'
                    
                    concept = {
                        'id': str(uuid.uuid4()),
                        'title': data['title'],
                        'summary': data['extract'][:1500],
                        'category': category,
                        'source': 'wikipedia',
                        'source_id': '',
                        'url': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                        'created_at': datetime.now()
                    }
                    concepts.append(concept)
                    logger.info(f"✅ {i+1:2d}/50: {concept['title']} ({category})")
            
            # Small delay to be respectful
            time.sleep(0.2)
            
        except Exception as e:
            logger.warning(f"⚠️ Skipped {title}: {e}")
    
    logger.info(f"📊 Successfully fetched {len(concepts)} concepts")
    
    # Store concepts
    stored_count = await db.insert_concepts(concepts)
    logger.info(f"✅ Stored {stored_count} concepts in database")
    
    # Generate embeddings
    logger.info("🧠 Generating SBERT embeddings...")
    embeddings = []
    
    for i, concept in enumerate(concepts):
        try:
            text = f"{concept['title']}. {concept['summary']}"
            embedding_vector = embedder.generate_embedding(text)
            
            embedding = {
                'id': str(uuid.uuid4()),
                'concept_id': concept['id'],
                'embedding': embedding_vector.tolist(),
                'model': 'all-MiniLM-L6-v2',
                'created_at': datetime.now()
            }
            embeddings.append(embedding)
            
            if (i + 1) % 10 == 0:
                logger.info(f"🧠 Embeddings: {i + 1}/{len(concepts)}")
                
        except Exception as e:
            logger.error(f"❌ Embedding failed for {concept['title']}: {e}")
    
    # Store embeddings
    embedding_count = await db.insert_embeddings(embeddings)
    logger.info(f"✅ Stored {embedding_count} embeddings")
    
    # Generate positions (simple grid)
    logger.info("🌌 Generating 3D positions...")
    positions = []
    
    import math
    grid_size = math.ceil(math.sqrt(len(concepts)))
    
    for i, concept in enumerate(concepts):
        x = (i % grid_size) * 60 - (grid_size * 30)
        y = (i // grid_size) * 60 - (grid_size * 30)
        z = 0
        
        position = {
            'concept_id': concept['id'],
            'x': x,
            'y': y,
            'z': z,
            'cluster_id': concept['category'].replace(' ', '_').lower()
        }
        positions.append(position)
    
    position_count = await db.insert_positions(positions)
    logger.info(f"✅ Stored {position_count} positions")
    
    logger.info("🎉 Quick 50-concept ingestion complete!")
    logger.info(f"📊 Final stats:")
    logger.info(f"   • Concepts: {stored_count}")
    logger.info(f"   • Embeddings: {embedding_count}")
    logger.info(f"   • Positions: {position_count}")
    logger.info(f"   • Categories: {len(set(c['category'] for c in concepts))}")
    logger.info("💡 Check your frontend - you should now see 55+ concepts!")

if __name__ == '__main__':
    asyncio.run(quick_ingestion())
