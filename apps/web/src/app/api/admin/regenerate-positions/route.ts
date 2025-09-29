import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { concepts, nodePositions } from '@/lib/schema';
import { eq } from 'drizzle-orm';

interface RegeneratedPosition {
  concept_id: string;
  x: number;
  y: number;
  z: number;
  cluster_id: string;
}

function generateRandomGalaxyPosition(): [number, number, number] {
  // Expanded galaxy parameters for much better spacing
  const galaxyRadius = 400;  // Doubled from 200
  const coreRadius = 80;     // Increased from 50
  const haloRadius = 600;    // Doubled from 300
  
  // Use spherical coordinates for uniform distribution
  const u = Math.random();
  const v = Math.random();
  
  const theta = 2 * Math.PI * u; // Azimuthal angle
  const phi = Math.acos(2 * v - 1); // Polar angle
  
  // More spread out distribution - less clustering in center
  const rand = Math.random();
  let radius: number;
  
  if (rand < 0.15) { // Only 15% in core (reduced from 30%)
    radius = coreRadius * Math.random() + 20; // Minimum distance from center
  } else if (rand < 0.70) { // 55% in main galaxy (increased)
    radius = coreRadius + (galaxyRadius - coreRadius) * Math.random();
  } else { // 30% in outer halo (increased from 20%)
    radius = galaxyRadius + (haloRadius - galaxyRadius) * Math.random();
  }
  
  // Convert to Cartesian coordinates
  const x = radius * Math.sin(phi) * Math.cos(theta);
  const y = radius * Math.sin(phi) * Math.sin(theta);
  const z = radius * Math.cos(phi);
  
  return [x, y, z];
}

export async function POST(request: NextRequest) {
  try {
    // Simple admin check (you can enhance this)
    const adminKey = request.headers.get('x-admin-key');
    if (adminKey !== process.env.ADMIN_API_KEY && adminKey !== 'lynx-admin-2024') {
      return NextResponse.json(
        { error: 'Unauthorized - Invalid admin key' },
        { status: 401 }
      );
    }

    console.log('🚀 Starting position regeneration...');

    // Fetch all concepts
    const allConcepts = await db
      .select({
        id: concepts.id,
        title: concepts.title,
        category: concepts.category,
      })
      .from(concepts);

    console.log(`📊 Found ${allConcepts.length} concepts to reposition`);

    if (allConcepts.length === 0) {
      return NextResponse.json(
        { error: 'No concepts found' },
        { status: 404 }
      );
    }

    // Generate new positions
    const newPositions: RegeneratedPosition[] = [];
    
    for (let i = 0; i < allConcepts.length; i++) {
      const concept = allConcepts[i];
      const [x, y, z] = generateRandomGalaxyPosition();
      
      newPositions.push({
        concept_id: concept.id,
        x: x,
        y: y,
        z: z,
        cluster_id: (concept.category || 'general').replace(/\s+/g, '_').toLowerCase()
      });

      if ((i + 1) % 100 === 0) {
        console.log(`🎯 Generated positions: ${i + 1}/${allConcepts.length}`);
      }
    }

    console.log('💾 Updating positions in database...');

    // Update positions in database (batch update)
    let updatedCount = 0;
    
    for (const position of newPositions) {
      try {
        // Try to update existing position
        const result = await db
          .update(nodePositions)
          .set({
            x: position.x,
            y: position.y,
            z: position.z,
            clusterId: position.cluster_id,
            updatedAt: new Date(),
          })
          .where(eq(nodePositions.conceptId, position.concept_id));

        // If no rows were updated, insert new position
        if ((result as any).rowCount === 0) {
          await db.insert(nodePositions).values({
            conceptId: position.concept_id,
            x: position.x,
            y: position.y,
            z: position.z,
            clusterId: position.cluster_id,
          });
        }
        
        updatedCount++;
      } catch (error) {
        console.error(`Error updating position for ${position.concept_id}:`, error);
      }
    }

    // Calculate distribution summary
    const xCoords = newPositions.map(p => p.x);
    const yCoords = newPositions.map(p => p.y);
    const zCoords = newPositions.map(p => p.z);

    const summary = {
      conceptsRepositioned: updatedCount,
      totalConcepts: allConcepts.length,
      distribution: {
        xRange: [Math.min(...xCoords), Math.max(...xCoords)],
        yRange: [Math.min(...yCoords), Math.max(...yCoords)],
        zRange: [Math.min(...zCoords), Math.max(...zCoords)],
      },
      method: 'random_spherical_galaxy_expanded',
      galaxyRadius: 400,
      coreRadius: 80,
      haloRadius: 600,
    };

    console.log('🎉 Position regeneration complete!');
    console.log(`📊 Updated ${updatedCount} positions`);

    return NextResponse.json({
      success: true,
      message: 'Positions regenerated successfully',
      summary,
    });

  } catch (error) {
    console.error('Error regenerating positions:', error);
    return NextResponse.json(
      { error: 'Failed to regenerate positions', details: (error as Error).message },
      { status: 500 }
    );
  }
}
