#!/usr/bin/env python3
"""
Smart expansion to 10K concepts without duplicates
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Set
from dotenv import load_dotenv

load_dotenv()
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from scripts.ingestion.database import DatabaseManager
from scripts.ingestion.wikipedia_client import WikipediaClient
from scripts.ingestion.arxiv_client import ArxivClient
from scripts.ingestion.embedding_generator import EmbeddingGenerator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SmartExpansion:
    """Smart expansion to 10K avoiding duplicates"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.wikipedia_client = WikipediaClient()
        self.arxiv_client = ArxivClient()
        self.embedder = EmbeddingGenerator()
        self.target_total = 10000
    
    async def get_existing_titles(self) -> Set[str]:
        """Get set of existing concept titles to avoid duplicates"""
        logger.info("📋 Getting existing concept titles...")
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT LOWER(title) FROM concepts")
                titles = cur.fetchall()
        
        existing_titles = {title[0] for title in titles}
        logger.info(f"✅ Found {len(existing_titles)} existing titles")
        return existing_titles
    
    async def get_current_counts(self):
        """Get current concept counts"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM concepts")
                total = cur.fetchone()[0]
                
                cur.execute("SELECT source, COUNT(*) FROM concepts GROUP BY source")
                by_source = dict(cur.fetchall())
        
        return total, by_source
    
    def filter_duplicates(self, concepts, existing_titles):
        """Filter out concepts that would create duplicates"""
        filtered = []
        for concept in concepts:
            title_lower = concept['title'].lower()
            if title_lower not in existing_titles:
                filtered.append(concept)
                existing_titles.add(title_lower)  # Add to set to avoid duplicates within this batch
        
        logger.info(f"🔍 Filtered {len(concepts)} → {len(filtered)} concepts (removed {len(concepts) - len(filtered)} duplicates)")
        return filtered
    
    async def expand_wikipedia(self, target_count, existing_titles):
        """Expand Wikipedia concepts intelligently"""
        logger.info(f"📚 Expanding Wikipedia concepts (target: {target_count})")
        
        # Get concepts from expanded domains
        all_concepts = []
        concepts_per_domain = target_count // len(self.wikipedia_client.expanded_domains)
        
        for domain in self.wikipedia_client.expanded_domains.keys():
            logger.info(f"🔍 Fetching from {domain}...")
            domain_concepts = self.wikipedia_client.fetch_concepts_by_domain(domain, concepts_per_domain + 50)  # Extra buffer
            
            # Filter duplicates
            filtered_concepts = self.filter_duplicates(domain_concepts, existing_titles)
            all_concepts.extend(filtered_concepts)
            
            if len(all_concepts) >= target_count:
                break
        
        return all_concepts[:target_count]
    
    async def expand_arxiv(self, target_count, existing_titles):
        """Expand arXiv papers intelligently"""
        logger.info(f"📄 Expanding arXiv papers (target: {target_count})")
        
        # Get papers from multiple categories
        arxiv_categories = [
            'cs.AI', 'cs.LG', 'cs.CV', 'cs.CL', 'cs.RO', 'cs.CR', 'cs.DB', 'cs.DS',
            'physics.gen-ph', 'cond-mat', 'quant-ph', 'astro-ph',
            'math.CO', 'math.NT', 'math.AG', 'math.ST',
            'q-bio.GN', 'q-bio.BM', 'q-bio.NC', 'econ.TH'
        ]
        
        all_papers = []
        papers_per_category = max(1, target_count // len(arxiv_categories))
        
        for category in arxiv_categories:
            try:
                logger.info(f"🔍 Fetching from {category}...")
                papers = self.arxiv_client.fetch_papers_by_category(category, papers_per_category + 20)  # Extra buffer
                
                # Filter duplicates
                filtered_papers = self.filter_duplicates(papers, existing_titles)
                all_papers.extend(filtered_papers)
                
                if len(all_papers) >= target_count:
                    break
                    
            except Exception as e:
                logger.warning(f"⚠️ Failed to fetch from {category}: {e}")
                continue
        
        return all_papers[:target_count]
    
    async def process_new_concepts(self, concepts):
        """Process new concepts: store, embed, position"""
        if not concepts:
            return 0
        
        logger.info(f"💾 Processing {len(concepts)} new concepts...")
        
        # Step 1: Store concepts
        stored_count = await self.db.insert_concepts(concepts)
        logger.info(f"✅ Stored {stored_count} concepts")
        
        # Step 2: Generate embeddings
        logger.info("🧠 Generating embeddings...")
        embeddings = []
        for concept in concepts:
            try:
                text = f"{concept['title']}. {concept['summary']}"
                embedding_vector = self.embedder.generate_embedding(text)
                
                embedding = {
                    'id': concept['id'] + '_emb',
                    'concept_id': concept['id'],
                    'embedding': embedding_vector.tolist(),
                    'model': 'all-MiniLM-L6-v2',
                    'created_at': concept['created_at']
                }
                embeddings.append(embedding)
                
            except Exception as e:
                logger.error(f"❌ Embedding failed for {concept['title']}: {e}")
        
        embedding_count = await self.db.insert_embeddings(embeddings)
        logger.info(f"✅ Generated {embedding_count} embeddings")
        
        # Step 3: Generate positions
        logger.info("🌌 Generating positions...")
        positions = self.generate_positions(concepts)
        position_count = await self.db.insert_positions(positions)
        logger.info(f"✅ Generated {position_count} positions")
        
        return stored_count
    
    def generate_positions(self, concepts):
        """Generate optimized positions for new concepts"""
        import random
        import math
        
        positions = []
        galaxy_radius = 600
        
        for concept in concepts:
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
            
            cluster_id = concept['category'].replace(' ', '_').lower() if concept['category'] else 'general'
            
            position = {
                'concept_id': concept['id'],
                'x': float(x),
                'y': float(y),
                'z': float(z),
                'cluster_id': cluster_id
            }
            positions.append(position)
        
        return positions
    
    async def run_smart_expansion(self):
        """Run the complete smart expansion"""
        logger.info("🚀 Starting smart expansion to 10K...")
        
        try:
            # Get current state
            current_total, by_source = await self.get_current_counts()
            needed = self.target_total - current_total
            
            logger.info(f"📊 Current: {current_total}, Target: {self.target_total}, Need: {needed}")
            
            if needed <= 0:
                logger.info("🎉 Already at target!")
                return
            
            # Get existing titles to avoid duplicates
            existing_titles = await self.get_existing_titles()
            
            # Plan expansion (aim for balanced mix)
            wikipedia_target = int(needed * 0.7)  # 70% Wikipedia
            arxiv_target = needed - wikipedia_target  # 30% arXiv
            
            logger.info(f"📋 Plan: {wikipedia_target} Wikipedia + {arxiv_target} arXiv")
            
            # Expand Wikipedia
            if wikipedia_target > 0:
                wikipedia_concepts = await self.expand_wikipedia(wikipedia_target, existing_titles)
                await self.process_new_concepts(wikipedia_concepts)
            
            # Expand arXiv
            if arxiv_target > 0:
                arxiv_concepts = await self.expand_arxiv(arxiv_target, existing_titles)
                await self.process_new_concepts(arxiv_concepts)
            
            # Final statistics
            final_total, final_by_source = await self.get_current_counts()
            
            logger.info("🎉 Smart expansion complete!")
            logger.info(f"📊 Final Statistics:")
            logger.info(f"   • Total concepts: {final_total}")
            for source, count in final_by_source.items():
                logger.info(f"   • {source}: {count}")
            
            if final_total >= self.target_total:
                logger.info("✅ Target achieved!")
            else:
                logger.info(f"📈 Progress: {final_total}/{self.target_total} ({final_total/self.target_total*100:.1f}%)")
                
        except Exception as e:
            logger.error(f"💥 Smart expansion failed: {e}")
            raise

async def main():
    """Main execution"""
    expansion = SmartExpansion()
    await expansion.run_smart_expansion()

if __name__ == '__main__':
    asyncio.run(main())
