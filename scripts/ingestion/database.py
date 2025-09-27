"""
Database management for LYNX ingestion pipeline
"""

import os
import logging
import asyncio
from typing import List, Dict, Any, Optional
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor, execute_values
    USING_PSYCOPG2 = True
except ImportError:
    # Use psycopg3
    import psycopg as psycopg2
    from psycopg.rows import dict_row
    USING_PSYCOPG2 = False
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database operations for the ingestion pipeline"""
    
    def __init__(self):
        self.connection_string = os.getenv('DATABASE_URL')
        if not self.connection_string:
            raise ValueError("DATABASE_URL environment variable not set")
    
    def get_connection(self):
        """Get a database connection"""
        return psycopg2.connect(self.connection_string)
    
    async def update_status(
        self, 
        status: str, 
        processed_concepts: int = 0,
        total_concepts: int = 0,
        total_embeddings: int = 0,
        total_edges: int = 0,
        error_message: Optional[str] = None
    ):
        """Update the ingestion status"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE ingestion_status 
                    SET status = %s,
                        processed_concepts = %s,
                        total_concepts = %s,
                        total_embeddings = %s,
                        total_edges = %s,
                        last_updated = NOW(),
                        error_message = %s
                    WHERE id = 1
                """, (status, processed_concepts, total_concepts, 
                     total_embeddings, total_edges, error_message))
                conn.commit()
    
    async def insert_concepts(self, concepts: List[Dict[str, Any]]) -> int:
        """Insert concepts into the database"""
        if not concepts:
            return 0
            
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                if USING_PSYCOPG2:
                    # Use psycopg2 execute_values
                    values = [
                        (
                            concept['id'],
                            concept['title'],
                            concept['summary'],
                            concept['source'],
                            concept['source_id'],
                            concept['url'],
                            concept.get('category')
                        )
                        for concept in concepts
                    ]
                    
                    execute_values(
                        cur,
                        """
                        INSERT INTO concepts (id, title, summary, source, source_id, url, category)
                        VALUES %s
                        ON CONFLICT (id) DO UPDATE SET
                            title = EXCLUDED.title,
                            summary = EXCLUDED.summary,
                            updated_at = NOW()
                        """,
                        values,
                        template=None,
                        page_size=1000
                    )
                else:
                    # Use psycopg3 executemany
                    for concept in concepts:
                        cur.execute(
                            """
                            INSERT INTO concepts (id, title, summary, source, source_id, url, category)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (id) DO UPDATE SET
                                title = EXCLUDED.title,
                                summary = EXCLUDED.summary,
                                updated_at = NOW()
                            """,
                            (
                                concept['id'],
                                concept['title'],
                                concept['summary'],
                                concept['source'],
                                concept['source_id'],
                                concept['url'],
                                concept.get('category')
                            )
                        )
                
                conn.commit()
                logger.info(f"Inserted/updated {len(concepts)} concepts")
                return len(concepts)
    
    async def insert_embeddings(self, embeddings: List[Dict[str, Any]]) -> int:
        """Insert embeddings into the database"""
        if not embeddings:
            return 0
            
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                if USING_PSYCOPG2:
                    # Use psycopg2 execute_values
                    values = [
                        (
                            embedding['id'],
                            embedding['concept_id'],
                            embedding['embedding'],  # numpy array will be converted to vector
                            embedding.get('model', 'all-MiniLM-L6-v2')
                        )
                        for embedding in embeddings
                    ]
                    
                    execute_values(
                        cur,
                        """
                        INSERT INTO embeddings (id, concept_id, embedding, model)
                        VALUES %s
                        ON CONFLICT (id) DO UPDATE SET
                            embedding = EXCLUDED.embedding,
                            model = EXCLUDED.model
                        """,
                        values,
                        template=None,
                        page_size=100  # Smaller batches for large vectors
                    )
                else:
                    # Use psycopg3 executemany
                    for embedding in embeddings:
                        cur.execute(
                            """
                            INSERT INTO embeddings (id, concept_id, embedding, model)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (id) DO UPDATE SET
                                embedding = EXCLUDED.embedding,
                                model = EXCLUDED.model
                            """,
                            (
                                embedding['id'],
                                embedding['concept_id'],
                                embedding['embedding'],
                                embedding.get('model', 'all-MiniLM-L6-v2')
                            )
                        )
                
                conn.commit()
                logger.info(f"Inserted/updated {len(embeddings)} embeddings")
                return len(embeddings)
    
    async def insert_edges(self, edges: List[Dict[str, Any]]) -> int:
        """Insert edges into the database"""
        if not edges:
            return 0
            
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Prepare data for batch insert
                values = [
                    (
                        edge['id'],
                        edge['source_id'],
                        edge['target_id'],
                        edge['weight'],
                        edge['edge_type']
                    )
                    for edge in edges
                ]
                
                execute_values(
                    cur,
                    """
                    INSERT INTO edges (id, source_id, target_id, weight, edge_type)
                    VALUES %s
                    ON CONFLICT (source_id, target_id, edge_type) DO UPDATE SET
                        weight = EXCLUDED.weight
                    """,
                    values,
                    template=None,
                    page_size=1000
                )
                
                conn.commit()
                logger.info(f"Inserted/updated {len(edges)} edges")
                return len(edges)
    
    async def insert_positions(self, positions: List[Dict[str, Any]]) -> int:
        """Insert node positions into the database"""
        if not positions:
            return 0
            
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                if USING_PSYCOPG2:
                    # Use psycopg2 execute_values
                    values = [
                        (
                            position['concept_id'],
                            position['x'],
                            position['y'],
                            position['z'],
                            position.get('cluster_id')
                        )
                        for position in positions
                    ]
                    
                    execute_values(
                        cur,
                        """
                        INSERT INTO node_positions (concept_id, x, y, z, cluster_id)
                        VALUES %s
                        ON CONFLICT (concept_id) DO UPDATE SET
                            x = EXCLUDED.x,
                            y = EXCLUDED.y,
                            z = EXCLUDED.z,
                            cluster_id = EXCLUDED.cluster_id,
                            updated_at = NOW()
                        """,
                        values,
                        template=None,
                        page_size=1000
                    )
                else:
                    # Use psycopg3 executemany
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
    
    async def get_existing_concepts(self) -> List[str]:
        """Get list of existing concept IDs"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM concepts")
                return [row[0] for row in cur.fetchall()]
    
    async def cleanup_orphaned_data(self):
        """Clean up orphaned embeddings, edges, and positions"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Clean up orphaned embeddings
                cur.execute("""
                    DELETE FROM embeddings 
                    WHERE concept_id NOT IN (SELECT id FROM concepts)
                """)
                
                # Clean up orphaned edges
                cur.execute("""
                    DELETE FROM edges 
                    WHERE source_id NOT IN (SELECT id FROM concepts)
                       OR target_id NOT IN (SELECT id FROM concepts)
                """)
                
                # Clean up orphaned positions
                cur.execute("""
                    DELETE FROM node_positions 
                    WHERE concept_id NOT IN (SELECT id FROM concepts)
                """)
                
                conn.commit()
                logger.info("Cleaned up orphaned data")
