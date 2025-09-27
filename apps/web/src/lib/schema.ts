import { pgTable, text, real, timestamp, integer, index, unique, customType } from 'drizzle-orm/pg-core';
import { relations } from 'drizzle-orm';

// Custom vector type for pgvector
const vector = (dimensions: number) => customType<{ data: number[]; driverData: string }>({
  dataType() {
    return `vector(${dimensions})`;
  },
});

// Concepts table
export const concepts = pgTable('concepts', {
  id: text('id').primaryKey(),
  title: text('title').notNull(),
  summary: text('summary').notNull(),
  source: text('source').notNull().$type<'wikipedia' | 'arxiv' | 'news'>(),
  sourceId: text('source_id').notNull(),
  url: text('url').notNull(),
  category: text('category'),
  createdAt: timestamp('created_at', { withTimezone: true }).defaultNow().notNull(),
  updatedAt: timestamp('updated_at', { withTimezone: true }).defaultNow().notNull(),
}, (table) => ({
  sourceIdx: index('idx_concepts_source').on(table.source),
  categoryIdx: index('idx_concepts_category').on(table.category),
}));

// Embeddings table
export const embeddings = pgTable('embeddings', {
  id: text('id').primaryKey(),
  conceptId: text('concept_id').notNull().references(() => concepts.id, { onDelete: 'cascade' }),
  embedding: vector(384)('embedding').notNull(),
  model: text('model').notNull().default('text-embedding-3-large'),
  createdAt: timestamp('created_at', { withTimezone: true }).defaultNow().notNull(),
}, (table) => ({
  conceptIdIdx: index('idx_embeddings_concept_id').on(table.conceptId),
}));

// Edges table
export const edges = pgTable('edges', {
  id: text('id').primaryKey(),
  sourceId: text('source_id').notNull().references(() => concepts.id, { onDelete: 'cascade' }),
  targetId: text('target_id').notNull().references(() => concepts.id, { onDelete: 'cascade' }),
  weight: real('weight').notNull(),
  edgeType: text('edge_type').notNull().$type<'similarity' | 'citation' | 'category'>(),
  createdAt: timestamp('created_at', { withTimezone: true }).defaultNow().notNull(),
}, (table) => ({
  sourceIdx: index('idx_edges_source').on(table.sourceId),
  targetIdx: index('idx_edges_target').on(table.targetId),
  weightIdx: index('idx_edges_weight').on(table.weight),
  typeIdx: index('idx_edges_type').on(table.edgeType),
  uniqueEdge: unique('unique_edge').on(table.sourceId, table.targetId, table.edgeType),
}));

// Node positions table
export const nodePositions = pgTable('node_positions', {
  conceptId: text('concept_id').primaryKey().references(() => concepts.id, { onDelete: 'cascade' }),
  x: real('x').notNull(),
  y: real('y').notNull(),
  z: real('z').notNull(),
  clusterId: text('cluster_id'),
  createdAt: timestamp('created_at', { withTimezone: true }).defaultNow().notNull(),
  updatedAt: timestamp('updated_at', { withTimezone: true }).defaultNow().notNull(),
}, (table) => ({
  clusterIdx: index('idx_positions_cluster').on(table.clusterId),
}));

// Ingestion status table
export const ingestionStatus = pgTable('ingestion_status', {
  id: integer('id').primaryKey().default(1),
  totalConcepts: integer('total_concepts').default(0).notNull(),
  processedConcepts: integer('processed_concepts').default(0).notNull(),
  totalEmbeddings: integer('total_embeddings').default(0).notNull(),
  totalEdges: integer('total_edges').default(0).notNull(),
  lastUpdated: timestamp('last_updated', { withTimezone: true }).defaultNow().notNull(),
  status: text('status').notNull().default('idle').$type<'idle' | 'ingesting' | 'embedding' | 'building_graph' | 'complete' | 'error'>(),
  errorMessage: text('error_message'),
});

// Relations
export const conceptsRelations = relations(concepts, ({ one, many }) => ({
  embedding: one(embeddings, {
    fields: [concepts.id],
    references: [embeddings.conceptId],
  }),
  position: one(nodePositions, {
    fields: [concepts.id],
    references: [nodePositions.conceptId],
  }),
  outgoingEdges: many(edges, { relationName: 'sourceEdges' }),
  incomingEdges: many(edges, { relationName: 'targetEdges' }),
}));

export const embeddingsRelations = relations(embeddings, ({ one }) => ({
  concept: one(concepts, {
    fields: [embeddings.conceptId],
    references: [concepts.id],
  }),
}));

export const edgesRelations = relations(edges, ({ one }) => ({
  source: one(concepts, {
    fields: [edges.sourceId],
    references: [concepts.id],
    relationName: 'sourceEdges',
  }),
  target: one(concepts, {
    fields: [edges.targetId],
    references: [concepts.id],
    relationName: 'targetEdges',
  }),
}));

export const nodePositionsRelations = relations(nodePositions, ({ one }) => ({
  concept: one(concepts, {
    fields: [nodePositions.conceptId],
    references: [concepts.id],
  }),
}));
