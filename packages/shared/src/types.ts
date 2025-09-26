import { z } from 'zod';

// Core concept schema
export const ConceptSchema = z.object({
  id: z.string(),
  title: z.string(),
  summary: z.string(),
  source: z.enum(['wikipedia', 'arxiv', 'news']),
  source_id: z.string(),
  url: z.string().url(),
  category: z.string().optional(),
  created_at: z.date(),
  updated_at: z.date(),
});

export type Concept = z.infer<typeof ConceptSchema>;

// Embedding schema
export const EmbeddingSchema = z.object({
  id: z.string(),
  concept_id: z.string(),
  embedding: z.array(z.number()),
  model: z.string().default('text-embedding-3-large'),
  created_at: z.date(),
});

export type Embedding = z.infer<typeof EmbeddingSchema>;

// Edge schema for graph connections
export const EdgeSchema = z.object({
  id: z.string(),
  source_id: z.string(),
  target_id: z.string(),
  weight: z.number().min(0).max(1),
  edge_type: z.enum(['similarity', 'citation', 'category']),
  created_at: z.date(),
});

export type Edge = z.infer<typeof EdgeSchema>;

// Node position for visualization
export const NodePositionSchema = z.object({
  concept_id: z.string(),
  x: z.number(),
  y: z.number(),
  z: z.number(),
  cluster_id: z.string().optional(),
});

export type NodePosition = z.infer<typeof NodePositionSchema>;

// API request/response schemas
export const SearchRequestSchema = z.object({
  query: z.string().min(1).max(500),
  limit: z.number().min(1).max(100).default(20),
  threshold: z.number().min(0).max(1).default(0.7),
});

export type SearchRequest = z.infer<typeof SearchRequestSchema>;

export const SearchResultSchema = z.object({
  concept: ConceptSchema,
  similarity: z.number(),
  position: NodePositionSchema.optional(),
});

export type SearchResult = z.infer<typeof SearchResultSchema>;

export const SearchResponseSchema = z.object({
  results: z.array(SearchResultSchema),
  query: z.string(),
  total: z.number(),
  took_ms: z.number(),
});

export type SearchResponse = z.infer<typeof SearchResponseSchema>;

// Pathfinding schemas
export const PathRequestSchema = z.object({
  source_id: z.string(),
  target_id: z.string(),
  max_depth: z.number().min(1).max(10).default(6),
});

export type PathRequest = z.infer<typeof PathRequestSchema>;

export const PathNodeSchema = z.object({
  concept: ConceptSchema,
  distance: z.number(),
  position: NodePositionSchema.optional(),
});

export type PathNode = z.infer<typeof PathNodeSchema>;

export const PathResponseSchema = z.object({
  path: z.array(PathNodeSchema),
  total_distance: z.number(),
  took_ms: z.number(),
});

export type PathResponse = z.infer<typeof PathResponseSchema>;

// Wormhole (cross-domain connection) schemas
export const WormholeSchema = z.object({
  source: ConceptSchema,
  target: ConceptSchema,
  similarity: z.number(),
  cross_domain: z.boolean(),
  source_category: z.string(),
  target_category: z.string(),
});

export type Wormhole = z.infer<typeof WormholeSchema>;

// Galaxy viewport for spatial queries
export const ViewportSchema = z.object({
  center_x: z.number(),
  center_y: z.number(),
  center_z: z.number(),
  radius: z.number().positive(),
  zoom_level: z.number().min(0).max(10),
});

export type Viewport = z.infer<typeof ViewportSchema>;

// Concept detail with neighbors
export const ConceptDetailSchema = z.object({
  concept: ConceptSchema,
  position: NodePositionSchema,
  neighbors: z.array(z.object({
    concept: ConceptSchema,
    similarity: z.number(),
    edge_type: z.string(),
  })),
  wormholes: z.array(WormholeSchema),
});

export type ConceptDetail = z.infer<typeof ConceptDetailSchema>;

// API Error schema
export const ApiErrorSchema = z.object({
  error: z.string(),
  message: z.string(),
  code: z.number(),
});

export type ApiError = z.infer<typeof ApiErrorSchema>;

// Ingestion status
export const IngestionStatusSchema = z.object({
  total_concepts: z.number(),
  processed_concepts: z.number(),
  total_embeddings: z.number(),
  total_edges: z.number(),
  last_updated: z.date(),
  status: z.enum(['idle', 'ingesting', 'embedding', 'building_graph', 'complete', 'error']),
});

export type IngestionStatus = z.infer<typeof IngestionStatusSchema>;
