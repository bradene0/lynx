import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { edges } from '@/lib/schema';
import { desc, sql, gte } from 'drizzle-orm';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const limit = parseInt(searchParams.get('limit') || '1000');
    const offset = parseInt(searchParams.get('offset') || '0');
    const minWeight = parseFloat(searchParams.get('minWeight') || '0.0');

    // Fetch edges from database
    const edgeList = await db
      .select({
        id: edges.id,
        source_id: edges.sourceId,
        target_id: edges.targetId,
        weight: edges.weight,
        edge_type: edges.edgeType,
      })
      .from(edges)
      .where(gte(edges.weight, minWeight))
      .orderBy(desc(edges.weight))
      .limit(limit)
      .offset(offset);

    return NextResponse.json(edgeList);
  } catch (error) {
    console.error('Error fetching edges:', error);
    return NextResponse.json(
      { error: 'Failed to fetch edges' },
      { status: 500 }
    );
  }
}
