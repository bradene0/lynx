"""
Wikipedia data ingestion for LYNX
Fetches Wikipedia articles and extracts concepts
"""

import asyncio
import logging
import requests
import time
from typing import List, Dict, Any, Optional
from urllib.parse import quote
import hashlib
import os

logger = logging.getLogger(__name__)

class WikipediaIngester:
    """Ingests Wikipedia articles for concept extraction"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': os.getenv('WIKIPEDIA_USER_AGENT', 'LYNX/1.0 (contact@example.com)')
        })
        self.base_url = 'https://en.wikipedia.org/api/rest_v1'
        self.api_url = 'https://en.wikipedia.org/w/api.php'
        self.rate_limit_delay = 0.2  # 200ms between requests (5 req/sec)
        
    def generate_concept_id(self, title: str, source: str = 'wikipedia') -> str:
        """Generate a unique concept ID"""
        content = f"{source}:{title}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def get_featured_articles(self, limit: int = 1000) -> List[str]:
        """Get list of featured articles as high-quality seed content"""
        try:
            # Get featured articles
            params = {
                'action': 'query',
                'format': 'json',
                'list': 'categorymembers',
                'cmtitle': 'Category:Featured articles',
                'cmlimit': min(limit, 500),  # API limit
                'cmnamespace': 0  # Main namespace only
            }
            
            response = self.session.get(self.api_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            articles = []
            if 'query' in data and 'categorymembers' in data['query']:
                articles = [page['title'] for page in data['query']['categorymembers']]
            
            logger.info(f"Found {len(articles)} featured articles")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching featured articles: {e}")
            return []
    
    async def get_random_articles(self, limit: int = 1000) -> List[str]:
        """Get random articles to supplement featured content"""
        articles = []
        batch_size = 50  # Get articles in batches
        
        try:
            for _ in range(0, limit, batch_size):
                params = {
                    'action': 'query',
                    'format': 'json',
                    'list': 'random',
                    'rnlimit': min(batch_size, limit - len(articles)),
                    'rnnamespace': 0  # Main namespace only
                }
                
                response = self.session.get(self.api_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if 'query' in data and 'random' in data['query']:
                    batch_articles = [page['title'] for page in data['query']['random']]
                    articles.extend(batch_articles)
                
                # Rate limiting
                await asyncio.sleep(self.rate_limit_delay)
                
                if len(articles) >= limit:
                    break
            
            logger.info(f"Found {len(articles)} random articles")
            return articles[:limit]
            
        except Exception as e:
            logger.error(f"Error fetching random articles: {e}")
            return articles
    
    async def get_article_content(self, title: str) -> Optional[Dict[str, Any]]:
        """Get article content and metadata"""
        try:
            # Get page summary from REST API
            encoded_title = quote(title.replace(' ', '_'))
            summary_url = f"{self.base_url}/page/summary/{encoded_title}"
            
            response = self.session.get(summary_url)
            response.raise_for_status()
            data = response.json()
            
            # Skip disambiguation pages and redirects
            if data.get('type') in ['disambiguation', 'redirect']:
                return None
            
            # Extract relevant information
            concept = {
                'id': self.generate_concept_id(title),
                'title': data.get('title', title),
                'summary': data.get('extract', ''),
                'source': 'wikipedia',
                'source_id': str(data.get('pageid', '')),
                'url': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                'category': self._extract_category(data)
            }
            
            # Validate required fields
            if not concept['summary'] or len(concept['summary']) < 50:
                return None
            
            return concept
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.debug(f"Article not found: {title}")
            else:
                logger.warning(f"HTTP error for {title}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching article {title}: {e}")
            return None
    
    def _extract_category(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract primary category from article data"""
        # This is a simplified categorization
        # In a full implementation, we'd use Wikipedia's category system
        
        title = data.get('title', '').lower()
        extract = data.get('extract', '').lower()
        
        # Science and technology
        if any(term in title or term in extract for term in [
            'physics', 'chemistry', 'biology', 'mathematics', 'computer', 
            'technology', 'engineering', 'science', 'quantum', 'molecular'
        ]):
            return 'Science & Technology'
        
        # History
        elif any(term in title or term in extract for term in [
            'war', 'battle', 'empire', 'dynasty', 'ancient', 'medieval',
            'century', 'historical', 'revolution'
        ]):
            return 'History'
        
        # Arts and culture
        elif any(term in title or term in extract for term in [
            'art', 'music', 'literature', 'painting', 'sculpture',
            'novel', 'film', 'theater', 'culture'
        ]):
            return 'Arts & Culture'
        
        # Philosophy and religion
        elif any(term in title or term in extract for term in [
            'philosophy', 'philosopher', 'religion', 'theology',
            'ethics', 'metaphysics', 'epistemology'
        ]):
            return 'Philosophy & Religion'
        
        # Geography and places
        elif any(term in title or term in extract for term in [
            'city', 'country', 'mountain', 'river', 'ocean',
            'continent', 'geography', 'located'
        ]):
            return 'Geography'
        
        return 'General'
    
    async def ingest(self, limit: int = 7000) -> List[Dict[str, Any]]:
        """Main ingestion method"""
        logger.info(f"Starting Wikipedia ingestion for {limit} concepts")
        
        # Get article titles
        featured_limit = min(1000, limit // 2)  # Up to 50% featured articles
        random_limit = limit - featured_limit
        
        logger.info("Fetching featured articles...")
        featured_articles = await self.get_featured_articles(featured_limit)
        
        logger.info("Fetching random articles...")
        random_articles = await self.get_random_articles(random_limit)
        
        all_titles = featured_articles + random_articles
        logger.info(f"Total articles to process: {len(all_titles)}")
        
        # Process articles
        concepts = []
        processed = 0
        
        for title in all_titles:
            try:
                concept = await self.get_article_content(title)
                if concept:
                    concepts.append(concept)
                
                processed += 1
                if processed % 100 == 0:
                    logger.info(f"Processed {processed}/{len(all_titles)} articles, "
                              f"extracted {len(concepts)} concepts")
                
                # Rate limiting
                await asyncio.sleep(self.rate_limit_delay)
                
            except Exception as e:
                logger.error(f"Error processing article {title}: {e}")
                continue
        
        logger.info(f"Wikipedia ingestion complete: {len(concepts)} concepts extracted")
        return concepts
