import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { concepts, embeddings, nodePositions } from '@/lib/schema';
import { eq, sql, desc, ilike, or } from 'drizzle-orm';
import { SearchRequestSchema, type SearchResponse } from '@lynx/shared';

// Note: Using text search for now, will implement SBERT similarity search later

export async function GET(request: NextRequest) {
  const startTime = Date.now();
  
  try {
    const { searchParams } = new URL(request.url);
    const query = searchParams.get('query');
    const limit = parseInt(searchParams.get('limit') || '20');
    const threshold = parseFloat(searchParams.get('threshold') || '0.7');

    // Validate input
    const validatedInput = SearchRequestSchema.parse({
      query,
      limit,
      threshold,
    });

    if (!validatedInput.query) {
      return NextResponse.json(
        { error: 'Query parameter is required' },
        { status: 400 }
      );
    }

    // Perform simple text search (will upgrade to SBERT similarity later)
    const searchTerm = `%${validatedInput.query.toLowerCase()}%`;
    
    const results = await db
      .select({
        concept: concepts,
        position: nodePositions,
        similarity: sql<number>`1.0`, // Placeholder similarity score
      })
      .from(concepts)
      .leftJoin(nodePositions, eq(concepts.id, nodePositions.conceptId))
      .where(
        or(
          ilike(concepts.title, searchTerm),
          ilike(concepts.summary, searchTerm)
        )
      )
      .orderBy(desc(concepts.createdAt))
      .limit(validatedInput.limit);

    const response: SearchResponse = {
      results: results.map((row) => ({
        concept: {
          id: row.concept.id,
          title: row.concept.title,
          summary: row.concept.summary,
          source: row.concept.source,
          source_id: row.concept.sourceId,
          url: row.concept.url,
          category: row.concept.category || '',
          created_at: row.concept.createdAt,
          updated_at: row.concept.updatedAt,
        },
        similarity: row.similarity,
        position: row.position ? {
          concept_id: row.position.conceptId,
          x: row.position.x,
          y: row.position.y,
          z: row.position.z,
          cluster_id: row.position.clusterId || undefined,
        } : undefined,
      })),
      query: validatedInput.query,
      total: results.length,
      took_ms: Date.now() - startTime,
    };

    return NextResponse.json(response);
  } catch (error) {
    console.error('Search error:', error);
    
    if (error instanceof Error) {
      return NextResponse.json(
        { error: 'Search failed', message: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
