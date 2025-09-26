-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create concepts table
CREATE TABLE IF NOT EXISTS concepts (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    source TEXT NOT NULL CHECK (source IN ('wikipedia', 'arxiv', 'news')),
    source_id TEXT NOT NULL,
    url TEXT NOT NULL,
    category TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create embeddings table with pgvector
CREATE TABLE IF NOT EXISTS embeddings (
    id TEXT PRIMARY KEY,
    concept_id TEXT NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    embedding vector(3072) NOT NULL,
    model TEXT NOT NULL DEFAULT 'text-embedding-3-large',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create edges table for graph connections
CREATE TABLE IF NOT EXISTS edges (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    target_id TEXT NOT NULL REFERENCES concepts(id) ON DELETE CASCADE,
    weight REAL NOT NULL CHECK (weight >= 0 AND weight <= 1),
    edge_type TEXT NOT NULL CHECK (edge_type IN ('similarity', 'citation', 'category')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(source_id, target_id, edge_type)
);

-- Create node positions table for pre-computed layout
CREATE TABLE IF NOT EXISTS node_positions (
    concept_id TEXT PRIMARY KEY REFERENCES concepts(id) ON DELETE CASCADE,
    x REAL NOT NULL,
    y REAL NOT NULL,
    z REAL NOT NULL,
    cluster_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create ingestion status table
CREATE TABLE IF NOT EXISTS ingestion_status (
    id INTEGER PRIMARY KEY DEFAULT 1,
    total_concepts INTEGER DEFAULT 0,
    processed_concepts INTEGER DEFAULT 0,
    total_embeddings INTEGER DEFAULT 0,
    total_edges INTEGER DEFAULT 0,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT NOT NULL DEFAULT 'idle' CHECK (status IN ('idle', 'ingesting', 'embedding', 'building_graph', 'complete', 'error')),
    error_message TEXT
);

-- Insert initial status row
INSERT INTO ingestion_status (id) VALUES (1) ON CONFLICT (id) DO NOTHING;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_concepts_source ON concepts(source);
CREATE INDEX IF NOT EXISTS idx_concepts_category ON concepts(category);
CREATE INDEX IF NOT EXISTS idx_concepts_title ON concepts USING GIN(to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_concepts_summary ON concepts USING GIN(to_tsvector('english', summary));

CREATE INDEX IF NOT EXISTS idx_embeddings_concept_id ON embeddings(concept_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id);
CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id);
CREATE INDEX IF NOT EXISTS idx_edges_weight ON edges(weight DESC);
CREATE INDEX IF NOT EXISTS idx_edges_type ON edges(edge_type);

CREATE INDEX IF NOT EXISTS idx_positions_cluster ON node_positions(cluster_id);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_concepts_updated_at BEFORE UPDATE ON concepts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_positions_updated_at BEFORE UPDATE ON node_positions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
