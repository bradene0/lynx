import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { concepts } from '@/lib/schema';
import { desc, sql } from 'drizzle-orm';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const limit = parseInt(searchParams.get('limit') || '1000');
    const offset = parseInt(searchParams.get('offset') || '0');

    // Fetch concepts with basic info
    const conceptList = await db
      .select({
        id: concepts.id,
        title: concepts.title,
        summary: concepts.summary,
        source: concepts.source,
        source_id: concepts.sourceId,
        url: concepts.url,
        category: concepts.category,
        created_at: concepts.createdAt,
        updated_at: concepts.updatedAt,
      })
      .from(concepts)
      .orderBy(desc(concepts.createdAt))
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
