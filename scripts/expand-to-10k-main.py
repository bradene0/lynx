#!/usr/bin/env python3
"""
LYNX 10K Expansion Main Script
Orchestrates the expansion from 678 to 10,000 concepts
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from scripts.ingestion.database import DatabaseManager
from scripts.ingestion.embedding_generator import EmbeddingGenerator
from scripts.ingestion.arxiv_client import ArxivClient
from scripts.ingestion.wikipedia_client import WikipediaClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LynxExpansion:
    """Main orchestrator for 10K expansion"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.embedder = EmbeddingGenerator()
        self.arxiv_client = ArxivClient()
        self.wikipedia_client = WikipediaClient()
        
        self.target_total = 10000
        self.existing_count = 0
    
    async def get_existing_count(self) -> int:
        """Get current concept count"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM concepts")
                count = cur.fetchone()[0]
                logger.info(f"📊 Current concepts in database: {count}")
                return count
    
    async def run_expansion(self):
        """Execute the full 10K expansion"""
        logger.info("🚀 Starting LYNX 10K Expansion...")
        
        try:
            # Check current state
            self.existing_count = await self.get_existing_count()
            needed = self.target_total - self.existing_count
            
            if needed <= 0:
                logger.info(f"🎉 Target already reached! ({self.existing_count} concepts)")
                return
            
            logger.info(f"🎯 Need {needed} more concepts")
            
            # Calculate optimal split (85% Wikipedia, 15% arXiv)
            wikipedia_target = int(needed * 0.85)
            arxiv_target = needed - wikipedia_target
            
            logger.info(f"📋 Plan: {wikipedia_target} Wikipedia + {arxiv_target} arXiv")
            
            # Phase 1: Fetch Wikipedia concepts
            logger.info("📚 Phase 1: Fetching Wikipedia concepts...")
            wikipedia_concepts = self.wikipedia_client.fetch_concepts(wikipedia_target)
            
            # Phase 2: Fetch arXiv papers
            logger.info("📄 Phase 2: Fetching arXiv papers...")
            arxiv_papers = self.arxiv_client.fetch_papers(arxiv_target)
            
            # Combine all new concepts
            all_new_concepts = wikipedia_concepts + arxiv_papers
            logger.info(f"📊 Total new concepts collected: {len(all_new_concepts)}")
            
            if not all_new_concepts:
                logger.error("❌ No new concepts collected")
                return
            
            # Phase 3: Store in database
            logger.info("💾 Phase 3: Storing concepts...")
            stored_count = await self.db.insert_concepts(all_new_concepts)
            
            # Phase 4: Generate embeddings
            logger.info("🧠 Phase 4: Generating embeddings...")
            embeddings = []
            
            for i, concept in enumerate(all_new_concepts):
                try:
                    text = f"{concept['title']}. {concept['summary']}"
                    embedding_vector = self.embedder.generate_embedding(text)
                    
                    embedding = {
                        'id': concept['id'] + '_emb',  # Simple ID generation
                        'concept_id': concept['id'],
                        'embedding': embedding_vector.tolist(),
                        'model': 'all-MiniLM-L6-v2',
                        'created_at': concept['created_at']
                    }
                    embeddings.append(embedding)
                    
                    if (i + 1) % 100 == 0:
                        logger.info(f"🧠 Embeddings progress: {i + 1}/{len(all_new_concepts)}")
                        
                except Exception as e:
                    logger.error(f"❌ Embedding failed for {concept['title']}: {e}")
            
            embedding_count = await self.db.insert_embeddings(embeddings)
            
            # Phase 5: Generate positions (using improved algorithm)
            logger.info("🌌 Phase 5: Generating positions...")
            positions = self.generate_positions_10k(all_new_concepts)
            position_count = await self.db.insert_positions(positions)
            
            # Final summary
            final_total = self.existing_count + stored_count
            logger.info("🎉 10K Expansion Complete!")
            logger.info("📊 Final Statistics:")
            logger.info(f"   • Previous concepts: {self.existing_count}")
            logger.info(f"   • New concepts added: {stored_count}")
            logger.info(f"   • Total concepts: {final_total}")
            logger.info(f"   • New embeddings: {embedding_count}")
            logger.info(f"   • New positions: {position_count}")
            logger.info(f"   • Wikipedia concepts: {len(wikipedia_concepts)}")
            logger.info(f"   • arXiv papers: {len(arxiv_papers)}")
            logger.info(f"   • Target achieved: {'✅' if final_total >= self.target_total else '❌'}")
            
            if final_total >= self.target_total:
                logger.info("🌟 LYNX is now ready for advanced features:")
                logger.info("   • LOD system implementation")
                logger.info("   • Pathfinding algorithms") 
                logger.info("   • Wormhole discovery")
                logger.info("   • Advanced clustering")
            
        except Exception as e:
            logger.error(f"💥 Expansion failed: {e}")
            raise
    
    def generate_positions_10k(self, concepts) -> list:
        """Generate optimized positions for 10K scale"""
        import random
        import math
        
        positions = []
        
        # Expanded galaxy parameters for 10K
        galaxy_radius = 600  # Larger for 10K
        core_radius = 120
        halo_radius = 1000
        
        def generate_position():
            u = random.uniform(0, 1)
            v = random.uniform(0, 1)
            
            theta = 2 * math.pi * u
            phi = math.acos(2 * v - 1)
            
            # Even more distributed for 10K
            rand = random.random()
            if rand < 0.08:  # 8% in core
                radius = random.uniform(40, core_radius)
            elif rand < 0.72:  # 64% in main galaxy  
                radius = random.uniform(core_radius, galaxy_radius)
            else:  # 28% in halo
                radius = random.uniform(galaxy_radius, halo_radius)
            
            x = radius * math.sin(phi) * math.cos(theta)
            y = radius * math.sin(phi) * math.sin(theta)
            z = radius * math.cos(phi)
            
            return float(x), float(y), float(z)
        
        for concept in concepts:
            x, y, z = generate_position()
            
            position = {
                'concept_id': concept['id'],
                'x': x,
                'y': y,
                'z': z,
                'cluster_id': concept['category'].replace(' ', '_').lower()
            }
            positions.append(position)
        
        logger.info(f"✅ Generated {len(positions)} positions for 10K scale")
        return positions

async def main():
    """Main execution"""
    expansion = LynxExpansion()
    await expansion.run_expansion()

if __name__ == '__main__':
    asyncio.run(main())
