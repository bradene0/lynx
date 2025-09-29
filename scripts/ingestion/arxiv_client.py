"""
Robust arXiv API Client for LYNX
Handles XML parsing, rate limiting, and error recovery
"""

import requests
import xml.etree.ElementTree as ET
import time
import logging
import re
from typing import List, Dict, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class ArxivClient:
    """Production-ready arXiv API client with proper error handling"""
    
    def __init__(self):
        self.base_url = "http://export.arxiv.org/api/query"
        self.rate_limit_delay = 3.0  # arXiv recommends 3 seconds
        self.timeout = 30
        self.max_retries = 3
        
        # Validated categories that work reliably
        self.categories = {
            'cs.AI': 'Artificial Intelligence',
            'cs.LG': 'Machine Learning', 
            'cs.CV': 'Computer Vision',
            'cs.CL': 'Computational Linguistics',
            'cs.RO': 'Robotics',
            'cs.CR': 'Cryptography and Security',
            'cs.DS': 'Data Structures and Algorithms',
            'cs.DB': 'Databases',
            'quant-ph': 'Quantum Physics',
            'physics.gen-ph': 'General Physics',
            'cond-mat.str-el': 'Condensed Matter',
            'math.CO': 'Combinatorics',
            'math.NT': 'Number Theory',
            'q-bio.BM': 'Biomolecules',
            'q-bio.GN': 'Genomics',
            'stat.ML': 'Machine Learning Statistics'
        }
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""
        
        # Remove extra whitespace and newlines
        cleaned = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common LaTeX artifacts
        cleaned = re.sub(r'\$[^$]*\$', '', cleaned)  # Remove inline math
        cleaned = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', cleaned)  # Remove LaTeX commands
        
        return cleaned[:1500]  # Truncate to reasonable length
    
    def _extract_arxiv_id(self, id_url: str) -> str:
        """Extract clean arXiv ID from URL"""
        try:
            # Handle various arXiv URL formats
            if '/abs/' in id_url:
                arxiv_id = id_url.split('/abs/')[-1]
            else:
                arxiv_id = id_url.split('/')[-1]
            
            # Remove version number (e.g., v1, v2)
            arxiv_id = re.sub(r'v\d+$', '', arxiv_id)
            
            return arxiv_id
        except Exception:
            return ""
    
    def _validate_paper(self, title: str, summary: str, arxiv_id: str) -> bool:
        """Validate paper content quality"""
        if not title or not summary or not arxiv_id:
            return False
        
        # Minimum content requirements
        if len(title.strip()) < 10:
            return False
        
        if len(summary.strip()) < 100:
            return False
        
        # Check for valid arXiv ID format
        if not re.match(r'^\d{4}\.\d{4,5}$', arxiv_id):
            return False
        
        return True
    
    def fetch_papers_by_category(self, category: str, max_results: int = 50) -> List[Dict]:
        """Fetch papers for a specific category with robust error handling"""
        papers = []
        
        if category not in self.categories:
            logger.warning(f"Unknown category: {category}")
            return papers
        
        category_name = self.categories[category]
        
        for attempt in range(self.max_retries):
            try:
                # Build query URL
                params = {
                    'search_query': f'cat:{category}',
                    'start': 0,
                    'max_results': max_results,
                    'sortBy': 'submittedDate',
                    'sortOrder': 'descending'
                }
                
                headers = {
                    'User-Agent': 'LYNX Academic Explorer/2.0 (research purposes)'
                }
                
                logger.info(f"📡 Fetching {category} papers (attempt {attempt + 1})")
                
                response = requests.get(
                    self.base_url,
                    params=params,
                    headers=headers,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    papers = self._parse_arxiv_response(response.content, category_name)
                    logger.info(f"✅ {category}: {len(papers)} papers fetched")
                    break
                    
                elif response.status_code == 429:
                    # Rate limited - wait longer
                    wait_time = self.rate_limit_delay * (attempt + 1)
                    logger.warning(f"⏳ Rate limited, waiting {wait_time}s")
                    time.sleep(wait_time)
                    continue
                    
                else:
                    logger.warning(f"⚠️ HTTP {response.status_code} for {category}")
                    if attempt == self.max_retries - 1:
                        break
                    time.sleep(self.rate_limit_delay)
                    
            except requests.exceptions.Timeout:
                logger.warning(f"⏰ Timeout for {category} (attempt {attempt + 1})")
                if attempt < self.max_retries - 1:
                    time.sleep(self.rate_limit_delay * 2)
                    
            except Exception as e:
                logger.error(f"❌ Error fetching {category}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.rate_limit_delay)
        
        # Rate limiting between categories
        time.sleep(self.rate_limit_delay)
        return papers
    
    def _parse_arxiv_response(self, xml_content: bytes, category_name: str) -> List[Dict]:
        """Parse arXiv XML response with robust namespace handling"""
        papers = []
        
        try:
            root = ET.fromstring(xml_content)
            
            # Handle namespace variations
            namespaces = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }
            
            # Find entries with flexible namespace handling
            entries = root.findall('.//atom:entry', namespaces)
            if not entries:
                # Fallback without namespace
                entries = root.findall('.//entry')
            
            logger.debug(f"Found {len(entries)} entries in XML response")
            
            for entry in entries:
                try:
                    # Extract fields with multiple fallback strategies
                    title_elem = entry.find('atom:title', namespaces)
                    if title_elem is None:
                        title_elem = entry.find('title')
                    
                    summary_elem = entry.find('atom:summary', namespaces)
                    if summary_elem is None:
                        summary_elem = entry.find('summary')
                    
                    id_elem = entry.find('atom:id', namespaces)
                    if id_elem is None:
                        id_elem = entry.find('id')
                    
                    if title_elem is None or summary_elem is None or id_elem is None:
                        continue
                    
                    # Extract and clean content
                    title = self._clean_text(title_elem.text)
                    summary = self._clean_text(summary_elem.text)
                    arxiv_id = self._extract_arxiv_id(id_elem.text)
                    
                    # Validate content
                    if not self._validate_paper(title, summary, arxiv_id):
                        continue
                    
                    paper = {
                        'id': str(uuid.uuid4()),
                        'title': title,
                        'summary': summary,
                        'category': f"Academic - {category_name}",
                        'source': 'arxiv',
                        'source_id': arxiv_id,
                        'url': f"https://arxiv.org/abs/{arxiv_id}",
                        'created_at': datetime.now()
                    }
                    
                    papers.append(paper)
                    
                except Exception as e:
                    logger.debug(f"Skipping malformed entry: {e}")
                    continue
                    
        except ET.ParseError as e:
            logger.error(f"XML parsing failed: {e}")
        except Exception as e:
            logger.error(f"Response parsing failed: {e}")
        
        return papers
    
    def fetch_papers(self, total_limit: int = 1500) -> List[Dict]:
        """Fetch papers across all categories with balanced distribution"""
        all_papers = []
        papers_per_category = max(1, total_limit // len(self.categories))
        
        logger.info(f"🎯 Fetching {total_limit} total papers ({papers_per_category} per category)")
        
        for category in self.categories.keys():
            try:
                category_papers = self.fetch_papers_by_category(category, papers_per_category)
                all_papers.extend(category_papers)
                
                logger.info(f"📊 Progress: {len(all_papers)}/{total_limit} papers")
                
                # Stop if we've reached our target
                if len(all_papers) >= total_limit:
                    break
                    
            except Exception as e:
                logger.error(f"Category {category} failed completely: {e}")
                continue
        
        # Trim to exact limit if needed
        if len(all_papers) > total_limit:
            all_papers = all_papers[:total_limit]
        
        logger.info(f"🎉 arXiv fetch complete: {len(all_papers)} papers")
        return all_papers

# Test function for validation
async def test_arxiv_client():
    """Test the arXiv client with a small sample"""
    client = ArxivClient()
    
    # Test single category
    test_papers = client.fetch_papers_by_category('cs.AI', 5)
    
    if test_papers:
        logger.info("✅ arXiv client test passed")
        for paper in test_papers[:2]:
            logger.info(f"Sample: {paper['title'][:50]}...")
        return True
    else:
        logger.error("❌ arXiv client test failed")
        return False

if __name__ == '__main__':
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_arxiv_client())
