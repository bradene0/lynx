#!/usr/bin/env python3
"""
Debug specific invisible nodes like "history of latin america"
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from scripts.ingestion.database import DatabaseManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SpecificNodeDebugger:
    """Debug specific invisible nodes"""
    
    def __init__(self):
        self.db = DatabaseManager()
    
    async def find_node(self, search_term):
        """Find nodes matching search term"""
        logger.info(f"🔍 Searching for nodes containing: '{search_term}'")
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                # Search for nodes with the term
                cur.execute("""
                    SELECT c.id, c.title, c.category, c.source, c.summary,
                           p.x, p.y, p.z, p.cluster_id
                    FROM concepts c
                    LEFT JOIN node_positions p ON c.id = p.concept_id
                    WHERE LOWER(c.title) LIKE %s OR LOWER(c.summary) LIKE %s
                    ORDER BY c.title
                """, (f'%{search_term.lower()}%', f'%{search_term.lower()}%'))
                
                results = cur.fetchall()
        
        if not results:
            logger.info(f"❌ No nodes found containing '{search_term}'")
            return []
        
        logger.info(f"📊 Found {len(results)} nodes:")
        for i, result in enumerate(results):
            concept_id, title, category, source, summary, x, y, z, cluster_id = result
            
            logger.info(f"\n📝 Node {i+1}: {title}")
            logger.info(f"   • ID: {concept_id}")
            logger.info(f"   • Category: {category}")
            logger.info(f"   • Source: {source}")
            logger.info(f"   • Summary: {summary[:100]}...")
            
            if x is not None:
                # Calculate distance from origin
                distance = (x**2 + y**2 + z**2)**0.5
                logger.info(f"   • Position: ({x:.1f}, {y:.1f}, {z:.1f})")
                logger.info(f"   • Distance from origin: {distance:.1f}")
                logger.info(f"   • Cluster: {cluster_id}")
                
                # Check if position is in reasonable range
                if distance > 1500:
                    logger.warning(f"   ⚠️  Very far from origin (>{1500})")
                elif distance > 1000:
                    logger.warning(f"   ⚠️  Far from origin (>{1000})")
                else:
                    logger.info(f"   ✅ Position looks reasonable")
            else:
                logger.error(f"   ❌ NO POSITION DATA")
        
        return results
    
    async def check_lod_filtering(self, node_positions, camera_pos=(0, 0, 100)):
        """Check if nodes would be filtered by LOD system"""
        logger.info(f"\n🎯 Checking LOD filtering from camera position {camera_pos}")
        
        # Simulate LOD system logic
        for i, pos in enumerate(node_positions):
            if len(pos) < 3:
                continue
                
            x, y, z = pos[5], pos[6], pos[7]  # Position columns
            if x is None:
                continue
                
            # Calculate distance from camera
            cam_x, cam_y, cam_z = camera_pos
            distance = ((x - cam_x)**2 + (y - cam_y)**2 + (z - cam_z)**2)**0.5
            
            # Check against LOD levels (from lod-system.tsx)
            lod_levels = [
                (100, 500),   # Close: distance <= 100, maxNodes = 500
                (300, 300),   # Medium: distance <= 300, maxNodes = 300  
                (600, 150),   # Far: distance <= 600, maxNodes = 150
                (1200, 75),   # Very far: distance <= 1200, maxNodes = 75
                (float('inf'), 30)  # Extreme: distance > 1200, maxNodes = 30
            ]
            
            lod_level = 0
            max_nodes = 30
            for j, (max_dist, nodes) in enumerate(lod_levels):
                if distance <= max_dist:
                    lod_level = j
                    max_nodes = nodes
                    break
            
            title = pos[1]  # Title column
            logger.info(f"   • {title}")
            logger.info(f"     Distance: {distance:.1f}, LOD Level: {lod_level}, Max nodes at this level: {max_nodes}")
            
            if distance > 1200:
                logger.warning(f"     ⚠️  At extreme distance - only top 30 nodes visible")
            elif distance > 600:
                logger.warning(f"     ⚠️  At far distance - only top 75-150 nodes visible")
    
    async def check_api_response(self, search_term):
        """Check if nodes appear in API responses"""
        logger.info(f"\n🌐 Checking API responses for '{search_term}'")
        
        import requests
        
        try:
            # Check concepts API
            response = requests.get('http://localhost:3000/api/concepts?limit=10000')
            if response.status_code == 200:
                concepts = response.json()
                matching = [c for c in concepts if search_term.lower() in c['title'].lower()]
                logger.info(f"📊 Concepts API: {len(concepts)} total, {len(matching)} matching '{search_term}'")
                
                for match in matching[:3]:
                    logger.info(f"   • {match['title']} ({match['category']})")
            else:
                logger.error(f"❌ Concepts API failed: {response.status_code}")
            
            # Check search API
            response = requests.get(f'http://localhost:3000/api/search?query={search_term}&limit=50')
            if response.status_code == 200:
                search_results = response.json()
                logger.info(f"🔍 Search API: {len(search_results['results'])} results")
                
                for result in search_results['results'][:3]:
                    logger.info(f"   • {result['concept']['title']} (similarity: {result['similarity']:.2f})")
            else:
                logger.error(f"❌ Search API failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ API check failed: {e}")

async def main():
    """Debug specific invisible node"""
    debugger = SpecificNodeDebugger()
    
    search_terms = [
        "latin america",
        "history of latin america", 
        "volcanology",
        "volcano"
    ]
    
    for term in search_terms:
        logger.info(f"\n{'='*60}")
        logger.info(f"🔍 DEBUGGING: '{term}'")
        logger.info(f"{'='*60}")
        
        # Find matching nodes
        results = await debugger.find_node(term)
        
        if results:
            # Check LOD filtering
            await debugger.check_lod_filtering(results)
            
            # Check API responses
            await debugger.check_api_response(term)
        
        logger.info(f"\n")

if __name__ == '__main__':
    asyncio.run(main())
