#!/usr/bin/env python3
"""
Create positions for all concepts that don't have them
"""

import asyncio
import sys
import logging
import requests
import uuid
import math
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

sys.path.append(str(Path(__file__).parent.parent))

from scripts.ingestion.database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_missing_positions():
    """Create positions for concepts that don't have them"""
    
    db = DatabaseManager()
    
    logger.info("🔍 Finding concepts without positions...")
    
    # Get concepts from API (what frontend sees)
    try:
        response = requests.get("http://localhost:3000/api/concepts")
        concepts = response.json()
        logger.info(f"📊 Found {len(concepts)} concepts from API")
    except Exception as e:
        logger.error(f"❌ Failed to get concepts from API: {e}")
        return
    
    # Get positions from API
    try:
        response = requests.get("http://localhost:3000/api/positions")
        positions = response.json()
        position_concept_ids = {pos['concept_id'] for pos in positions}
        logger.info(f"🌌 Found {len(positions)} existing positions")
    except Exception as e:
        logger.error(f"❌ Failed to get positions from API: {e}")
        return
    
    # Find concepts without positions
    missing_positions = []
    for concept in concepts:
        if concept['id'] not in position_concept_ids:
            missing_positions.append(concept)
    
    logger.info(f"🎯 Found {len(missing_positions)} concepts without positions")
    
    if not missing_positions:
        logger.info("✅ All concepts already have positions!")
        return
    
    # Create positions for missing concepts
    new_positions = []
    
    # Create a nice spiral galaxy layout for the missing concepts
    for i, concept in enumerate(missing_positions):
        # Spiral galaxy positioning
        angle = i * 0.5  # Spiral angle
        radius = 20 + (i * 8)  # Increasing radius
        height_variation = math.sin(i * 0.3) * 15  # Some height variation
        
        x = math.cos(angle) * radius
        y = height_variation
        z = math.sin(angle) * radius
        
        # Determine cluster based on category
        cluster_id = 'general'
        if concept.get('category'):
            cluster_id = concept['category'].lower().replace(' ', '_').replace('&', 'and')
        
        position = {
            'concept_id': concept['id'],
            'x': x,
            'y': y,
            'z': z,
            'cluster_id': cluster_id
        }
        new_positions.append(position)
        
        logger.info(f"📍 Position for {concept['title']}: ({x:.1f}, {y:.1f}, {z:.1f})")
    
    # Insert new positions
    if new_positions:
        logger.info(f"💾 Inserting {len(new_positions)} new positions...")
        try:
            count = await db.insert_positions(new_positions)
            logger.info(f"✅ Successfully created {count} positions!")
        except Exception as e:
            logger.error(f"❌ Failed to insert positions: {e}")
            return
    
    logger.info("🎉 Position fix complete!")
    logger.info("💡 Refresh your frontend - all concepts should now be visible in the galaxy!")

if __name__ == '__main__':
    asyncio.run(fix_missing_positions())
