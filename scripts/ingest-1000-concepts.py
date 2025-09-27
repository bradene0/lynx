#!/usr/bin/env python3
"""
LYNX Large-Scale Ingestion Pipeline
Ingest 1000 diverse concepts from Wikipedia + arXiv papers
"""

import os
import sys
import asyncio
import logging
import requests
import requests.utils
import time
import json
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict, Tuple
import uuid
from datetime import datetime
import xml.etree.ElementTree as ET

# Load environment variables
load_dotenv()

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from scripts.ingestion.database import DatabaseManager
from scripts.ingestion.embeddings import EmbeddingGenerator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LargeScaleIngestion:
    def __init__(self):
        self.db = DatabaseManager()
        self.embedder = EmbeddingGenerator()
        
        # Diverse knowledge domains with curated concepts
        self.knowledge_domains = {
            'Science & Technology': [
                'Artificial Intelligence', 'Quantum Computing', 'CRISPR', 'Nanotechnology',
                'Blockchain', 'Machine Learning', 'Robotics', 'Biotechnology', 'Cybersecurity',
                'Internet of Things', 'Virtual Reality', 'Augmented Reality', 'Cloud Computing',
                'Big Data', 'Neural Networks', 'Computer Vision', 'Natural Language Processing',
                'Genetic Engineering', 'Renewable Energy', 'Solar Power', 'Wind Energy',
                'Nuclear Energy', 'Fusion Power', 'Battery Technology', 'Electric Vehicles',
                'Autonomous Vehicles', 'Drone Technology', 'Space Technology', 'Satellite Technology',
                'GPS Technology', 'Fiber Optics', 'Laser Technology', 'Semiconductor',
                'Microprocessor', 'Quantum Physics', 'Particle Physics', 'String Theory',
                'Relativity', 'Thermodynamics', 'Electromagnetism', 'Optics', 'Acoustics',
                'Materials Science', 'Polymer Science', 'Crystallography', 'Metallurgy',
                'Chemical Engineering', 'Biochemistry', 'Molecular Biology', 'Genetics',
                'Immunology', 'Neuroscience', 'Pharmacology', 'Medical Imaging'
            ],
            'Mathematics & Logic': [
                'Calculus', 'Linear Algebra', 'Statistics', 'Probability Theory', 'Game Theory',
                'Number Theory', 'Topology', 'Geometry', 'Algebra', 'Discrete Mathematics',
                'Graph Theory', 'Combinatorics', 'Set Theory', 'Logic', 'Proof Theory',
                'Category Theory', 'Differential Equations', 'Complex Analysis', 'Real Analysis',
                'Functional Analysis', 'Measure Theory', 'Optimization', 'Operations Research',
                'Cryptography', 'Information Theory', 'Coding Theory', 'Computational Complexity',
                'Algorithm', 'Data Structure', 'Sorting Algorithm', 'Search Algorithm',
                'Dynamic Programming', 'Greedy Algorithm', 'Divide and Conquer', 'Recursion',
                'Mathematical Modeling', 'Numerical Analysis', 'Monte Carlo Method', 'Simulation',
                'Chaos Theory', 'Fractal', 'Knot Theory', 'Group Theory', 'Ring Theory',
                'Field Theory', 'Galois Theory', 'Algebraic Geometry', 'Differential Geometry'
            ],
            'History & Culture': [
                'Ancient Egypt', 'Roman Empire', 'Byzantine Empire', 'Medieval Europe',
                'Renaissance', 'Industrial Revolution', 'World War I', 'World War II',
                'Cold War', 'American Revolution', 'French Revolution', 'Russian Revolution',
                'Chinese Dynasty', 'Japanese History', 'Islamic Golden Age', 'Mongol Empire',
                'Ottoman Empire', 'British Empire', 'Spanish Empire', 'Portuguese Empire',
                'Colonialism', 'Imperialism', 'Decolonization', 'Civil Rights Movement',
                'Feminism', 'Abolition of Slavery', 'Democracy', 'Monarchy', 'Republic',
                'Feudalism', 'Capitalism', 'Socialism', 'Communism', 'Fascism', 'Nationalism',
                'Globalization', 'Cultural Revolution', 'Enlightenment', 'Scientific Revolution',
                'Protestant Reformation', 'Counter-Reformation', 'Crusades', 'Viking Age',
                'Stone Age', 'Bronze Age', 'Iron Age', 'Neolithic Revolution', 'Agriculture',
                'Urbanization', 'Trade Route', 'Silk Road', 'Maritime Trade'
            ],
            'Arts & Literature': [
                'Leonardo da Vinci', 'Michelangelo', 'Pablo Picasso', 'Vincent van Gogh',
                'Claude Monet', 'Salvador Dalí', 'Frida Kahlo', 'Andy Warhol', 'Jackson Pollock',
                'Impressionism', 'Cubism', 'Surrealism', 'Abstract Expressionism', 'Pop Art',
                'Baroque', 'Renaissance Art', 'Gothic Art', 'Romanticism', 'Realism',
                'Modernism', 'Postmodernism', 'Contemporary Art', 'Digital Art', 'Photography',
                'Cinema', 'Film Theory', 'Documentary', 'Animation', 'Special Effects',
                'Music Theory', 'Classical Music', 'Jazz', 'Rock Music', 'Electronic Music',
                'Opera', 'Symphony', 'Chamber Music', 'Folk Music', 'World Music',
                'Literature', 'Poetry', 'Novel', 'Drama', 'Epic', 'Mythology',
                'Shakespeare', 'Homer', 'Dante', 'Cervantes', 'Tolstoy', 'Joyce',
                'Kafka', 'Orwell', 'Hemingway', 'García Márquez', 'Toni Morrison',
                'Architecture', 'Gothic Architecture', 'Modern Architecture', 'Bauhaus',
                'Frank Lloyd Wright', 'Le Corbusier', 'Zaha Hadid', 'Sustainable Architecture'
            ],
            'Philosophy & Religion': [
                'Aristotle', 'Plato', 'Socrates', 'Immanuel Kant', 'Friedrich Nietzsche',
                'René Descartes', 'John Locke', 'David Hume', 'Jean-Jacques Rousseau',
                'Georg Wilhelm Friedrich Hegel', 'Karl Marx', 'Søren Kierkegaard',
                'Martin Heidegger', 'Jean-Paul Sartre', 'Simone de Beauvoir', 'Michel Foucault',
                'Ethics', 'Metaphysics', 'Epistemology', 'Logic', 'Aesthetics', 'Political Philosophy',
                'Philosophy of Mind', 'Philosophy of Science', 'Philosophy of Language',
                'Existentialism', 'Phenomenology', 'Pragmatism', 'Analytic Philosophy',
                'Continental Philosophy', 'Stoicism', 'Epicureanism', 'Skepticism', 'Empiricism',
                'Rationalism', 'Idealism', 'Materialism', 'Dualism', 'Monism', 'Determinism',
                'Free Will', 'Consciousness', 'Personal Identity', 'Moral Philosophy',
                'Christianity', 'Islam', 'Judaism', 'Buddhism', 'Hinduism', 'Taoism',
                'Confucianism', 'Shintoism', 'Sikhism', 'Jainism', 'Zoroastrianism',
                'Theology', 'Comparative Religion', 'Religious Studies', 'Mysticism', 'Meditation'
            ],
            'Social Sciences': [
                'Psychology', 'Sociology', 'Anthropology', 'Political Science', 'Economics',
                'Linguistics', 'Archaeology', 'Geography', 'Demography', 'Criminology',
                'International Relations', 'Public Policy', 'Urban Planning', 'Social Work',
                'Education', 'Pedagogy', 'Developmental Psychology', 'Cognitive Psychology',
                'Social Psychology', 'Behavioral Economics', 'Macroeconomics', 'Microeconomics',
                'Game Theory', 'Market Economy', 'Planned Economy', 'Mixed Economy',
                'Supply and Demand', 'Inflation', 'Unemployment', 'Economic Growth',
                'Globalization', 'International Trade', 'Monetary Policy', 'Fiscal Policy',
                'Social Structure', 'Social Class', 'Social Mobility', 'Social Change',
                'Culture', 'Subculture', 'Ethnicity', 'Race', 'Gender Studies', 'Feminism',
                'Human Rights', 'Social Justice', 'Inequality', 'Poverty', 'Welfare State',
                'Democracy', 'Authoritarianism', 'Totalitarianism', 'Political Party',
                'Electoral System', 'Governance', 'Public Administration', 'Bureaucracy'
            ],
            'Life Sciences': [
                'Evolution', 'Natural Selection', 'Genetics', 'DNA', 'RNA', 'Protein',
                'Cell Biology', 'Molecular Biology', 'Biochemistry', 'Microbiology',
                'Virology', 'Bacteriology', 'Immunology', 'Pharmacology', 'Toxicology',
                'Ecology', 'Biodiversity', 'Conservation Biology', 'Environmental Science',
                'Climate Change', 'Ecosystem', 'Food Chain', 'Symbiosis', 'Adaptation',
                'Speciation', 'Extinction', 'Fossil', 'Paleontology', 'Taxonomy',
                'Botany', 'Zoology', 'Entomology', 'Ornithology', 'Marine Biology',
                'Anatomy', 'Physiology', 'Neuroscience', 'Endocrinology', 'Cardiology',
                'Oncology', 'Pathology', 'Epidemiology', 'Public Health', 'Medicine',
                'Surgery', 'Anesthesia', 'Radiology', 'Psychiatry', 'Pediatrics',
                'Geriatrics', 'Reproductive Biology', 'Developmental Biology', 'Stem Cell',
                'Gene Therapy', 'Personalized Medicine', 'Bioinformatics', 'Genomics',
                'Proteomics', 'Metabolomics', 'Systems Biology', 'Synthetic Biology'
            ],
            'Physical Sciences': [
                'Physics', 'Chemistry', 'Astronomy', 'Astrophysics', 'Cosmology',
                'Quantum Mechanics', 'Relativity', 'Thermodynamics', 'Electromagnetism',
                'Optics', 'Mechanics', 'Fluid Dynamics', 'Solid State Physics',
                'Particle Physics', 'Nuclear Physics', 'Atomic Physics', 'Plasma Physics',
                'Condensed Matter Physics', 'Statistical Mechanics', 'Quantum Field Theory',
                'Organic Chemistry', 'Inorganic Chemistry', 'Physical Chemistry', 'Analytical Chemistry',
                'Polymer Chemistry', 'Catalysis', 'Electrochemistry', 'Photochemistry',
                'Spectroscopy', 'Crystallography', 'Materials Science', 'Nanotechnology',
                'Solar System', 'Galaxy', 'Black Hole', 'Neutron Star', 'Supernova',
                'Big Bang', 'Dark Matter', 'Dark Energy', 'Exoplanet', 'Astrobiology',
                'Space Exploration', 'Telescope', 'Satellite', 'Space Station', 'Mars Exploration',
                'Meteorology', 'Climate Science', 'Atmospheric Science', 'Oceanography',
                'Geology', 'Seismology', 'Volcanology', 'Mineralogy', 'Petrology'
            ]
        }
        
        # arXiv categories for academic papers
        self.arxiv_categories = {
            'cs.AI': 'Artificial Intelligence',
            'cs.LG': 'Machine Learning', 
            'cs.CV': 'Computer Vision',
            'cs.CL': 'Computational Linguistics',
            'cs.RO': 'Robotics',
            'cs.CR': 'Cryptography and Security',
            'physics.gen-ph': 'General Physics',
            'quant-ph': 'Quantum Physics',
            'astro-ph': 'Astrophysics',
            'cond-mat': 'Condensed Matter',
            'math.CO': 'Combinatorics',
            'math.NT': 'Number Theory',
            'math.AG': 'Algebraic Geometry',
            'q-bio.BM': 'Biomolecules',
            'q-bio.GN': 'Genomics',
            'q-bio.NC': 'Neurons and Cognition',
            'econ.TH': 'Theoretical Economics',
            'stat.ML': 'Machine Learning Statistics'
        }

    async def get_wikipedia_concepts(self, limit: int = 800) -> List[Dict]:
        """Get diverse Wikipedia concepts across all domains"""
        logger.info(f"🌍 Fetching {limit} Wikipedia concepts across all domains...")
        
        all_concepts = []
        concepts_per_domain = limit // len(self.knowledge_domains)
        
        for domain, concept_list in self.knowledge_domains.items():
            logger.info(f"📚 Processing domain: {domain}")
            
            # Take concepts from this domain
            domain_concepts = concept_list[:concepts_per_domain]
            
            for concept_title in domain_concepts:
                try:
                    # Wikipedia API call with proper headers and encoding
                    encoded_title = requests.utils.quote(concept_title.replace(' ', '_'))
                    search_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"
                    
                    headers = {
                        'User-Agent': 'LYNX Knowledge Explorer/1.0 (https://github.com/user/lynx; contact@example.com)',
                        'Accept': 'application/json',
                        'Accept-Encoding': 'gzip, deflate'
                    }
                    
                    response = requests.get(search_url, headers=headers, timeout=15)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if 'extract' in data and len(data['extract']) > 100:
                            concept = {
                                'id': str(uuid.uuid4()),
                                'title': data['title'],
                                'summary': data['extract'][:2000],  # Limit summary length
                                'category': domain,
                                'source': 'wikipedia',
                                'source_id': '',
                                'url': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                                'created_at': datetime.now()
                            }
                            all_concepts.append(concept)
                            logger.info(f"✅ Added: {concept['title']}")
                        else:
                            logger.warning(f"⚠️ Insufficient content for: {concept_title}")
                    else:
                        logger.warning(f"⚠️ Wikipedia API error for {concept_title}: {response.status_code}")
                        
                except requests.exceptions.RequestException as e:
                    logger.warning(f"🔄 Request failed for {concept_title}, trying alternative method: {e}")
                    
                    # Try the old Wikipedia API as fallback
                    try:
                        fallback_url = f"https://en.wikipedia.org/w/api.php?action=query&format=json&titles={encoded_title}&prop=extracts&exintro=true&explaintext=true&exsectionformat=plain"
                        fallback_response = requests.get(fallback_url, headers=headers, timeout=15)
                        
                        if fallback_response.status_code == 200:
                            fallback_data = fallback_response.json()
                            pages = fallback_data.get('query', {}).get('pages', {})
                            
                            for page_id, page_data in pages.items():
                                if page_id != '-1' and 'extract' in page_data:
                                    concept = {
                                        'id': str(uuid.uuid4()),
                                        'title': page_data['title'],
                                        'summary': page_data['extract'][:2000],
                                        'category': domain,
                                        'source': 'wikipedia',
                                        'source_id': '',
                                        'url': f"https://en.wikipedia.org/wiki/{encoded_title}",
                                        'created_at': datetime.now()
                                    }
                                    all_concepts.append(concept)
                                    logger.info(f"✅ Added (fallback): {concept['title']}")
                                    break
                    except Exception as fallback_error:
                        logger.error(f"❌ Both methods failed for {concept_title}: {fallback_error}")
                
                # More conservative rate limiting - 1 request per second
                time.sleep(1.0)
                
                if len(all_concepts) >= limit:
                    break
            
            if len(all_concepts) >= limit:
                break
        
        logger.info(f"🎯 Successfully fetched {len(all_concepts)} Wikipedia concepts")
        return all_concepts[:limit]

    async def get_arxiv_papers(self, limit: int = 200) -> List[Dict]:
        """Get recent arXiv papers for academic depth"""
        logger.info(f"📄 Fetching {limit} arXiv papers...")
        
        papers = []
        papers_per_category = limit // len(self.arxiv_categories)
        
        for category, category_name in self.arxiv_categories.items():
            try:
                # arXiv API query
                query_url = f"http://export.arxiv.org/api/query?search_query=cat:{category}&start=0&max_results={papers_per_category}&sortBy=submittedDate&sortOrder=descending"
                response = requests.get(query_url, timeout=15)
                
                if response.status_code == 200:
                    # Parse XML response
                    root = ET.fromstring(response.content)
                    
                    for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                        title_elem = entry.find('{http://www.w3.org/2005/Atom}title')
                        summary_elem = entry.find('{http://www.w3.org/2005/Atom}summary')
                        id_elem = entry.find('{http://www.w3.org/2005/Atom}id')
                        
                        if title_elem is not None and summary_elem is not None:
                            # Clean up title and summary
                            title = title_elem.text.strip().replace('\n', ' ')
                            summary = summary_elem.text.strip().replace('\n', ' ')[:2000]
                            arxiv_id = id_elem.text.split('/')[-1] if id_elem is not None else ''
                            
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
                            logger.info(f"✅ Added arXiv: {title[:50]}...")
                
                # Rate limiting for arXiv
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Error fetching arXiv category {category}: {e}")
        
        logger.info(f"🎯 Successfully fetched {len(papers)} arXiv papers")
        return papers

    async def generate_positions(self, concepts: List[Dict]) -> List[Dict]:
        """Generate 3D positions using improved distribution"""
        logger.info("🌌 Generating 3D galaxy positions...")
        
        positions = []
        
        # Create domain-based clustering
        domain_centers = {
            'Science & Technology': (0, 0, 0),
            'Mathematics & Logic': (100, 0, 0),
            'History & Culture': (-100, 0, 0),
            'Arts & Literature': (0, 100, 0),
            'Philosophy & Religion': (0, -100, 0),
            'Social Sciences': (50, 50, 0),
            'Life Sciences': (-50, 50, 0),
            'Physical Sciences': (0, 0, 100),
            'Academic - Artificial Intelligence': (150, 0, 0),
            'Academic - Machine Learning': (140, 10, 0),
            'Academic - Computer Vision': (130, 20, 0),
            'Academic - Computational Linguistics': (120, 30, 0),
            'Academic - Robotics': (110, 40, 0),
            'Academic - Cryptography and Security': (100, 50, 0),
            'Academic - General Physics': (0, 0, 120),
            'Academic - Quantum Physics': (10, 0, 110),
            'Academic - Astrophysics': (20, 0, 100),
            'Academic - Condensed Matter': (30, 0, 90),
        }
        
        for concept in concepts:
            category = concept['category']
            
            # Get domain center or use default
            center = domain_centers.get(category, (0, 0, 0))
            
            # Add random variation around center
            import random
            x = center[0] + random.uniform(-30, 30)
            y = center[1] + random.uniform(-30, 30) 
            z = center[2] + random.uniform(-30, 30)
            
            position = {
                'concept_id': concept['id'],
                'x': x,
                'y': y,
                'z': z,
                'cluster_id': category.replace(' ', '_').lower()
            }
            positions.append(position)
        
        logger.info(f"✅ Generated {len(positions)} positions")
        return positions

    async def run_large_scale_ingestion(self):
        """Main pipeline for 1000 concept ingestion"""
        logger.info("🚀 Starting LYNX Large-Scale Ingestion Pipeline...")
        logger.info("🎯 Target: 1000 concepts (800 Wikipedia + 200 arXiv)")
        
        try:
            # Step 1: Fetch Wikipedia concepts
            wikipedia_concepts = await self.get_wikipedia_concepts(800)
            
            # Step 2: Fetch arXiv papers  
            arxiv_papers = await self.get_arxiv_papers(200)
            
            # Combine all concepts
            all_concepts = wikipedia_concepts + arxiv_papers
            logger.info(f"📊 Total concepts collected: {len(all_concepts)}")
            
            # Step 3: Store concepts in database
            logger.info("💾 Storing concepts in database...")
            stored_count = await self.db.insert_concepts(all_concepts)
            logger.info(f"✅ Stored {stored_count} concepts")
            
            # Step 4: Generate embeddings
            logger.info("🧠 Generating SBERT embeddings...")
            embeddings = []
            
            for i, concept in enumerate(all_concepts):
                try:
                    # Create text for embedding (title + summary)
                    text = f"{concept['title']}. {concept['summary']}"
                    embedding_vector = self.embedder.generate_embedding(text)
                    
                    embedding = {
                        'id': str(uuid.uuid4()),
                        'concept_id': concept['id'],
                        'embedding': embedding_vector.tolist(),  # Convert numpy array to list
                        'model': 'all-MiniLM-L6-v2',
                        'created_at': datetime.now()
                    }
                    embeddings.append(embedding)
                    
                    if (i + 1) % 50 == 0:
                        logger.info(f"🧠 Generated embeddings: {i + 1}/{len(all_concepts)}")
                        
                except Exception as e:
                    logger.error(f"❌ Error generating embedding for {concept['title']}: {e}")
            
            # Store embeddings
            embedding_count = await self.db.insert_embeddings(embeddings)
            logger.info(f"✅ Stored {embedding_count} embeddings")
            
            # Step 5: Generate positions
            positions = await self.generate_positions(all_concepts)
            position_count = await self.db.insert_positions(positions)
            logger.info(f"✅ Stored {position_count} positions")
            
            # Step 6: Generate similarity edges (this will take time!)
            logger.info("🔗 Generating similarity edges...")
            # Skip edge building for now - we can run it separately
            logger.info("⏭️ Skipping edge generation for initial ingestion")
            logger.info("💡 Run 'python scripts/build-similarity-edges.py' after ingestion completes")
            
            logger.info("🎉 LYNX Large-Scale Ingestion Complete!")
            logger.info(f"📊 Final Stats:")
            logger.info(f"   • Concepts: {stored_count}")
            logger.info(f"   • Embeddings: {embedding_count}")
            logger.info(f"   • Positions: {position_count}")
            logger.info(f"   • Knowledge Domains: {len(self.knowledge_domains)}")
            logger.info(f"   • Academic Papers: {len(arxiv_papers)}")
            
        except Exception as e:
            logger.error(f"💥 Pipeline failed: {e}")
            raise

async def main():
    ingestion = LargeScaleIngestion()
    await ingestion.run_large_scale_ingestion()

if __name__ == '__main__':
    asyncio.run(main())
