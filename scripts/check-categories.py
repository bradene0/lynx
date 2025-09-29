#!/usr/bin/env python3
"""
Quick script to check actual database categories
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
            cur.execute('SELECT DISTINCT category, COUNT(*) FROM concepts GROUP BY category ORDER BY COUNT(*) DESC')
            categories = cur.fetchall()
            
    print('📊 Actual database categories:')
    for category, count in categories:
        print(f'   • "{category}": {count} concepts')
        
except Exception as e:
    print(f'Error: {e}')
