"""
arXiv data ingestion for LYNX
Fetches arXiv papers and extracts concepts
"""

import asyncio
import logging
import requests
import time
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from urllib.parse import quote
import hashlib
import re

logger = logging.getLogger(__name__)

class ArxivIngester:
    """Ingests arXiv papers for concept extraction"""
    
    def __init__(self):
        self.session = requests.Session()
        self.base_url = 'http://export.arxiv.org/api/query'
        self.rate_limit_delay = 3.0  # 3 seconds between requests (arXiv requirement)
        
        # Subject categories we're interested in (no finance as requested)
        self.categories = {
            'cs.AI': 'Artificial Intelligence',
            'cs.LG': 'Machine Learning', 
            'cs.CL': 'Computational Linguistics',
            'cs.CV': 'Computer Vision',
            'physics.gen-ph': 'General Physics',
            'quant-ph': 'Quantum Physics',
            'math.CO': 'Combinatorics',
            'math.DS': 'Dynamical Systems',
            'q-bio.GN': 'Genomics',
            'q-bio.MN': 'Molecular Networks',
            'stat.ML': 'Machine Learning Statistics'
        }
        
    def generate_concept_id(self, arxiv_id: str) -> str:
        """Generate a unique concept ID from arXiv ID"""
        content = f"arxiv:{arxiv_id}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def search_category(self, category: str, max_results: int = 500) -> List[Dict[str, Any]]:
        """Search for papers in a specific category"""
        papers = []
        start = 0
        batch_size = 100  # arXiv API limit
        
        try:
            while len(papers) < max_results:
                # Construct query
                params = {
                    'search_query': f'cat:{category}',
                    'start': start,
                    'max_results': min(batch_size, max_results - len(papers)),
                    'sortBy': 'submittedDate',
                    'sortOrder': 'descending'
                }
                
                logger.info(f"Fetching {category} papers: {start}-{start + batch_size}")
                
                response = self.session.get(self.base_url, params=params)
                response.raise_for_status()
                
                # Parse XML response
                root = ET.fromstring(response.content)
                entries = root.findall('{http://www.w3.org/2005/Atom}entry')
                
                if not entries:
                    logger.info(f"No more papers found for {category}")
                    break
                
                for entry in entries:
                    paper = self._parse_paper_entry(entry, category)
                    if paper:
                        papers.append(paper)
                
                start += batch_size
                
                # Rate limiting - arXiv requires 3 second delays
                await asyncio.sleep(self.rate_limit_delay)
                
        except Exception as e:
            logger.error(f"Error searching category {category}: {e}")
        
        logger.info(f"Found {len(papers)} papers for {category}")
        return papers
    
    def _parse_paper_entry(self, entry: ET.Element, category: str) -> Optional[Dict[str, Any]]:
        """Parse a single paper entry from arXiv XML"""
        try:
            # Extract arXiv ID
            id_elem = entry.find('{http://www.w3.org/2005/Atom}id')
            if id_elem is None:
                return None
            
            arxiv_url = id_elem.text
            arxiv_id = arxiv_url.split('/')[-1]  # Extract ID from URL
            
            # Extract title
            title_elem = entry.find('{http://www.w3.org/2005/Atom}title')
            title = title_elem.text.strip() if title_elem is not None else ''
            
            # Extract abstract
            summary_elem = entry.find('{http://www.w3.org/2005/Atom}summary')
            abstract = summary_elem.text.strip() if summary_elem is not None else ''
            
            # Extract authors
            authors = []
            for author in entry.findall('{http://www.w3.org/2005/Atom}author'):
                name_elem = author.find('{http://www.w3.org/2005/Atom}name')
                if name_elem is not None:
                    authors.append(name_elem.text)
            
            # Extract publication date
            published_elem = entry.find('{http://www.w3.org/2005/Atom}published')
            published_date = published_elem.text if published_elem is not None else ''
            
            # Clean up title and abstract
            title = re.sub(r'\s+', ' ', title).strip()
            abstract = re.sub(r'\s+', ' ', abstract).strip()
            
            # Skip if essential fields are missing
            if not title or not abstract or len(abstract) < 100:
                return None
            
            # Create concept
            concept = {
                'id': self.generate_concept_id(arxiv_id),
                'title': title,
                'summary': abstract,
                'source': 'arxiv',
                'source_id': arxiv_id,
                'url': arxiv_url,
                'category': self.categories.get(category, 'Science'),
                'metadata': {
                    'authors': authors,
                    'published_date': published_date,
                    'arxiv_category': category
                }
            }
            
            return concept
            
        except Exception as e:
            logger.error(f"Error parsing paper entry: {e}")
            return None
    
    async def get_recent_papers(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get recent papers across all categories"""
        papers = []
        papers_per_category = limit // len(self.categories)
        
        for category, category_name in self.categories.items():
            logger.info(f"Fetching papers from {category_name} ({category})")
            
            try:
                category_papers = await self.search_category(
                    category, 
                    max_results=papers_per_category
                )
                papers.extend(category_papers)
                
                logger.info(f"Added {len(category_papers)} papers from {category}")
                
            except Exception as e:
                logger.error(f"Error fetching papers from {category}: {e}")
                continue
        
        # Sort by quality indicators (could be citation count, etc.)
        # For now, we'll just shuffle to get variety
        import random
        random.shuffle(papers)
        
        return papers[:limit]
    
    async def ingest(self, limit: int = 3000) -> List[Dict[str, Any]]:
        """Main ingestion method"""
        logger.info(f"Starting arXiv ingestion for {limit} concepts")
        
        # Get papers
        papers = await self.get_recent_papers(limit)
        
        # Convert to concepts format
        concepts = []
        for paper in papers:
            # Remove metadata for storage (keep it simple for MVP)
            concept = {
                'id': paper['id'],
                'title': paper['title'],
                'summary': paper['summary'],
                'source': paper['source'],
                'source_id': paper['source_id'],
                'url': paper['url'],
                'category': paper['category']
            }
            concepts.append(concept)
        
        logger.info(f"arXiv ingestion complete: {len(concepts)} concepts extracted")
        return concepts
