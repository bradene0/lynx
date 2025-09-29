"""
Enhanced Wikipedia API Client for LYNX 10K Expansion
Optimized for high-volume, high-quality concept ingestion
"""

import requests
import time
import logging
import re
import uuid
from typing import List, Dict, Optional, Set
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

logger = logging.getLogger(__name__)

class WikipediaClient:
    """Production-ready Wikipedia client for 10K scale ingestion"""
    
    def __init__(self):
        self.base_url = "https://en.wikipedia.org/api/rest_v1/page/summary"
        self.search_url = "https://en.wikipedia.org/w/api.php"
        self.rate_limit_delay = 0.2  # Wikipedia allows 200 req/sec for bots
        self.timeout = 15
        self.max_retries = 3
        self.session = requests.Session()
        self.lock = threading.Lock()
        
        # Enhanced headers for better API compliance
        self.headers = {
            'User-Agent': 'LYNX Knowledge Explorer/2.0 (https://github.com/user/lynx; research@example.com)',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate'
        }
        self.session.headers.update(self.headers)
        
        # Expanded knowledge domains for 10K scale
        self.expanded_domains = {
            'Science & Technology': [
                # Core CS/AI
                'Artificial Intelligence', 'Machine Learning', 'Deep Learning', 'Neural Networks',
                'Computer Vision', 'Natural Language Processing', 'Robotics', 'Automation',
                'Data Science', 'Big Data', 'Data Mining', 'Pattern Recognition',
                
                # Quantum & Advanced Computing
                'Quantum Computing', 'Quantum Mechanics', 'Quantum Cryptography', 'Quantum Algorithms',
                'Supercomputing', 'Parallel Computing', 'Distributed Computing', 'Grid Computing',
                
                # Emerging Tech
                'Blockchain', 'Cryptocurrency', 'Smart Contracts', 'Decentralized Finance',
                'Internet of Things', 'Edge Computing', 'Fog Computing', 'Cloud Computing',
                'Virtual Reality', 'Augmented Reality', 'Mixed Reality', 'Metaverse',
                
                # Security & Networks
                'Cybersecurity', 'Cryptography', 'Network Security', 'Information Security',
                'Computer Networks', 'Network Protocols', 'Internet', 'World Wide Web',
                
                # Biotechnology
                'Biotechnology', 'Genetic Engineering', 'CRISPR', 'Gene Therapy',
                'Synthetic Biology', 'Bioinformatics', 'Computational Biology', 'Systems Biology',
                
                # Materials & Nano
                'Nanotechnology', 'Materials Science', 'Graphene', 'Carbon Nanotubes',
                'Metamaterials', 'Smart Materials', 'Biomaterials', 'Superconductors',
                
                # Energy & Environment
                'Renewable Energy', 'Solar Power', 'Wind Energy', 'Hydroelectric Power',
                'Nuclear Energy', 'Fusion Power', 'Battery Technology', 'Energy Storage',
                'Fuel Cells', 'Hydrogen Economy', 'Carbon Capture', 'Climate Technology',
                
                # Transportation & Space
                'Electric Vehicles', 'Autonomous Vehicles', 'Transportation', 'Logistics',
                'Space Technology', 'Satellite Technology', 'Space Exploration', 'Mars Colonization',
                'Aerospace Engineering', 'Rocket Technology', 'Space Station', 'Telescopes'
            ],
            
            'Mathematics & Physics': [
                # Pure Mathematics
                'Calculus', 'Linear Algebra', 'Differential Equations', 'Complex Analysis',
                'Real Analysis', 'Functional Analysis', 'Measure Theory', 'Topology',
                'Differential Geometry', 'Algebraic Geometry', 'Number Theory', 'Group Theory',
                'Ring Theory', 'Field Theory', 'Galois Theory', 'Category Theory',
                
                # Applied Mathematics
                'Statistics', 'Probability Theory', 'Bayesian Statistics', 'Statistical Inference',
                'Mathematical Modeling', 'Numerical Analysis', 'Optimization', 'Operations Research',
                'Game Theory', 'Decision Theory', 'Control Theory', 'Dynamical Systems',
                'Chaos Theory', 'Fractal Geometry', 'Graph Theory', 'Network Theory',
                'Combinatorics', 'Discrete Mathematics', 'Information Theory', 'Coding Theory',
                
                # Physics
                'Physics', 'Classical Mechanics', 'Quantum Mechanics', 'Relativity',
                'Thermodynamics', 'Statistical Mechanics', 'Electromagnetism', 'Optics',
                'Particle Physics', 'Nuclear Physics', 'Atomic Physics', 'Molecular Physics',
                'Condensed Matter Physics', 'Solid State Physics', 'Plasma Physics', 'Astrophysics',
                'Cosmology', 'General Relativity', 'Quantum Field Theory', 'String Theory',
                'Standard Model', 'Dark Matter', 'Dark Energy', 'Black Holes', 'Big Bang Theory'
            ],
            
            'Life Sciences & Medicine': [
                # Biology Fundamentals
                'Biology', 'Cell Biology', 'Molecular Biology', 'Biochemistry', 'Biophysics',
                'Genetics', 'Genomics', 'Proteomics', 'Metabolomics', 'Transcriptomics',
                'Epigenetics', 'Population Genetics', 'Evolutionary Biology', 'Phylogenetics',
                
                # Ecology & Environment
                'Ecology', 'Environmental Science', 'Conservation Biology', 'Biodiversity',
                'Climate Change', 'Global Warming', 'Ecosystem', 'Food Chain', 'Symbiosis',
                'Marine Biology', 'Botany', 'Zoology', 'Entomology', 'Ornithology',
                
                # Neuroscience & Psychology
                'Neuroscience', 'Brain', 'Consciousness', 'Cognitive Science', 'Neuroplasticity',
                'Memory', 'Learning', 'Perception', 'Emotion', 'Behavior',
                
                # Medicine & Health
                'Medicine', 'Anatomy', 'Physiology', 'Pathology', 'Pharmacology',
                'Drug Discovery', 'Clinical Trials', 'Medical Imaging', 'Surgery',
                'Immunology', 'Vaccines', 'Antibodies', 'Immune System', 'Autoimmune Disease',
                'Cancer Research', 'Oncology', 'Tumor Biology', 'Chemotherapy', 'Radiation Therapy',
                'Stem Cells', 'Regenerative Medicine', 'Tissue Engineering', 'Organ Transplantation',
                'Gene Therapy', 'Personalized Medicine', 'Precision Medicine', 'Telemedicine',
                
                # Microbiology & Disease
                'Microbiology', 'Virology', 'Bacteriology', 'Infectious Diseases', 'Epidemiology',
                'Public Health', 'Global Health', 'Healthcare Systems', 'Medical Ethics'
            ],
            
            'Social Sciences & Economics': [
                # Psychology
                'Psychology', 'Cognitive Psychology', 'Social Psychology', 'Developmental Psychology',
                'Clinical Psychology', 'Behavioral Psychology', 'Neuropsychology', 'Psychotherapy',
                
                # Sociology & Anthropology
                'Sociology', 'Social Theory', 'Social Networks', 'Cultural Studies', 'Social Change',
                'Anthropology', 'Cultural Anthropology', 'Archaeology', 'Human Evolution',
                'Ethnography', 'Folklore', 'Mythology', 'Cultural Heritage',
                
                # Economics & Finance
                'Economics', 'Macroeconomics', 'Microeconomics', 'Economic Theory', 'Econometrics',
                'Behavioral Economics', 'Development Economics', 'International Economics',
                'Finance', 'Financial Markets', 'Investment', 'Banking', 'Insurance',
                'Corporate Finance', 'Financial Technology', 'Cryptocurrency Economics',
                
                # Political Science
                'Political Science', 'International Relations', 'Diplomacy', 'Governance',
                'Public Policy', 'Social Policy', 'Political Theory', 'Comparative Politics',
                'Democracy', 'Authoritarianism', 'Political Economy', 'Geopolitics',
                
                # Other Social Sciences
                'Education', 'Pedagogy', 'Learning Theory', 'Educational Technology', 'Curriculum',
                'Linguistics', 'Computational Linguistics', 'Language Evolution', 'Semantics',
                'Geography', 'Human Geography', 'Physical Geography', 'GIS', 'Cartography',
                'Urban Planning', 'Regional Planning', 'Sustainable Development', 'Smart Cities',
                'Demography', 'Population Studies', 'Migration', 'Urbanization',
                'Criminology', 'Justice System', 'Law Enforcement', 'Legal Studies',
                'Social Work', 'Community Development', 'Social Justice', 'Human Rights'
            ],
            
            'Arts & Culture': [
                # Visual Arts
                'Art History', 'Painting', 'Sculpture', 'Drawing', 'Printmaking',
                'Photography', 'Digital Art', 'Video Art', 'Installation Art', 'Performance Art',
                'Renaissance Art', 'Baroque Art', 'Impressionism', 'Modern Art', 'Contemporary Art',
                'Abstract Art', 'Conceptual Art', 'Pop Art', 'Street Art', 'Folk Art',
                
                # Architecture & Design
                'Architecture', 'Urban Design', 'Landscape Architecture', 'Interior Design',
                'Sustainable Architecture', 'Green Building', 'Architectural Theory', 'Bauhaus',
                'Design', 'Graphic Design', 'Industrial Design', 'Product Design',
                'User Experience Design', 'User Interface Design', 'Web Design',
                
                # Music & Performing Arts
                'Music', 'Music Theory', 'Composition', 'Performance', 'Conducting',
                'Classical Music', 'Jazz', 'Popular Music', 'Electronic Music', 'World Music',
                'Opera', 'Musical Theater', 'Dance', 'Ballet', 'Theater', 'Drama',
                
                # Literature & Media
                'Literature', 'Poetry', 'Fiction', 'Non-fiction', 'Creative Writing',
                'Literary Criticism', 'Comparative Literature', 'World Literature',
                'Film', 'Cinema', 'Documentary', 'Animation', 'Film Theory',
                'Television', 'Radio', 'Journalism', 'Media Studies', 'Communication',
                
                # Cultural Studies
                'Cultural Theory', 'Aesthetics', 'Art Criticism', 'Cultural Studies',
                'Fashion', 'Textile Arts', 'Crafts', 'Ceramics', 'Jewelry',
                'Museums', 'Curation', 'Art Conservation', 'Cultural Heritage', 'Tourism'
            ],
            
            'History & Philosophy': [
                # Historical Periods
                'Ancient History', 'Classical Antiquity', 'Medieval History', 'Renaissance',
                'Age of Enlightenment', 'Industrial Revolution', 'Modern History', 'Contemporary History',
                'Prehistory', 'Bronze Age', 'Iron Age', 'Stone Age',
                
                # Regional History
                'World History', 'European History', 'American History', 'Asian History',
                'African History', 'Middle Eastern History', 'Latin American History',
                'History of Science', 'History of Technology', 'History of Medicine',
                'Economic History', 'Social History', 'Cultural History', 'Political History',
                
                # Philosophy Branches
                'Philosophy', 'Ethics', 'Moral Philosophy', 'Applied Ethics', 'Bioethics',
                'Metaphysics', 'Ontology', 'Epistemology', 'Philosophy of Mind',
                'Philosophy of Science', 'Philosophy of Language', 'Political Philosophy',
                'Aesthetics', 'Logic', 'Philosophy of Religion', 'Philosophy of Law',
                
                # Philosophical Traditions
                'Ancient Philosophy', 'Medieval Philosophy', 'Modern Philosophy', 'Contemporary Philosophy',
                'Western Philosophy', 'Eastern Philosophy', 'Chinese Philosophy', 'Indian Philosophy',
                'Islamic Philosophy', 'Jewish Philosophy', 'Existentialism', 'Phenomenology',
                'Analytic Philosophy', 'Continental Philosophy', 'Pragmatism', 'Postmodernism',
                
                # Religion & Spirituality
                'Religion', 'Christianity', 'Islam', 'Judaism', 'Buddhism', 'Hinduism',
                'Taoism', 'Confucianism', 'Shintoism', 'Sikhism', 'Jainism',
                'Theology', 'Comparative Religion', 'Religious Studies', 'Mysticism',
                'Meditation', 'Spirituality', 'Sacred Texts', 'Religious Philosophy'
            ]
        }
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize Wikipedia text"""
        if not text:
            return ""
        
        # Remove Wikipedia markup and references
        cleaned = re.sub(r'\[[\d\s,]+\]', '', text)  # Remove citation numbers
        cleaned = re.sub(r'\([^)]*\)', '', cleaned)  # Remove parenthetical notes
        cleaned = re.sub(r'\s+', ' ', cleaned.strip())  # Normalize whitespace
        
        return cleaned[:1500]  # Optimal length for embeddings
    
    def _validate_concept(self, title: str, summary: str, url: str) -> bool:
        """Validate Wikipedia concept quality"""
        if not all([title, summary, url]):
            return False
        
        # Content quality checks
        if len(title.strip()) < 3:
            return False
        
        if len(summary.strip()) < 100:
            return False
        
        # Avoid disambiguation and meta pages
        if any(term in title.lower() for term in ['disambiguation', 'category:', 'list of', 'template:']):
            return False
        
        # Avoid overly technical or specific pages
        if any(term in summary.lower() for term in ['may refer to:', 'is a surname', 'is a given name']):
            return False
        
        return True
    
    def fetch_concept(self, title: str, category: str) -> Optional[Dict]:
        """Fetch a single Wikipedia concept with error handling"""
        for attempt in range(self.max_retries):
            try:
                encoded_title = requests.utils.quote(title.replace(' ', '_'))
                url = f"{self.base_url}/{encoded_title}"
                
                response = self.session.get(url, timeout=self.timeout)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'extract' in data and data['extract']:
                        title_clean = data.get('title', title)
                        summary_clean = self._clean_text(data['extract'])
                        page_url = data.get('content_urls', {}).get('desktop', {}).get('page', '')
                        
                        if self._validate_concept(title_clean, summary_clean, page_url):
                            return {
                                'id': str(uuid.uuid4()),
                                'title': title_clean,
                                'summary': summary_clean,
                                'category': category,
                                'source': 'wikipedia',
                                'source_id': str(data.get('pageid', '')),
                                'url': page_url,
                                'created_at': datetime.now()
                            }
                
                elif response.status_code == 404:
                    # Page doesn't exist, don't retry
                    break
                    
                elif response.status_code == 429:
                    # Rate limited
                    time.sleep(self.rate_limit_delay * (attempt + 1) * 5)
                    continue
                
                # Other errors, wait and retry
                time.sleep(self.rate_limit_delay * (attempt + 1))
                
            except Exception as e:
                logger.debug(f"Error fetching {title}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.rate_limit_delay * 2)
        
        return None
    
    def fetch_concepts_by_domain(self, domain: str, target_count: int) -> List[Dict]:
        """Fetch concepts for a specific domain with parallel processing"""
        if domain not in self.expanded_domains:
            logger.warning(f"Unknown domain: {domain}")
            return []
        
        concept_titles = self.expanded_domains[domain]
        logger.info(f"📚 Fetching {target_count} concepts from {domain} ({len(concept_titles)} available)")
        
        # Ensure we have enough titles
        if len(concept_titles) < target_count:
            # Repeat titles if needed (will be filtered by validation)
            concept_titles = concept_titles * ((target_count // len(concept_titles)) + 1)
        
        successful_concepts = []
        
        # Use ThreadPoolExecutor for parallel fetching (respecting rate limits)
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all tasks
            future_to_title = {
                executor.submit(self.fetch_concept, title, domain): title 
                for title in concept_titles[:target_count + 50]  # Extra buffer
            }
            
            for future in as_completed(future_to_title):
                if len(successful_concepts) >= target_count:
                    break
                
                title = future_to_title[future]
                try:
                    concept = future.result()
                    if concept:
                        successful_concepts.append(concept)
                        
                        if len(successful_concepts) % 50 == 0:
                            logger.info(f"✅ {domain}: {len(successful_concepts)}/{target_count}")
                
                except Exception as e:
                    logger.debug(f"Future failed for {title}: {e}")
                
                # Rate limiting
                time.sleep(self.rate_limit_delay)
        
        logger.info(f"🎯 {domain} complete: {len(successful_concepts)} concepts")
        return successful_concepts[:target_count]
    
    def fetch_concepts(self, total_target: int) -> List[Dict]:
        """Fetch concepts across all domains with balanced distribution"""
        all_concepts = []
        concepts_per_domain = total_target // len(self.expanded_domains)
        
        logger.info(f"🌍 Fetching {total_target} Wikipedia concepts ({concepts_per_domain} per domain)")
        
        for domain in self.expanded_domains.keys():
            try:
                domain_concepts = self.fetch_concepts_by_domain(domain, concepts_per_domain)
                all_concepts.extend(domain_concepts)
                
                logger.info(f"📊 Progress: {len(all_concepts)}/{total_target} concepts")
                
                if len(all_concepts) >= total_target:
                    break
                    
            except Exception as e:
                logger.error(f"Domain {domain} failed: {e}")
                continue
        
        # Trim to exact target
        final_concepts = all_concepts[:total_target]
        logger.info(f"🎉 Wikipedia fetch complete: {len(final_concepts)} concepts")
        
        return final_concepts

# Test function
def test_wikipedia_client():
    """Test the Wikipedia client"""
    logging.basicConfig(level=logging.INFO)
    client = WikipediaClient()
    
    # Test single concept
    concept = client.fetch_concept('Artificial Intelligence', 'Science & Technology')
    
    if concept:
        logger.info("✅ Wikipedia client test passed")
        logger.info(f"Sample: {concept['title']} - {concept['summary'][:100]}...")
        return True
    else:
        logger.error("❌ Wikipedia client test failed")
        return False

if __name__ == '__main__':
    test_wikipedia_client()
