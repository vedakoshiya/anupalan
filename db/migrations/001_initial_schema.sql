-- ==============================================================================
-- Migration: 001_initial_schema.sql
-- Description: Core schema for Anupalan compliance navigator
-- Target: PostgreSQL 16+ with pgvector & pg_trgm extensions
-- ==============================================================================

-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 1. Instruments Table (Primary catalog of circulars, notifications, and acts)
CREATE TABLE IF NOT EXISTS instruments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    authority TEXT NOT NULL,              -- e.g. 'CBIC', 'GST Council', 'Gujarat Labour Dept', 'MSME Ministry'
    type TEXT NOT NULL,                   -- 'notification', 'circular', 'act', 'rule', 'scheme', 'order'
    number TEXT NOT NULL,                 -- e.g. '12/2024-Central Tax'
    title TEXT NOT NULL,
    jurisdiction TEXT NOT NULL,           -- 'central' | 'gujarat'
    issued_on DATE NOT NULL,
    effective_from DATE,
    effective_to DATE,
    language TEXT[] NOT NULL DEFAULT '{"en"}',
    source_url TEXT NOT NULL,
    raw_object_key TEXT NOT NULL,
    content_hash TEXT NOT NULL UNIQUE,
    ingest_version INT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (authority, type, number)
);

-- 2. Legal Relations Table (Graph linking amendments, supersessions, and rescissions)
CREATE TABLE IF NOT EXISTS instrument_relations (
    from_id UUID NOT NULL REFERENCES instruments(id) ON DELETE CASCADE,
    to_id UUID NOT NULL REFERENCES instruments(id) ON DELETE CASCADE,
    relation TEXT NOT NULL CHECK (relation IN ('amends', 'supersedes', 'clarifies', 'rescinds')),
    effective_from DATE,
    scope TEXT,                           -- e.g. 'Clause 3(b)', 'Entry 15'
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (from_id, to_id, relation)
);

-- 3. Sections Table (Document structure tree)
CREATE TABLE IF NOT EXISTS sections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    instrument_id UUID NOT NULL REFERENCES instruments(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES sections(id) ON DELETE CASCADE,
    path TEXT NOT NULL,                   -- e.g. 'Notif 12/2024 > Para 3 > Cl (b)'
    heading TEXT,
    page_from INT,
    page_to INT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 4. Chunks Table (Indexed semantic units with contextual headers and embeddings)
CREATE TABLE IF NOT EXISTS chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    section_id UUID NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    instrument_id UUID NOT NULL REFERENCES instruments(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    context_header TEXT NOT NULL,
    chunk_type TEXT NOT NULL,             -- 'clause' | 'table_row' | 'definition' | 'proviso'
    effective_from DATE,
    effective_to DATE,
    jurisdiction TEXT NOT NULL,           -- 'central' | 'gujarat'
    subjects TEXT[] NOT NULL DEFAULT '{}',
    language TEXT NOT NULL DEFAULT 'en',  -- 'en' | 'gu' | 'hi'
    embedding VECTOR(1024),               -- Multi-lingual dense embedding (e.g. BGE-M3)
    embed_model TEXT NOT NULL,
    ocr_quality NUMERIC(3,2),             -- Score from 0.00 to 1.00
    bbox JSONB,                           -- Coordinates for visual highlight on PDF page
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 5. Glossary Table (Mapping vernacular and Gujlish variants to canonical legal terms)
CREATE TABLE IF NOT EXISTS glossary (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    canonical_term TEXT NOT NULL,
    variants TEXT[] NOT NULL DEFAULT '{}',
    language TEXT NOT NULL,               -- 'gu' | 'hi' | 'en'
    definition TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 6. Queries Table (Audit log and query trace with DPDP retention)
CREATE TABLE IF NOT EXISTS queries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID,
    raw_query TEXT NOT NULL,
    language TEXT,
    as_of DATE NOT NULL,
    intent TEXT,
    rewritten JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 7. Answers Table (Verification traces, model versions, and cost audits)
CREATE TABLE IF NOT EXISTS answers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_id UUID NOT NULL REFERENCES queries(id) ON DELETE CASCADE,
    retrieved JSONB NOT NULL,             -- Chunks, BM25 scores, vector distances, rerank scores
    prompt_version TEXT NOT NULL,
    model TEXT NOT NULL,
    output JSONB NOT NULL,                -- Claims, citations, action steps
    verifier JSONB NOT NULL,              -- Entailment results, numeric check results
    abstained BOOLEAN NOT NULL DEFAULT FALSE,
    corpus_snapshot TEXT NOT NULL,
    latency_ms INT,
    cost_inr NUMERIC(8,3),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 8. Feedback Table (End-user and accountant quality evaluations)
CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    answer_id UUID NOT NULL REFERENCES answers(id) ON DELETE CASCADE,
    rating SMALLINT CHECK (rating IN (-1, 1)), -- -1: Thumbs down, 1: Thumbs up
    reason_code TEXT,                     -- 'incorrect_rate', 'outdated_rule', 'missing_clause', 'bad_translation'
    comment TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ==============================================================================
-- Performance & Retrieval Indexes
-- ==============================================================================

-- B-Tree index for temporal and jurisdictional pre-filtering
CREATE INDEX IF NOT EXISTS idx_chunks_temporal_filter 
ON chunks (jurisdiction, effective_from, effective_to);

-- GIN index for subject tagging search
CREATE INDEX IF NOT EXISTS idx_chunks_subjects 
ON chunks USING GIN (subjects);

-- Full-Text Search (FTS) index on chunk content for BM25 lexical retrieval
CREATE INDEX IF NOT EXISTS idx_chunks_text_fts 
ON chunks USING GIN (to_tsvector('english', text));

-- HNSW Vector Index on embeddings (Cosine similarity for 1024-dim vectors)
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw 
ON chunks USING hnsw (embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);

-- Index for fast query session lookup
CREATE INDEX IF NOT EXISTS idx_queries_session_id 
ON queries (session_id);

-- Index for DPDP data expiration / retention purging
CREATE INDEX IF NOT EXISTS idx_queries_created_at 
ON queries (created_at);
