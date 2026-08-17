-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the titles table
DROP TABLE IF EXISTS public.prgi_titles CASCADE;
CREATE TABLE public.prgi_titles (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    registration_number VARCHAR(100),
    language VARCHAR(50) NOT NULL,
    periodicity VARCHAR(50) NOT NULL,
    publisher VARCHAR(255),
    owner VARCHAR(255),
    publication_state VARCHAR(100),
    publication_district VARCHAR(100),
    source VARCHAR(50) DEFAULT 'REGISTERED',
    embedding vector(384)
);

-- Index for semantic similarity using HNSW
CREATE INDEX ON public.prgi_titles USING hnsw (embedding vector_cosine_ops);
