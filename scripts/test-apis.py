#!/usr/bin/env python3
"""
Test the APIs to see what data is being returned
"""

import requests
import json

def test_api(endpoint, name):
    """Test an API endpoint"""
    try:
        print(f"\n🧪 Testing {name}: {endpoint}")
        response = requests.get(f"http://localhost:3000{endpoint}")
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                print(f"✅ Success: {len(data)} items")
                if data:
                    print(f"📄 Sample item: {json.dumps(data[0], indent=2)[:200]}...")
            else:
                print(f"✅ Success: {json.dumps(data, indent=2)[:200]}...")
        else:
            print(f"❌ Error {response.status_code}: {response.text[:200]}")
            
    except Exception as e:
        print(f"💥 Exception: {e}")

if __name__ == '__main__':
    print("🔍 Testing LYNX APIs...")
    
    # Test all APIs
    test_api("/api/concepts", "Concepts API")
    test_api("/api/positions", "Positions API") 
    test_api("/api/edges", "Edges API")
    test_api("/api/ingestion/status", "Status API")
    
    print("\n🎯 API testing complete!")
