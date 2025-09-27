#!/usr/bin/env python3
"""
Fix missing connections and positions for the 54 concepts
"""

import asyncio
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append(str(Path(__file__).parent.parent))

from scripts.ingestion.database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_connections():
    """Build edges between all concepts using simple similarity"""
    
    db = DatabaseManager()
    
    logger.info("🔍 Checking current data...")
    
    # Get all concepts
    concepts = await db.get_all_concepts()
    logger.info(f"📊 Found {len(concepts)} concepts")
    
    # Get all positions
    positions = await db.get_all_positions()
    logger.info(f"🌌 Found {len(positions)} positions")
    
    # Get all edges
    edges = await db.get_all_edges()
    logger.info(f"🔗 Found {len(edges)} edges")
    
    if len(edges) < 10:  # We need more edges
        logger.info("🔗 Building similarity edges between concepts...")
        
        # Simple approach: connect concepts with similar categories or keywords
        new_edges = []
        edge_count = 0
        
        for i, concept1 in enumerate(concepts):
            for j, concept2 in enumerate(concepts[i+1:], i+1):
                if edge_count >= 100:  # Limit to 100 edges for now
                    break
                    
                # Calculate simple similarity
                similarity = calculate_simple_similarity(concept1, concept2)
                
                if similarity > 0.1:  # Threshold for connection
                    edge = {
                        'id': f"edge_{i}_{j}",
                        'source_id': concept1['id'],
                        'target_id': concept2['id'],
                        'weight': similarity,
                        'edge_type': 'similarity'
                    }
                    new_edges.append(edge)
                    edge_count += 1
            
            if edge_count >= 100:
                break
        
        if new_edges:
            logger.info(f"💾 Storing {len(new_edges)} new edges...")
            await db.insert_edges(new_edges)
            logger.info("✅ Edges created!")
        else:
            logger.info("⚠️ No new edges to create")
    
    logger.info("🎉 Connection fix complete!")
    logger.info("💡 Try refreshing your frontend - concepts should now be connected!")

def calculate_simple_similarity(concept1, concept2):
    """Calculate simple text similarity between concepts"""
    
    # Get text content
    text1 = f"{concept1['title']} {concept1.get('summary', '')} {concept1.get('category', '')}"
    text2 = f"{concept2['title']} {concept2.get('summary', '')} {concept2.get('category', '')}"
    
    text1 = text1.lower()
    text2 = text2.lower()
    
    # Simple keyword overlap
    words1 = set(text1.split())
    words2 = set(text2.split())
    
    # Remove common words
    common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'}
    
    words1 = words1 - common_words
    words2 = words2 - common_words
    
    if not words1 or not words2:
        return 0.0
    
    # Calculate Jaccard similarity
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    similarity = intersection / union if union > 0 else 0.0
    
    # Boost similarity for same category
    if concept1.get('category') == concept2.get('category') and concept1.get('category'):
        similarity += 0.2
    
    return min(similarity, 1.0)

if __name__ == '__main__':
    asyncio.run(fix_connections())
