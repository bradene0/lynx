#!/usr/bin/env python3
"""
Debug script to find invisible nodes and data inconsistencies
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from collections import defaultdict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from scripts.ingestion.database import DatabaseManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NodeVisibilityDebugger:
    """Debug invisible nodes and data consistency"""
    
    def __init__(self):
        self.db = DatabaseManager()
    
    async def analyze_data_consistency(self):
        """Analyze concepts vs positions consistency"""
        logger.info("🔍 Analyzing data consistency...")
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                # Get concept counts by category
                cur.execute("""
                    SELECT category, COUNT(*) as concept_count
                    FROM concepts 
                    GROUP BY category 
                    ORDER BY concept_count DESC
                """)
                concept_stats = cur.fetchall()
                
                # Get position counts by cluster_id (which should map to category)
                cur.execute("""
                    SELECT cluster_id, COUNT(*) as position_count
                    FROM node_positions 
                    GROUP BY cluster_id 
                    ORDER BY position_count DESC
                """)
                position_stats = cur.fetchall()
                
                # Find concepts without positions
                cur.execute("""
                    SELECT c.id, c.title, c.category, c.source
                    FROM concepts c
                    LEFT JOIN node_positions p ON c.id = p.concept_id
                    WHERE p.concept_id IS NULL
                    ORDER BY c.category, c.title
                """)
                missing_positions = cur.fetchall()
                
                # Find positions without concepts
                cur.execute("""
                    SELECT p.concept_id, p.cluster_id
                    FROM node_positions p
                    LEFT JOIN concepts c ON p.concept_id = c.id
                    WHERE c.id IS NULL
                """)
                orphaned_positions = cur.fetchall()
                
                # Sample concepts by category
                cur.execute("""
                    SELECT c.category, COUNT(*) as total,
                           COUNT(p.concept_id) as with_positions,
                           COUNT(*) - COUNT(p.concept_id) as missing_positions
                    FROM concepts c
                    LEFT JOIN node_positions p ON c.id = p.concept_id
                    GROUP BY c.category
                    ORDER BY missing_positions DESC, total DESC
                """)
                category_analysis = cur.fetchall()
        
        # Report findings
        logger.info("📊 CONCEPT STATISTICS:")
        for category, count in concept_stats:
            logger.info(f"   • {category}: {count} concepts")
        
        logger.info("\n📍 POSITION STATISTICS:")
        for cluster_id, count in position_stats:
            logger.info(f"   • {cluster_id}: {count} positions")
        
        logger.info(f"\n❌ MISSING POSITIONS: {len(missing_positions)} concepts")
        if missing_positions:
            category_missing = defaultdict(list)
            for concept_id, title, category, source in missing_positions:
                category_missing[category].append((title, source))
            
            for category, items in category_missing.items():
                logger.info(f"   • {category}: {len(items)} missing")
                for title, source in items[:3]:  # Show first 3
                    logger.info(f"     - {title} ({source})")
                if len(items) > 3:
                    logger.info(f"     ... and {len(items) - 3} more")
        
        logger.info(f"\n🔗 ORPHANED POSITIONS: {len(orphaned_positions)}")
        
        logger.info("\n📋 CATEGORY ANALYSIS:")
        for category, total, with_pos, missing in category_analysis:
            percentage = (with_pos / total * 100) if total > 0 else 0
            logger.info(f"   • {category}: {with_pos}/{total} ({percentage:.1f}%) have positions")
            if missing > 0:
                logger.info(f"     ⚠️  {missing} concepts missing positions")
        
        return {
            'missing_positions': missing_positions,
            'orphaned_positions': orphaned_positions,
            'category_analysis': category_analysis
        }
    
    async def check_position_distribution(self):
        """Check if positions are properly distributed"""
        logger.info("\n🌌 Analyzing position distribution...")
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                # Get position ranges
                cur.execute("""
                    SELECT 
                        MIN(x) as min_x, MAX(x) as max_x,
                        MIN(y) as min_y, MAX(y) as max_y,
                        MIN(z) as min_z, MAX(z) as max_z,
                        COUNT(*) as total_positions
                    FROM node_positions
                """)
                ranges = cur.fetchone()
                
                # Check for clustering issues
                cur.execute("""
                    SELECT cluster_id, 
                           COUNT(*) as count,
                           AVG(x) as avg_x, AVG(y) as avg_y, AVG(z) as avg_z,
                           STDDEV(x) as std_x, STDDEV(y) as std_y, STDDEV(z) as std_z
                    FROM node_positions
                    GROUP BY cluster_id
                    ORDER BY count DESC
                """)
                cluster_stats = cur.fetchall()
        
        if ranges:
            min_x, max_x, min_y, max_y, min_z, max_z, total = ranges
            logger.info(f"📊 Position ranges ({total} total positions):")
            logger.info(f"   • X: {min_x:.1f} to {max_x:.1f} (range: {max_x - min_x:.1f})")
            logger.info(f"   • Y: {min_y:.1f} to {max_y:.1f} (range: {max_y - min_y:.1f})")
            logger.info(f"   • Z: {min_z:.1f} to {max_z:.1f} (range: {max_z - min_z:.1f})")
        
        logger.info("\n🎯 Cluster distribution:")
        for stats in cluster_stats:
            cluster_id, count, avg_x, avg_y, avg_z, std_x, std_y, std_z = stats
            logger.info(f"   • {cluster_id}: {count} nodes")
            logger.info(f"     Center: ({avg_x:.1f}, {avg_y:.1f}, {avg_z:.1f})")
            if std_x is not None:
                logger.info(f"     Spread: σx={std_x:.1f}, σy={std_y:.1f}, σz={std_z:.1f}")
    
    async def sample_invisible_nodes(self, category="History"):
        """Sample specific category nodes to debug visibility"""
        logger.info(f"\n🔍 Sampling {category} nodes...")
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                # Get sample nodes from category
                cur.execute("""
                    SELECT c.id, c.title, c.category, c.source,
                           p.x, p.y, p.z, p.cluster_id
                    FROM concepts c
                    LEFT JOIN node_positions p ON c.id = p.concept_id
                    WHERE c.category = %s
                    ORDER BY c.title
                    LIMIT 10
                """, (category,))
                samples = cur.fetchall()
        
        logger.info(f"📝 Sample {category} nodes:")
        for sample in samples:
            concept_id, title, cat, source, x, y, z, cluster_id = sample
            if x is not None:
                logger.info(f"   ✅ {title} - Position: ({x:.1f}, {y:.1f}, {z:.1f}) Cluster: {cluster_id}")
            else:
                logger.info(f"   ❌ {title} - NO POSITION")
    
    async def generate_missing_positions(self):
        """Generate positions for concepts that are missing them"""
        logger.info("\n🔧 Generating missing positions...")
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                # Get concepts without positions
                cur.execute("""
                    SELECT c.id, c.category
                    FROM concepts c
                    LEFT JOIN node_positions p ON c.id = p.concept_id
                    WHERE p.concept_id IS NULL
                """)
                missing = cur.fetchall()
        
        if not missing:
            logger.info("✅ No missing positions found!")
            return
        
        logger.info(f"🎯 Generating positions for {len(missing)} concepts...")
        
        import random
        import math
        
        positions = []
        galaxy_radius = 600  # Match the 10K expansion parameters
        
        for concept_id, category in missing:
            # Generate random spherical position
            u = random.uniform(0, 1)
            v = random.uniform(0, 1)
            
            theta = 2 * math.pi * u
            phi = math.acos(2 * v - 1)
            
            # Distribute across galaxy
            rand = random.random()
            if rand < 0.1:  # 10% in core
                radius = random.uniform(40, 120)
            elif rand < 0.7:  # 60% in main galaxy
                radius = random.uniform(120, galaxy_radius)
            else:  # 30% in halo
                radius = random.uniform(galaxy_radius, 1000)
            
            x = radius * math.sin(phi) * math.cos(theta)
            y = radius * math.sin(phi) * math.sin(theta)
            z = radius * math.cos(phi)
            
            cluster_id = category.replace(' ', '_').lower() if category else 'general'
            
            positions.append((concept_id, x, y, z, cluster_id))
        
        # Insert positions
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.executemany("""
                    INSERT INTO node_positions (concept_id, x, y, z, cluster_id)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (concept_id) DO NOTHING
                """, positions)
                conn.commit()
        
        logger.info(f"✅ Generated {len(positions)} new positions!")

async def main():
    """Run comprehensive node visibility analysis"""
    debugger = NodeVisibilityDebugger()
    
    try:
        # Step 1: Analyze data consistency
        analysis = await debugger.analyze_data_consistency()
        
        # Step 2: Check position distribution
        await debugger.check_position_distribution()
        
        # Step 3: Sample problematic categories
        await debugger.sample_invisible_nodes("History")
        await debugger.sample_invisible_nodes("Arts & Culture")
        await debugger.sample_invisible_nodes("Science & Technology")
        
        # Step 4: Generate missing positions if needed
        if analysis['missing_positions']:
            await debugger.generate_missing_positions()
            logger.info("\n🔄 Re-analyzing after position generation...")
            await debugger.analyze_data_consistency()
        
        logger.info("\n🎉 Analysis complete!")
        logger.info("💡 If nodes are still invisible, check:")
        logger.info("   • LOD system filtering")
        logger.info("   • Frontend category color mapping")
        logger.info("   • Three.js rendering limits")
        
    except Exception as e:
        logger.error(f"💥 Analysis failed: {e}")
        raise

if __name__ == '__main__':
    asyncio.run(main())
