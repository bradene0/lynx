import { NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { concepts, embeddings, edges } from '@/lib/schema';
import { count } from 'drizzle-orm';

export async function GET() {
  try {
    // Get current counts from database
    const [conceptCount] = await db.select({ count: count() }).from(concepts);
    const [embeddingCount] = await db.select({ count: count() }).from(embeddings);
    const [edgeCount] = await db.select({ count: count() }).from(edges);

    const status = {
      total_concepts: conceptCount.count,
      processed_concepts: conceptCount.count,
      total_embeddings: embeddingCount.count,
      total_edges: edgeCount.count,
      status: conceptCount.count > 5 ? 'complete' : 'idle',
      last_updated: new Date().toISOString(),
    };

    return NextResponse.json(status);
  } catch (error) {
    console.error('Error fetching ingestion status:', error);
    return NextResponse.json(
      { 
        total_concepts: 0,
        processed_concepts: 0,
        total_embeddings: 0,
        total_edges: 0,
        status: 'error',
        last_updated: new Date().toISOString(),
        errorMessage: 'Failed to fetch status'
      },
      { status: 500 }
    );
  }
}
