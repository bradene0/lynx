#!/usr/bin/env python3
"""
Simple Position Fix Script for LYNX
Uses the same database connection as the web app
"""

import os
import sys
import random
import math
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from web app
web_app_dir = Path(__file__).parent.parent / "apps" / "web"
load_dotenv(web_app_dir / ".env.local")
load_dotenv(web_app_dir / ".env")

# Try to import psycopg
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG_VERSION = 2
except ImportError:
    try:
        import psycopg as psycopg2
        from psycopg.rows import dict_row
        PSYCOPG_VERSION = 3
    except ImportError:
        print("❌ Error: Neither psycopg2 nor psycopg3 is installed")
        print("Please install one of them: pip install psycopg2-binary OR pip install psycopg")
        sys.exit(1)

def get_database_connection():
    """Get database connection using the same method as web app"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ Error: DATABASE_URL environment variable not found")
        print("Make sure your .env.local file in apps/web/ contains the DATABASE_URL")
        sys.exit(1)
    
    try:
        if PSYCOPG_VERSION == 2:
            return psycopg2.connect(database_url)
        else:
            return psycopg2.connect(database_url)
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print(f"DATABASE_URL: {database_url[:50]}...")
        sys.exit(1)

def generate_random_galaxy_position():
    """Generate a random position in 3D galaxy space"""
    # Galaxy parameters
    galaxy_radius = 200
    core_radius = 50
    halo_radius = 300
    
    # Use spherical coordinates for uniform distribution
    u = random.uniform(0, 1)
    v = random.uniform(0, 1)
    
    theta = 2 * math.pi * u  # Azimuthal angle
    phi = math.acos(2 * v - 1)  # Polar angle
    
    # Galaxy-like radius distribution
    rand = random.random()
    if rand < 0.3:  # 30% in dense core
        radius = random.uniform(10, core_radius)
    elif rand < 0.8:  # 50% in main galaxy
        radius = random.uniform(core_radius, galaxy_radius)
    else:  # 20% in outer halo
        radius = random.uniform(galaxy_radius, halo_radius)
    
    # Convert to Cartesian coordinates
    x = radius * math.sin(phi) * math.cos(theta)
    y = radius * math.sin(phi) * math.sin(theta)
    z = radius * math.cos(phi)
    
    return float(x), float(y), float(z)

def main():
    print("🚀 LYNX Position Fix Script")
    print("🌌 Regenerating positions for better galaxy distribution...")
    
    # Connect to database
    conn = get_database_connection()
    print("✅ Connected to database")
    
    try:
        if PSYCOPG_VERSION == 2:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
        else:
            cursor = conn.cursor(row_factory=dict_row)
        
        # Get all existing concepts
        cursor.execute("SELECT id, title, category FROM concepts ORDER BY created_at")
        concepts = cursor.fetchall()
        
        print(f"📊 Found {len(concepts)} concepts to reposition")
        
        if not concepts:
            print("⚠️ No concepts found in database")
            return
        
        # Generate new positions
        new_positions = []
        for i, concept in enumerate(concepts):
            x, y, z = generate_random_galaxy_position()
            
            new_positions.append({
                'concept_id': concept['id'],
                'x': x,
                'y': y,
                'z': z,
                'cluster_id': (concept['category'] or 'general').replace(' ', '_').lower()
            })
            
            if (i + 1) % 100 == 0:
                print(f"🎯 Generated positions: {i + 1}/{len(concepts)}")
        
        # Update positions in database
        print("💾 Updating positions in database...")
        
        for position in new_positions:
            cursor.execute("""
                INSERT INTO node_positions (concept_id, x, y, z, cluster_id, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
                ON CONFLICT (concept_id) DO UPDATE SET
                    x = EXCLUDED.x,
                    y = EXCLUDED.y,
                    z = EXCLUDED.z,
                    cluster_id = EXCLUDED.cluster_id,
                    updated_at = NOW()
            """, (
                position['concept_id'],
                position['x'],
                position['y'],
                position['z'],
                position['cluster_id']
            ))
        
        conn.commit()
        
        print("🎉 Position regeneration complete!")
        print(f"📊 Successfully updated {len(new_positions)} positions")
        
        # Print distribution summary
        x_coords = [pos['x'] for pos in new_positions]
        y_coords = [pos['y'] for pos in new_positions]
        z_coords = [pos['z'] for pos in new_positions]
        
        print("📍 Position distribution summary:")
        print(f"   • X range: {min(x_coords):.1f} to {max(x_coords):.1f}")
        print(f"   • Y range: {min(y_coords):.1f} to {max(y_coords):.1f}")
        print(f"   • Z range: {min(z_coords):.1f} to {max(z_coords):.1f}")
        print("   • Distribution: Random spherical galaxy pattern")
        
    except Exception as e:
        print(f"❌ Error during position regeneration: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    main()
