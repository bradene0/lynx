import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { nodePositions } from '@/lib/schema';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const limit = parseInt(searchParams.get('limit') || '10000');
    const offset = parseInt(searchParams.get('offset') || '0');

    // Fetch node positions
    const positions = await db
      .select({
        concept_id: nodePositions.conceptId,
        x: nodePositions.x,
        y: nodePositions.y,
        z: nodePositions.z,
        cluster_id: nodePositions.clusterId,
      })
      .from(nodePositions)
      .limit(limit)
      .offset(offset);

    return NextResponse.json(positions);
  } catch (error) {
    console.error('Error fetching positions:', error);
    return NextResponse.json(
      { error: 'Failed to fetch positions' },
      { status: 500 }
    );
  }
}
