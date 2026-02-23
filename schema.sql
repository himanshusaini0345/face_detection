"""
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS pictures (
    id          SERIAL PRIMARY KEY,
    file_id     TEXT NOT NULL,
    webviewlink TEXT NOT NULL,
    embedding   vector(768),          -- imgbeddings outputs 768-dim vectors
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS pictures_embedding_idx
    ON pictures USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
"""