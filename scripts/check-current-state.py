#!/usr/bin/env python3
"""
Check current database state after duplicate removal
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from scripts.ingestion.database import DatabaseManager

try:
    db = DatabaseManager()
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            # Get current counts
            cur.execute('SELECT COUNT(*) FROM concepts')
            concept_count = cur.fetchone()[0]
            
            cur.execute('SELECT COUNT(*) FROM embeddings')
            embedding_count = cur.fetchone()[0]
            
            cur.execute('SELECT COUNT(*) FROM node_positions')
            position_count = cur.fetchone()[0]
            
            cur.execute('SELECT COUNT(*) FROM edges')
            edge_count = cur.fetchone()[0]
            
            # Check by source
            cur.execute('SELECT source, COUNT(*) FROM concepts GROUP BY source ORDER BY COUNT(*) DESC')
            by_source = cur.fetchall()
            
            # Check by category
            cur.execute('SELECT category, COUNT(*) FROM concepts GROUP BY category ORDER BY COUNT(*) DESC LIMIT 10')
            by_category = cur.fetchall()
            
    print('📊 Current Database State:')
    print(f'   • Total concepts: {concept_count}')
    print(f'   • Total embeddings: {embedding_count}')
    print(f'   • Total positions: {position_count}')
    print(f'   • Total edges: {edge_count}')
    
    print(f'\n📚 By Source:')
    for source, count in by_source:
        print(f'   • {source}: {count}')
    
    print(f'\n🏷️ Top Categories:')
    for category, count in by_category:
        print(f'   • {category}: {count}')
        
    print(f'\n🎯 Target: 10,000 concepts')
    print(f'📈 Need: {10000 - concept_count} more concepts')
        
except Exception as e:
    print(f'Error: {e}')
