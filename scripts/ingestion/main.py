#!/usr/bin/env python3
"""
LYNX Data Ingestion Pipeline
Main entry point for ingesting Wikipedia and arXiv data
"""

import os
import sys
import logging
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from scripts.ingestion.wikipedia_ingester import WikipediaIngester
from scripts.ingestion.arxiv_ingester import ArxivIngester
from scripts.ingestion.embedding_generator import EmbeddingGenerator
from scripts.ingestion.graph_builder import GraphBuilder
from scripts.ingestion.database import DatabaseManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ingestion.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class IngestionPipeline:
    """Main ingestion pipeline orchestrator"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.wikipedia_ingester = WikipediaIngester()
        self.arxiv_ingester = ArxivIngester()
        self.embedding_generator = EmbeddingGenerator()
        self.graph_builder = GraphBuilder()
        
    async def run_full_pipeline(self, target_concepts: int = 10000):
        """Run the complete ingestion pipeline"""
        logger.info(f"Starting LYNX ingestion pipeline for {target_concepts} concepts")
        
        try:
            # Update status
            await self.db.update_status('ingesting', 0, target_concepts)
            
            # Phase 1: Ingest raw data
            logger.info("Phase 1: Ingesting Wikipedia data...")
            wikipedia_concepts = await self.wikipedia_ingester.ingest(
                limit=int(target_concepts * 0.7)  # 70% Wikipedia
            )
            
            logger.info("Phase 1: Ingesting arXiv data...")
            arxiv_concepts = await self.arxiv_ingester.ingest(
                limit=int(target_concepts * 0.3)  # 30% arXiv
            )
            
            all_concepts = wikipedia_concepts + arxiv_concepts
            logger.info(f"Phase 1 complete: {len(all_concepts)} concepts ingested")
            
            # Phase 2: Generate embeddings
            await self.db.update_status('embedding', len(all_concepts), target_concepts)
            logger.info("Phase 2: Generating embeddings...")
            
            embeddings = await self.embedding_generator.generate_embeddings(all_concepts)
            logger.info(f"Phase 2 complete: {len(embeddings)} embeddings generated")
            
            # Phase 3: Build graph
            await self.db.update_status('building_graph', len(all_concepts), target_concepts)
            logger.info("Phase 3: Building knowledge graph...")
            
            edges = await self.graph_builder.build_graph(all_concepts, embeddings)
            logger.info(f"Phase 3 complete: {len(edges)} edges created")
            
            # Phase 4: Compute positions
            logger.info("Phase 4: Computing node positions...")
            positions = await self.graph_builder.compute_positions(all_concepts, edges)
            logger.info(f"Phase 4 complete: {len(positions)} positions computed")
            
            # Update final status
            await self.db.update_status(
                'complete', 
                len(all_concepts), 
                target_concepts,
                total_embeddings=len(embeddings),
                total_edges=len(edges)
            )
            
            logger.info("🌌 LYNX ingestion pipeline completed successfully!")
            logger.info(f"📊 Final stats:")
            logger.info(f"   - Concepts: {len(all_concepts)}")
            logger.info(f"   - Embeddings: {len(embeddings)}")
            logger.info(f"   - Edges: {len(edges)}")
            logger.info(f"   - Positions: {len(positions)}")
            
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}")
            await self.db.update_status('error', error_message=str(e))
            raise
    
    async def run_incremental_update(self):
        """Run incremental update for existing data"""
        logger.info("Starting incremental update...")
        # TODO: Implement incremental updates
        pass

async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='LYNX Data Ingestion Pipeline')
    parser.add_argument('--concepts', type=int, default=10000, 
                       help='Target number of concepts to ingest')
    parser.add_argument('--incremental', action='store_true',
                       help='Run incremental update instead of full pipeline')
    
    args = parser.parse_args()
    
    pipeline = IngestionPipeline()
    
    if args.incremental:
        await pipeline.run_incremental_update()
    else:
        await pipeline.run_full_pipeline(args.concepts)

if __name__ == '__main__':
    asyncio.run(main())
