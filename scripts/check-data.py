#!/usr/bin/env python3
"""
Check what data we have in the database
"""

import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.ingestion.database import DatabaseManager

async def check_data():
    db = DatabaseManager()
    
    print("🔍 Checking LYNX database contents...")
    
    # Check concepts
    try:
        concepts = await db.get_all_concepts()
        print(f"📊 Total concepts: {len(concepts)}")
        if concepts:
            print(f"📚 Sample concepts: {[c['title'] for c in concepts[:5]]}")
    except Exception as e:
        print(f"❌ Error getting concepts: {e}")
    
    # Check positions  
    try:
        positions = await db.get_all_positions()
        print(f"🌌 Total positions: {len(positions)}")
        if positions:
            print(f"🎯 Sample positions: {[(p['x'], p['y'], p['z']) for p in positions[:3]]}")
    except Exception as e:
        print(f"❌ Error getting positions: {e}")
    
    # Check edges
    try:
        edges = await db.get_all_edges()
        print(f"🔗 Total edges: {len(edges)}")
        if edges:
            print(f"🔗 Sample edges: {[(e['source_id'][:8], e['target_id'][:8], e['weight']) for e in edges[:3]]}")
    except Exception as e:
        print(f"❌ Error getting edges: {e}")

if __name__ == '__main__':
    asyncio.run(check_data())
