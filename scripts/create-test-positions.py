#!/usr/bin/env python3
"""
Create test positions for our 5 ingested concepts
"""

import os
import sys
import asyncio
import logging
import random
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from scripts.ingestion.database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_test_positions():
    """Create test positions for existing concepts"""
    
    db = DatabaseManager()
    
    try:
        # Get existing concepts
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, title, category FROM concepts")
                concepts = cur.fetchall()
        
        if not concepts:
            logger.error("No concepts found in database")
            return
        
        logger.info(f"Creating positions for {len(concepts)} concepts")
        
        # Create positions in a rough circle for visualization
        positions = []
        for i, concept in enumerate(concepts):
            concept_id, title, category = concept
            
            # Arrange in a circle with some randomness
            angle = (i / len(concepts)) * 2 * 3.14159
            radius = 50 + random.uniform(-10, 10)
            
            x = radius * random.uniform(0.8, 1.2) * (1 if i % 2 == 0 else -1)
            y = radius * random.uniform(0.8, 1.2) * (1 if (i // 2) % 2 == 0 else -1)
            z = random.uniform(-20, 20)
            
            position = {
                'concept_id': concept_id,
                'x': float(x),
                'y': float(y),
                'z': float(z),
                'cluster_id': category or 'General'
            }
            positions.append(position)
            
            logger.info(f"Position for '{title}': ({x:.1f}, {y:.1f}, {z:.1f})")
        
        # Insert positions
        await db.insert_positions(positions)
        
        logger.info(f"✅ Created {len(positions)} test positions")
        
    except Exception as e:
        logger.error(f"❌ Failed to create positions: {e}")
        raise

if __name__ == '__main__':
    asyncio.run(create_test_positions())
