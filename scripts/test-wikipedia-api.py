#!/usr/bin/env python3
"""
Test Wikipedia API with improved error handling
"""

import requests
import requests.utils
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_wikipedia_api():
    """Test Wikipedia API with different methods"""
    
    test_concepts = [
        'Artificial Intelligence',
        'Machine Learning', 
        'Quantum Computing',
        'Black Hole',
        'Leonardo da Vinci'
    ]
    
    headers = {
        'User-Agent': 'LYNX Knowledge Explorer/1.0 (https://github.com/user/lynx; contact@example.com)',
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip, deflate'
    }
    
    successful = 0
    
    for concept_title in test_concepts:
        logger.info(f"🧪 Testing: {concept_title}")
        
        try:
            # Method 1: REST API
            encoded_title = requests.utils.quote(concept_title.replace(' ', '_'))
            search_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"
            
            response = requests.get(search_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if 'extract' in data:
                    logger.info(f"✅ REST API success: {data['title']}")
                    logger.info(f"   Summary: {data['extract'][:100]}...")
                    successful += 1
                    time.sleep(1)
                    continue
            
            logger.warning(f"⚠️ REST API failed ({response.status_code}), trying fallback...")
            
            # Method 2: Traditional API
            fallback_url = f"https://en.wikipedia.org/w/api.php?action=query&format=json&titles={encoded_title}&prop=extracts&exintro=true&explaintext=true&exsectionformat=plain"
            fallback_response = requests.get(fallback_url, headers=headers, timeout=15)
            
            if fallback_response.status_code == 200:
                fallback_data = fallback_response.json()
                pages = fallback_data.get('query', {}).get('pages', {})
                
                for page_id, page_data in pages.items():
                    if page_id != '-1' and 'extract' in page_data:
                        logger.info(f"✅ Fallback API success: {page_data['title']}")
                        logger.info(f"   Summary: {page_data['extract'][:100]}...")
                        successful += 1
                        break
                else:
                    logger.error(f"❌ Both methods failed for: {concept_title}")
            else:
                logger.error(f"❌ Fallback API also failed ({fallback_response.status_code})")
                
        except Exception as e:
            logger.error(f"❌ Exception for {concept_title}: {e}")
        
        time.sleep(1)
    
    logger.info(f"🎯 Test Results: {successful}/{len(test_concepts)} successful")
    
    if successful >= 3:
        logger.info("✅ Wikipedia API is working! Ready for full ingestion.")
        return True
    else:
        logger.error("❌ Wikipedia API issues persist. Check network/firewall.")
        return False

if __name__ == '__main__':
    test_wikipedia_api()
