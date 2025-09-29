import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { concepts, embeddings, edges } from '@/lib/schema';
import { eq, sql } from 'drizzle-orm';

// Admin API to generate semantic edges
export async function POST(request: NextRequest) {
  try {
    // Admin authentication check
    const adminKey = request.headers.get('x-admin-key');
    if (!adminKey || adminKey !== process.env.ADMIN_API_KEY) {
      return NextResponse.json(
        { error: 'Unauthorized - Invalid admin key' },
        { status: 401 }
      );
    }

    // Verify admin key is set in environment
    if (!process.env.ADMIN_API_KEY) {
      console.error('ADMIN_API_KEY environment variable not set');
      return NextResponse.json(
        { error: 'Server configuration error' },
        { status: 500 }
      );
    }
    const { searchParams } = new URL(request.url);
    const clearExisting = searchParams.get('clear') === 'true';
    const threshold = parseFloat(searchParams.get('threshold') || '0.6');
    const maxEdgesPerNode = parseInt(searchParams.get('maxEdges') || '12');

    console.log('🚀 Starting edge generation...');
    console.log(`Parameters: threshold=${threshold}, maxEdges=${maxEdgesPerNode}, clear=${clearExisting}`);

    // Step 1: Clear existing edges if requested
    if (clearExisting) {
      console.log('🗑️ Clearing existing edges...');
      await db.delete(edges);
      console.log('✅ Existing edges cleared');
    }

    // Step 2: Get all embeddings with concept info
    console.log('📊 Fetching embeddings...');
    const embeddingsData = await db
      .select({
        conceptId: embeddings.conceptId,
        embedding: embeddings.embedding,
        title: concepts.title,
        category: concepts.category,
      })
      .from(embeddings)
      .innerJoin(concepts, eq(embeddings.conceptId, concepts.id));

    console.log(`✅ Loaded ${embeddingsData.length} embeddings`);

    if (embeddingsData.length === 0) {
      return NextResponse.json(
        { error: 'No embeddings found. Generate embeddings first.' },
        { status: 400 }
      );
    }

    // Step 3: Compute similarities and generate edges
    console.log('🧮 Computing similarities...');
    const newEdges: Array<{
      id: string;
      sourceId: string;
      targetId: string;
      weight: number;
      edgeType: 'similarity' | 'citation' | 'category';
    }> = [];

    // Convert embeddings to arrays for computation
    const embeddingVectors = embeddingsData.map(item => {
      const embedding = Array.isArray(item.embedding) ? item.embedding : JSON.parse(item.embedding as string);
      return {
        conceptId: item.conceptId,
        vector: embedding,
        title: item.title,
        category: item.category,
      };
    });

    // Compute cosine similarities
    for (let i = 0; i < embeddingVectors.length; i++) {
      const sourceVector = embeddingVectors[i];
      const similarities: Array<{ conceptId: string; similarity: number }> = [];

      for (let j = i + 1; j < embeddingVectors.length; j++) {
        const targetVector = embeddingVectors[j];
        
        // Compute cosine similarity
        const dotProduct = sourceVector.vector.reduce((sum: number, a: number, idx: number) => 
          sum + a * targetVector.vector[idx], 0);
        
        const magnitudeA = Math.sqrt(sourceVector.vector.reduce((sum: number, a: number) => sum + a * a, 0));
        const magnitudeB = Math.sqrt(targetVector.vector.reduce((sum: number, b: number) => sum + b * b, 0));
        
        const similarity = dotProduct / (magnitudeA * magnitudeB);

        if (similarity >= threshold) {
          similarities.push({
            conceptId: targetVector.conceptId,
            similarity: similarity,
          });
        }
      }

      // Sort by similarity and take top k
      similarities.sort((a, b) => b.similarity - a.similarity);
      const topSimilarities = similarities.slice(0, maxEdgesPerNode);

      // Create edge records
      for (const sim of topSimilarities) {
        newEdges.push({
          id: crypto.randomUUID(),
          sourceId: sourceVector.conceptId,
          targetId: sim.conceptId,
          weight: sim.similarity,
          edgeType: 'similarity',
        });
      }

      // Progress logging
      if ((i + 1) % 100 === 0) {
        console.log(`Progress: ${i + 1}/${embeddingVectors.length} concepts processed`);
      }
    }

    console.log(`🔗 Generated ${newEdges.length} edges`);

    // Step 4: Insert edges in batches
    console.log('💾 Inserting edges...');
    const batchSize = 1000;
    let insertedCount = 0;

    for (let i = 0; i < newEdges.length; i += batchSize) {
      const batch = newEdges.slice(i, i + batchSize);
      await db.insert(edges).values(batch);
      insertedCount += batch.length;
      
      if (i % 5000 === 0) {
        console.log(`Inserted ${insertedCount}/${newEdges.length} edges...`);
      }
    }

    // Step 5: Generate statistics
    const edgeStats = await db
      .select({
        totalEdges: sql<number>`COUNT(*)`,
        avgWeight: sql<number>`AVG(weight)`,
        minWeight: sql<number>`MIN(weight)`,
        maxWeight: sql<number>`MAX(weight)`,
      })
      .from(edges);

    const stats = edgeStats[0];

    console.log('🎉 Edge generation complete!');
    console.log(`📊 Statistics: ${stats.totalEdges} edges, avg weight: ${stats.avgWeight?.toFixed(3)}`);

    return NextResponse.json({
      success: true,
      message: 'Edges generated successfully',
      statistics: {
        totalConcepts: embeddingsData.length,
        totalEdges: stats.totalEdges,
        averageWeight: stats.avgWeight,
        weightRange: {
          min: stats.minWeight,
          max: stats.maxWeight,
        },
        averageEdgesPerConcept: (stats.totalEdges * 2) / embeddingsData.length, // Bidirectional
        threshold: threshold,
        maxEdgesPerNode: maxEdgesPerNode,
      },
    });

  } catch (error) {
    console.error('Error generating edges:', error);
    return NextResponse.json(
      { error: 'Failed to generate edges', details: (error as Error).message },
      { status: 500 }
    );
  }
}
