#!/usr/bin/env python3
"""
Call the admin API to generate edges via web interface
"""

import requests
import json
import time

def generate_edges_via_api():
    """Generate edges using the admin API"""
    print("🚀 LYNX Edge Generation via Admin API")
    print("🔗 Calling the admin endpoint to generate semantic connections...")
    
    try:
        # Call the admin API
        url = "http://localhost:3000/api/admin/generate-edges"
        params = {
            'clear': 'true',        # Clear existing edges
            'threshold': '0.6',     # Minimum similarity threshold
            'maxEdges': '12'        # Max edges per node (k=12)
        }
        
        print("📡 Sending request to generate edges...")
        start_time = time.time()
        
        response = requests.post(url, params=params, timeout=300)  # 5 minute timeout
        
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print("🎉 Edge generation successful!")
            print("📊 Results:")
            
            stats = result.get('statistics', {})
            print(f"   • Total concepts: {stats.get('totalConcepts', 'N/A')}")
            print(f"   • Total edges: {stats.get('totalEdges', 'N/A')}")
            print(f"   • Average edges per concept: {stats.get('averageEdgesPerConcept', 'N/A'):.1f}")
            print(f"   • Weight range: {stats.get('weightRange', {}).get('min', 'N/A'):.3f} - {stats.get('weightRange', {}).get('max', 'N/A'):.3f}")
            print(f"   • Average weight: {stats.get('averageWeight', 'N/A'):.3f}")
            print(f"   • Similarity threshold: {stats.get('threshold', 'N/A')}")
            print(f"   • Processing time: {elapsed_time:.1f} seconds")
            
            print("\n✅ Semantic connections have been generated!")
            print("🌌 Your galaxy now has intelligent edge connections")
            print("🔄 Refresh your browser to see the new connections")
            print("⚙️ Use the settings panel (bottom-left) to control connection visibility")
            
        else:
            print(f"❌ Edge generation failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out - edge generation may still be running")
        print("💡 Check the server logs or try again in a few minutes")
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == '__main__':
    generate_edges_via_api()
