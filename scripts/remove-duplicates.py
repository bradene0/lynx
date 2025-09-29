#!/usr/bin/env python3
"""
Remove duplicate concepts from LYNX database
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from scripts.ingestion.database import DatabaseManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DuplicateRemover:
    """Remove duplicate concepts and clean up related data"""
    
    def __init__(self):
        self.db = DatabaseManager()
    
    async def find_duplicates(self):
        """Find duplicate concepts by title"""
        logger.info("🔍 Finding duplicate concepts...")
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                # Find concepts with same title
                cur.execute("""
                    SELECT title, COUNT(*) as count, 
                           array_agg(id ORDER BY created_at) as ids,
                           array_agg(source ORDER BY created_at) as sources
                    FROM concepts 
                    GROUP BY title
                    HAVING COUNT(*) > 1
                    ORDER BY COUNT(*) DESC
                """)
                
                duplicates = cur.fetchall()
        
        logger.info(f"📊 Found {len(duplicates)} sets of duplicates:")
        
        duplicate_info = []
        total_to_remove = 0
        
        for title, count, ids, sources in duplicates:
            logger.info(f"   • '{title}': {count} copies ({', '.join(sources)})")
            
            # Keep the first one (oldest), mark others for removal
            keep_id = ids[0]
            remove_ids = ids[1:]
            
            duplicate_info.append({
                'title': title,
                'keep_id': keep_id,
                'remove_ids': remove_ids,
                'count': count
            })
            
            total_to_remove += len(remove_ids)
        
        logger.info(f"📊 Total concepts to remove: {total_to_remove}")
        return duplicate_info
    
    async def remove_duplicates(self, duplicate_info):
        """Remove duplicate concepts and related data"""
        logger.info("🗑️ Removing duplicate concepts...")
        
        total_removed = 0
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                for dup in duplicate_info:
                    title = dup['title']
                    remove_ids = dup['remove_ids']
                    
                    logger.info(f"🔄 Processing '{title}' - removing {len(remove_ids)} duplicates")
                    
                    for concept_id in remove_ids:
                        # Remove related data first (due to foreign key constraints)
                        
                        # Remove embeddings
                        cur.execute("DELETE FROM embeddings WHERE concept_id = %s", (concept_id,))
                        
                        # Remove positions
                        cur.execute("DELETE FROM node_positions WHERE concept_id = %s", (concept_id,))
                        
                        # Remove edges (both source and target)
                        cur.execute("DELETE FROM edges WHERE source_id = %s OR target_id = %s", 
                                  (concept_id, concept_id))
                        
                        # Remove concept
                        cur.execute("DELETE FROM concepts WHERE id = %s", (concept_id,))
                        
                        total_removed += 1
                        
                        if total_removed % 10 == 0:
                            logger.info(f"   Removed {total_removed} duplicates...")
                
                conn.commit()
        
        logger.info(f"✅ Removed {total_removed} duplicate concepts")
        return total_removed
    
    async def update_statistics(self):
        """Update final statistics"""
        logger.info("📊 Updating statistics...")
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                # Get final counts
                cur.execute("SELECT COUNT(*) FROM concepts")
                concept_count = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM embeddings")
                embedding_count = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM node_positions")
                position_count = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM edges")
                edge_count = cur.fetchone()[0]
        
        logger.info(f"📈 Final Statistics:")
        logger.info(f"   • Concepts: {concept_count}")
        logger.info(f"   • Embeddings: {embedding_count}")
        logger.info(f"   • Positions: {position_count}")
        logger.info(f"   • Edges: {edge_count}")

async def main():
    """Main execution"""
    remover = DuplicateRemover()
    
    try:
        # Find duplicates
        duplicate_info = await remover.find_duplicates()
        
        if not duplicate_info:
            logger.info("✅ No duplicates found!")
            return
        
        # Remove duplicates
        removed_count = await remover.remove_duplicates(duplicate_info)
        
        # Update statistics
        await remover.update_statistics()
        
        logger.info("🎉 Duplicate removal complete!")
        logger.info("🔄 Refresh your browser to see the cleaned data")
        
    except Exception as e:
        logger.error(f"💥 Duplicate removal failed: {e}")
        raise

if __name__ == '__main__':
    asyncio.run(main())
