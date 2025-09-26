import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { concepts, edges, nodePositions } from '@/lib/schema';
import { eq, or, and, desc } from 'drizzle-orm';
import { type ConceptDetail } from '@lynx/shared';

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const startTime = Date.now();
  
  try {
    const conceptId = params.id;

    if (!conceptId) {
      return NextResponse.json(
        { error: 'Concept ID is required' },
        { status: 400 }
      );
    }

    // Get the main concept with position
    const conceptResult = await db
      .select({
        concept: concepts,
        position: nodePositions,
      })
      .from(concepts)
      .leftJoin(nodePositions, eq(concepts.id, nodePositions.conceptId))
      .where(eq(concepts.id, conceptId))
      .limit(1);

    if (conceptResult.length === 0) {
      return NextResponse.json(
        { error: 'Concept not found' },
        { status: 404 }
      );
    }

    const { concept, position } = conceptResult[0];

    // Get neighbors (connected concepts)
    const neighbors = await db
      .select({
        concept: concepts,
        edge: edges,
      })
      .from(edges)
      .innerJoin(
        concepts,
        or(
          and(eq(edges.sourceId, conceptId), eq(concepts.id, edges.targetId)),
          and(eq(edges.targetId, conceptId), eq(concepts.id, edges.sourceId))
        )
      )
      .where(or(eq(edges.sourceId, conceptId), eq(edges.targetId, conceptId)))
      .orderBy(desc(edges.weight))
      .limit(20);

    // Find wormholes (cross-domain connections)
    const wormholes = neighbors
      .filter((neighbor) => {
        const neighborCategory = neighbor.concept.category;
        const conceptCategory = concept.category;
        return neighborCategory && 
               conceptCategory && 
               neighborCategory !== conceptCategory &&
               neighbor.edge.weight > 0.8; // High similarity across domains
      })
      .slice(0, 5);

    const response: ConceptDetail = {
      concept: {
        id: concept.id,
        title: concept.title,
        summary: concept.summary,
        source: concept.source,
        source_id: concept.sourceId,
        url: concept.url,
        category: concept.category || '',
        created_at: concept.createdAt,
        updated_at: concept.updatedAt,
      },
      position: position ? {
        concept_id: position.conceptId,
        x: position.x,
        y: position.y,
        z: position.z,
        cluster_id: position.clusterId || undefined,
      } : {
        concept_id: conceptId,
        x: 0,
        y: 0,
        z: 0,
      },
      neighbors: neighbors.map((neighbor) => ({
        concept: {
          id: neighbor.concept.id,
          title: neighbor.concept.title,
          summary: neighbor.concept.summary,
          source: neighbor.concept.source,
          source_id: neighbor.concept.sourceId,
          url: neighbor.concept.url,
          category: neighbor.concept.category || '',
          created_at: neighbor.concept.createdAt,
          updated_at: neighbor.concept.updatedAt,
        },
        similarity: neighbor.edge.weight,
        edge_type: neighbor.edge.edgeType,
      })),
      wormholes: wormholes.map((wormhole) => ({
        source: {
          id: concept.id,
          title: concept.title,
          summary: concept.summary,
          source: concept.source,
          source_id: concept.sourceId,
          url: concept.url,
          category: concept.category || '',
          created_at: concept.createdAt,
          updated_at: concept.updatedAt,
        },
        target: {
          id: wormhole.concept.id,
          title: wormhole.concept.title,
          summary: wormhole.concept.summary,
          source: wormhole.concept.source,
          source_id: wormhole.concept.sourceId,
          url: wormhole.concept.url,
          category: wormhole.concept.category || '',
          created_at: wormhole.concept.createdAt,
          updated_at: wormhole.concept.updatedAt,
        },
        similarity: wormhole.edge.weight,
        cross_domain: true,
        source_category: concept.category || '',
        target_category: wormhole.concept.category || '',
      })),
    };

    return NextResponse.json(response);
  } catch (error) {
    console.error('Concept detail error:', error);
    
    return NextResponse.json(
      { error: 'Failed to fetch concept details' },
      { status: 500 }
    );
  }
}
