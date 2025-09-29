#!/usr/bin/env python3
"""
Call the admin API to regenerate positions
This uses your running web app's new admin endpoint
"""

import requests
import json
import time

def main():
    print("🚀 LYNX Position Regeneration via Admin API")
    print("🌌 Calling the admin endpoint to fix position distribution...")
    
    # Your web app URL
    base_url = "http://localhost:3000"
    admin_endpoint = f"{base_url}/api/admin/regenerate-positions"
    
    # Admin key for security
    headers = {
        'Content-Type': 'application/json',
        'x-admin-key': 'lynx-admin-2024'  # Simple admin key
    }
    
    try:
        print("📡 Sending request to regenerate positions...")
        
        response = requests.post(admin_endpoint, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print("🎉 Position regeneration successful!")
            print(f"📊 Results:")
            
            if 'summary' in result:
                summary = result['summary']
                print(f"   • Concepts repositioned: {summary['conceptsRepositioned']}")
                print(f"   • Total concepts: {summary['totalConcepts']}")
                print(f"   • Method: {summary['method']}")
                print(f"   • Galaxy radius: {summary['galaxyRadius']}")
                
                if 'distribution' in summary:
                    dist = summary['distribution']
                    print(f"   • X range: {dist['xRange'][0]:.1f} to {dist['xRange'][1]:.1f}")
                    print(f"   • Y range: {dist['yRange'][0]:.1f} to {dist['yRange'][1]:.1f}")
                    print(f"   • Z range: {dist['zRange'][0]:.1f} to {dist['zRange'][1]:.1f}")
            
            print("\n✅ Position distribution has been fixed!")
            print("🌌 Your galaxy should now show properly distributed planets")
            print("🔄 Refresh your browser to see the new layout")
            
        elif response.status_code == 401:
            print("❌ Unauthorized - Admin key required")
            print("The admin endpoint is protected")
            
        else:
            print(f"❌ Request failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"Response: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - make sure your web app is running")
        print("Run: npm run dev (in the apps/web directory)")
        print("Then try this script again")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    main()
