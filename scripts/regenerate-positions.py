#!/usr/bin/env python3
"""
LYNX Position Regeneration Script
Regenerates 3D positions for existing concepts with improved random distribution
"""

import os
import sys
import asyncio
import logging
import random
import math
import numpy as np
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict, Any

# Load environment variables from the web app directory
web_app_dir = Path(__file__).parent.parent / "apps" / "web"
load_dotenv(web_app_dir / ".env.local")
load_dotenv(web_app_dir / ".env")
load_dotenv()  # Also load from project root

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Try to import the database manager, but create our own if needed
try:
    from scripts.ingestion.database import DatabaseManager
    USE_EXISTING_DB_MANAGER = True
except ImportError:
    USE_EXISTING_DB_MANAGER = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PositionRegenerator:
    """Regenerates node positions with improved spatial distribution"""
    
    def __init__(self):
        if USE_EXISTING_DB_MANAGER:
            self.db = DatabaseManager()
        else:
            # Create a simple database connection for this script
            self.connection_string = os.getenv('DATABASE_URL')
            if not self.connection_string:
                raise ValueError("DATABASE_URL environment variable not set")
        
        # Galaxy parameters for better distribution
        self.galaxy_radius = 200  # Main galaxy radius
        self.core_radius = 50     # Dense core radius
        self.halo_radius = 300    # Sparse outer halo
        self.spiral_arms = 4      # Number of spiral arms
    
    def get_connection(self):
        """Get a database connection"""
        if USE_EXISTING_DB_MANAGER:
            return self.db.get_connection()
        else:
            try:
                import psycopg2
                return psycopg2.connect(self.connection_string)
            except ImportError:
                import psycopg as psycopg2
                return psycopg2.connect(self.connection_string)
        
    def generate_spherical_coordinates(self) -> tuple[float, float, float]:
        """Generate random spherical coordinates for uniform 3D distribution"""
        # Use uniform distribution on sphere surface
        u = random.uniform(0, 1)
        v = random.uniform(0, 1)
        
        # Convert to spherical coordinates
        theta = 2 * math.pi * u  # Azimuthal angle
        phi = math.acos(2 * v - 1)  # Polar angle
        
        # Random radius with galaxy-like distribution
        # Most nodes in main galaxy, some in core, few in halo
        rand = random.random()
        if rand < 0.3:  # 30% in dense core
            radius = random.uniform(10, self.core_radius)
        elif rand < 0.8:  # 50% in main galaxy
            radius = random.uniform(self.core_radius, self.galaxy_radius)
        else:  # 20% in outer halo
            radius = random.uniform(self.galaxy_radius, self.halo_radius)
        
        # Convert to Cartesian coordinates
        x = radius * math.sin(phi) * math.cos(theta)
        y = radius * math.sin(phi) * math.sin(theta)
        z = radius * math.cos(phi)
        
        return x, y, z
    
    def generate_spiral_galaxy_position(self, concept_index: int, total_concepts: int) -> tuple[float, float, float]:
        """Generate position following a spiral galaxy pattern"""
        # Determine which spiral arm this concept belongs to
        arm_index = concept_index % self.spiral_arms
        
        # Position along the arm (0 to 1)
        arm_position = (concept_index / total_concepts) + (arm_index / self.spiral_arms)
        arm_position = arm_position % 1.0
        
        # Spiral parameters
        max_radius = self.galaxy_radius
        spiral_tightness = 2.0  # How tight the spiral is
        
        # Calculate spiral position
        angle = arm_position * 4 * math.pi * spiral_tightness + (arm_index * 2 * math.pi / self.spiral_arms)
        radius = arm_position * max_radius
        
        # Add some randomness to avoid perfect spirals
        angle += random.uniform(-0.5, 0.5)
        radius += random.uniform(-20, 20)
        radius = max(10, min(max_radius, radius))  # Clamp radius
        
        # Convert to Cartesian
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        
        # Z coordinate with galaxy disk thickness
        disk_thickness = 40
        z = random.uniform(-disk_thickness/2, disk_thickness/2)
        
        # Add some nodes above/below the disk
        if random.random() < 0.1:  # 10% chance
            z += random.uniform(-80, 80)
        
        return x, y, z
    
    def generate_clustered_random_position(self, category: str, concept_index: int) -> tuple[float, float, float]:
        """Generate position with loose category-based clustering but still random"""
        # Create loose category regions (much larger and more spread out)
        category_regions = {
            'Science & Technology': (0, 0, 0),
            'Mathematics & Logic': (80, 60, 20),
            'History & Culture': (-70, 50, -30),
            'Arts & Literature': (60, -80, 40),
            'Philosophy & Religion': (-90, -60, -20),
            'Social Sciences': (40, 90, 30),
            'Life Sciences': (-60, -90, 50),
            'Physical Sciences': (90, 30, -40),
        }
        
        # Get base region or use random for unknown categories
        if any(cat in category for cat in category_regions.keys()):
            # Find matching category
            base_region = None
            for cat_key, region in category_regions.items():
                if cat_key in category:
                    base_region = region
                    break
            if base_region is None:
                base_region = (0, 0, 0)
        else:
            # Academic papers and other categories get random positions
            base_region = (
                random.uniform(-self.galaxy_radius, self.galaxy_radius),
                random.uniform(-self.galaxy_radius, self.galaxy_radius),
                random.uniform(-50, 50)
            )
        
        # Add large random variation (much larger than before)
        variation = 120  # Large variation for natural distribution
        x = base_region[0] + random.uniform(-variation, variation)
        y = base_region[1] + random.uniform(-variation, variation)
        z = base_region[2] + random.uniform(-variation/2, variation/2)
        
        return x, y, z
    
    def generate_pure_random_position(self) -> tuple[float, float, float]:
        """Generate completely random position within galaxy bounds"""
        # Use cubic distribution for more natural randomness
        max_coord = self.galaxy_radius * 1.2
        
        x = random.uniform(-max_coord, max_coord)
        y = random.uniform(-max_coord, max_coord)
        z = random.uniform(-60, 60)  # Flatter galaxy disk
        
        return x, y, z
    
    async def get_existing_concepts(self) -> List[Dict[str, Any]]:
        """Fetch all existing concepts from database"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, title, category, source
                    FROM concepts
                    ORDER BY created_at
                """)
                
                concepts = []
                for row in cur.fetchall():
                    concepts.append({
                        'id': row[0],
                        'title': row[1],
                        'category': row[2] or 'General',
                        'source': row[3]
                    })
                
                return concepts
    
    async def insert_positions(self, positions: List[Dict[str, Any]]) -> int:
        """Insert node positions into the database"""
        if not positions:
            return 0
        
        if USE_EXISTING_DB_MANAGER:
            return await self.db.insert_positions(positions)
        
        # Direct database insertion
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                for position in positions:
                    cur.execute(
                        """
                        INSERT INTO node_positions (concept_id, x, y, z, cluster_id)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (concept_id) DO UPDATE SET
                            x = EXCLUDED.x,
                            y = EXCLUDED.y,
                            z = EXCLUDED.z,
                            cluster_id = EXCLUDED.cluster_id,
                            updated_at = NOW()
                        """,
                        (
                            position['concept_id'],
                            position['x'],
                            position['y'],
                            position['z'],
                            position.get('cluster_id')
                        )
                    )
                
                conn.commit()
                logger.info(f"Inserted/updated {len(positions)} positions")
                return len(positions)
    
    async def regenerate_all_positions(self, distribution_method: str = 'mixed'):
        """Regenerate positions for all existing concepts"""
        logger.info("🌌 Starting position regeneration...")
        
        # Get all existing concepts
        concepts = await self.get_existing_concepts()
        logger.info(f"📊 Found {len(concepts)} existing concepts")
        
        if not concepts:
            logger.warning("No concepts found in database")
            return
        
        # Generate new positions based on method
        new_positions = []
        
        for i, concept in enumerate(concepts):
            if distribution_method == 'spherical':
                x, y, z = self.generate_spherical_coordinates()
            elif distribution_method == 'spiral':
                x, y, z = self.generate_spiral_galaxy_position(i, len(concepts))
            elif distribution_method == 'clustered':
                x, y, z = self.generate_clustered_random_position(concept['category'], i)
            elif distribution_method == 'random':
                x, y, z = self.generate_pure_random_position()
            else:  # mixed - default
                # Use different methods for different concept types
                rand = random.random()
                if rand < 0.4:  # 40% spherical
                    x, y, z = self.generate_spherical_coordinates()
                elif rand < 0.7:  # 30% spiral
                    x, y, z = self.generate_spiral_galaxy_position(i, len(concepts))
                elif rand < 0.9:  # 20% clustered
                    x, y, z = self.generate_clustered_random_position(concept['category'], i)
                else:  # 10% pure random
                    x, y, z = self.generate_pure_random_position()
            
            position = {
                'concept_id': concept['id'],
                'x': float(x),
                'y': float(y), 
                'z': float(z),
                'cluster_id': concept['category'].replace(' ', '_').lower()
            }
            new_positions.append(position)
            
            if (i + 1) % 100 == 0:
                logger.info(f"🎯 Generated positions: {i + 1}/{len(concepts)}")
        
        # Store new positions in database
        logger.info("💾 Storing new positions in database...")
        position_count = await self.insert_positions(new_positions)
        
        logger.info("🎉 Position regeneration complete!")
        logger.info(f"📊 Final Stats:")
        logger.info(f"   • Concepts repositioned: {position_count}")
        logger.info(f"   • Distribution method: {distribution_method}")
        logger.info(f"   • Galaxy radius: {self.galaxy_radius}")
        logger.info(f"   • Core radius: {self.core_radius}")
        logger.info(f"   • Halo radius: {self.halo_radius}")
        
        # Print distribution summary
        logger.info("📍 Position distribution summary:")
        x_coords = [pos['x'] for pos in new_positions]
        y_coords = [pos['y'] for pos in new_positions]
        z_coords = [pos['z'] for pos in new_positions]
        
        logger.info(f"   • X range: {min(x_coords):.1f} to {max(x_coords):.1f}")
        logger.info(f"   • Y range: {min(y_coords):.1f} to {max(y_coords):.1f}")
        logger.info(f"   • Z range: {min(z_coords):.1f} to {max(z_coords):.1f}")

async def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Regenerate LYNX concept positions')
    parser.add_argument(
        '--method', 
        choices=['spherical', 'spiral', 'clustered', 'random', 'mixed'],
        default='mixed',
        help='Distribution method to use (default: mixed)'
    )
    
    args = parser.parse_args()
    
    logger.info(f"🚀 LYNX Position Regeneration - Method: {args.method}")
    
    regenerator = PositionRegenerator()
    await regenerator.regenerate_all_positions(args.method)

if __name__ == '__main__':
    asyncio.run(main())
