import { NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { ingestionStatus } from '@/lib/schema';
import { eq } from 'drizzle-orm';
import { type IngestionStatus } from '@lynx/shared';

export async function GET() {
  try {
    const status = await db
      .select()
      .from(ingestionStatus)
      .where(eq(ingestionStatus.id, 1))
      .limit(1);

    if (status.length === 0) {
      // Return default status if no record exists
      const defaultStatus: IngestionStatus = {
        total_concepts: 0,
        processed_concepts: 0,
        total_embeddings: 0,
        total_edges: 0,
        last_updated: new Date(),
        status: 'idle',
      };
      
      return NextResponse.json(defaultStatus);
    }

    const result = status[0];
    const response: IngestionStatus = {
      total_concepts: result.totalConcepts,
      processed_concepts: result.processedConcepts,
      total_embeddings: result.totalEmbeddings,
      total_edges: result.totalEdges,
      last_updated: result.lastUpdated,
      status: result.status,
    };

    return NextResponse.json(response);
  } catch (error) {
    console.error('Status fetch error:', error);
    
    return NextResponse.json(
      { error: 'Failed to fetch ingestion status' },
      { status: 500 }
    );
  }
}
