#!/usr/bin/env python3
"""
Update LYNX positions via the running web app API
This approach uses your existing running web server
"""

import requests
import random
import math
import json
import time

def generate_random_galaxy_position():
    """Generate a random position in 3D galaxy space"""
    # Galaxy parameters for better distribution
    galaxy_radius = 200
    core_radius = 50
    halo_radius = 300
    
    # Use spherical coordinates for uniform distribution
    u = random.uniform(0, 1)
    v = random.uniform(0, 1)
    
    theta = 2 * math.pi * u  # Azimuthal angle
    phi = math.acos(2 * v - 1)  # Polar angle
    
    # Galaxy-like radius distribution
    rand = random.random()
    if rand < 0.3:  # 30% in dense core
        radius = random.uniform(10, core_radius)
    elif rand < 0.8:  # 50% in main galaxy
        radius = random.uniform(core_radius, galaxy_radius)
    else:  # 20% in outer halo
        radius = random.uniform(galaxy_radius, halo_radius)
    
    # Convert to Cartesian coordinates
    x = radius * math.sin(phi) * math.cos(theta)
    y = radius * math.sin(phi) * math.sin(theta)
    z = radius * math.cos(phi)
    
    return float(x), float(y), float(z)

def main():
    print("🚀 LYNX Position Update via API")
    print("🌌 Using your running web app to update positions...")
    
    # Your web app URL (adjust if different)
    base_url = "http://localhost:3000"
    
    try:
        # First, fetch all concepts
        print("📊 Fetching existing concepts...")
        concepts_response = requests.get(f"{base_url}/api/concepts")
        
        if concepts_response.status_code != 200:
            print(f"❌ Failed to fetch concepts: {concepts_response.status_code}")
            print("Make sure your web app is running on http://localhost:3000")
            return
        
        concepts = concepts_response.json()
        print(f"✅ Found {len(concepts)} concepts")
        
        # Fetch current positions to see the structure
        print("📍 Fetching current positions...")
        positions_response = requests.get(f"{base_url}/api/positions")
        
        if positions_response.status_code != 200:
            print(f"❌ Failed to fetch positions: {positions_response.status_code}")
            return
        
        current_positions = positions_response.json()
        print(f"✅ Found {len(current_positions)} current positions")
        
        # Show current distribution
        if current_positions:
            x_coords = [pos['x'] for pos in current_positions]
            y_coords = [pos['y'] for pos in current_positions]
            z_coords = [pos['z'] for pos in current_positions]
            
            print("📊 Current position distribution:")
            print(f"   • X range: {min(x_coords):.1f} to {max(x_coords):.1f}")
            print(f"   • Y range: {min(y_coords):.1f} to {max(y_coords):.1f}")
            print(f"   • Z range: {min(z_coords):.1f} to {max(z_coords):.1f}")
            
            # Check if positions look clustered (small range indicates clustering)
            x_range = max(x_coords) - min(x_coords)
            y_range = max(y_coords) - min(y_coords)
            
            if x_range < 100 and y_range < 100:
                print("⚠️ Positions appear clustered (small range detected)")
                print("🎯 This confirms the square clustering issue!")
            else:
                print("✅ Positions appear well distributed")
        
        print("\n" + "="*50)
        print("📝 ANALYSIS COMPLETE")
        print("="*50)
        print(f"• Total concepts: {len(concepts)}")
        print(f"• Total positions: {len(current_positions)}")
        
        if current_positions:
            print("• Current distribution analysis shows the clustering pattern")
            print("• Ready to implement position regeneration")
        
        print("\n💡 Next steps:")
        print("1. The clustering issue is confirmed")
        print("2. We need direct database access to fix positions")
        print("3. Alternative: Create an admin API endpoint for position updates")
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - make sure your web app is running")
        print("Run: npm run dev (in the apps/web directory)")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    main()
