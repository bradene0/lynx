import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { concepts, nodePositions } from '@/lib/schema';
import { desc, sql, eq } from 'drizzle-orm';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const limit = parseInt(searchParams.get('limit') || '10000'); // Support 10K concepts
    const offset = parseInt(searchParams.get('offset') || '0');
    
    // Spatial query parameters for LOD
    const centerX = parseFloat(searchParams.get('centerX') || '0');
    const centerY = parseFloat(searchParams.get('centerY') || '0');
    const centerZ = parseFloat(searchParams.get('centerZ') || '0');
    const radius = parseFloat(searchParams.get('radius') || '1000');
    const importance = parseFloat(searchParams.get('minImportance') || '0');

    // Build spatial query if center is provided
    let query = db
      .select({
        id: concepts.id,
        title: concepts.title,
        summary: concepts.summary,
        category: concepts.category,
        source: concepts.source,
        sourceUrl: concepts.url,
        createdAt: concepts.createdAt,
      })
      .from(concepts);
    
    // Skip spatial filtering for now - just get all concepts
    // TODO: Re-enable spatial queries after testing
    
    const conceptList = await query
      .limit(limit)
      .offset(offset);

    return NextResponse.json(conceptList);
  } catch (error) {
    console.error('Error fetching concepts:', error);
    return NextResponse.json(
      { error: 'Failed to fetch concepts' },
      { status: 500 }
    );
  }
}
