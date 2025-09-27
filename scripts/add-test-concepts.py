#!/usr/bin/env python3
"""
Add test concepts directly to database for testing
"""

import os
import sys
import asyncio
import logging
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def add_test_concepts():
    """Add test concepts directly"""
    db = DatabaseManager()
    
    # Test concepts with summaries
    test_concepts = [
        {
            'id': str(uuid.uuid4()),
            'title': 'Machine Learning',
            'summary': 'Machine learning is a method of data analysis that automates analytical model building. It is a branch of artificial intelligence based on the idea that systems can learn from data, identify patterns and make decisions with minimal human intervention.',
            'category': 'Science & Technology',
            'source': 'manual',
            'source_id': '',
            'url': '',
            'created_at': datetime.now()
        },
        {
            'id': str(uuid.uuid4()),
            'title': 'Deep Learning',
            'summary': 'Deep learning is part of a broader family of machine learning methods based on artificial neural networks with representation learning. Learning can be supervised, semi-supervised or unsupervised.',
            'category': 'Science & Technology',
            'source': 'manual',
            'source_id': '',
            'url': '',
            'created_at': datetime.now()
        },
        {
            'id': str(uuid.uuid4()),
            'title': 'Computer Vision',
            'summary': 'Computer vision is an interdisciplinary scientific field that deals with how computers can gain high-level understanding from digital images or videos.',
            'category': 'Science & Technology',
            'source': 'manual',
            'source_id': '',
            'url': '',
            'created_at': datetime.now()
        },
        {
            'id': str(uuid.uuid4()),
            'title': 'Natural Language Processing',
            'summary': 'Natural language processing is a subfield of linguistics, computer science, and artificial intelligence concerned with the interactions between computers and human language.',
            'category': 'Science & Technology',
            'source': 'manual',
            'source_id': '',
            'url': '',
            'created_at': datetime.now()
        },
        {
            'id': str(uuid.uuid4()),
            'title': 'Robotics',
            'summary': 'Robotics is an interdisciplinary branch of computer science and engineering. Robotics involves design, construction, operation, and use of robots.',
            'category': 'Science & Technology',
            'source': 'manual',
            'source_id': '',
            'url': '',
            'created_at': datetime.now()
        },
        {
            'id': str(uuid.uuid4()),
            'title': 'Quantum Computing',
            'summary': 'Quantum computing is a type of computation that harnesses the collective properties of quantum states, such as superposition, interference, and entanglement, to perform calculations.',
            'category': 'Physical Sciences',
            'source': 'manual',
            'source_id': '',
            'url': '',
            'created_at': datetime.now()
        },
        {
            'id': str(uuid.uuid4()),
            'title': 'Photosynthesis',
            'summary': 'Photosynthesis is a process used by plants and other organisms to convert light energy into chemical energy that, through cellular respiration, can later be released to fuel the organism activities.',
            'category': 'Life Sciences',
            'source': 'manual',
            'source_id': '',
            'url': '',
            'created_at': datetime.now()
        },
        {
            'id': str(uuid.uuid4()),
            'title': 'Renaissance Art',
            'summary': 'Renaissance art is the painting, sculpture and decorative arts of the period of European history known as the Renaissance, which emerged as a distinct style in Italy in about AD 1400.',
            'category': 'Arts & Culture',
            'source': 'manual',
            'source_id': '',
            'url': '',
            'created_at': datetime.now()
        },
        {
            'id': str(uuid.uuid4()),
            'title': 'Game Theory',
            'summary': 'Game theory is the study of mathematical models of strategic interaction among rational decision-makers. It has applications in all fields of social science, as well as in logic, systems science and computer science.',
            'category': 'Mathematics & Logic',
            'source': 'manual',
            'source_id': '',
            'url': '',
            'created_at': datetime.now()
        },
        {
            'id': str(uuid.uuid4()),
            'title': 'Cognitive Psychology',
            'summary': 'Cognitive psychology is the scientific study of mental processes such as attention, language use, memory, perception, problem solving, creativity, and reasoning.',
            'category': 'Social Sciences',
            'source': 'manual',
            'source_id': '',
            'url': '',
            'created_at': datetime.now()
        }
    ]
    
    logger.info(f"Adding {len(test_concepts)} test concepts...")
    
    # Store concepts
    stored_count = await db.insert_concepts(test_concepts)
    logger.info(f"✅ Stored {stored_count} concepts")
    
    # Generate simple positions
    positions = []
    for i, concept in enumerate(test_concepts):
        x = (i % 5) * 80 - 160  # 5x2 grid
        y = (i // 5) * 80 - 40
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
    
    # Generate simple embeddings
    embeddings = []
    for concept in test_concepts:
        # Simple embedding based on concept title hash
        import hashlib
        text = concept['title']
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()
        
        embedding_list = []
        for i in range(384):
            byte_val = hash_bytes[i % len(hash_bytes)]
            normalized_val = (byte_val - 127.5) / 127.5
            embedding_list.append(normalized_val)
        
        embedding = {
            'concept_id': concept['id'],
            'embedding': embedding_list,
            'model': 'test-hash',
            'created_at': datetime.now()
        }
        embeddings.append(embedding)
    
    embedding_count = await db.insert_embeddings(embeddings)
    logger.info(f"✅ Stored {embedding_count} embeddings")
    
    logger.info("🎉 Test concepts added successfully!")
    logger.info("💡 Check your frontend - you should now see 15 total concepts!")

if __name__ == '__main__':
    asyncio.run(add_test_concepts())
