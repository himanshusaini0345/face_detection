CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS drive_folders (
    id         TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    parent_id  TEXT,            -- plain TEXT, no FK — parent may not be visible to service account
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS drive_files (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    webviewlink TEXT NOT NULL,
    folder_id   TEXT,           -- plain TEXT, no FK
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS pictures (
    id          SERIAL PRIMARY KEY,
    file_id     TEXT NOT NULL,
    webviewlink TEXT NOT NULL,
    embedding   vector(768),
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS drive_folders_parent_idx ON drive_folders(parent_id);
CREATE INDEX IF NOT EXISTS drive_files_folder_idx   ON drive_files(folder_id);
CREATE INDEX IF NOT EXISTS pictures_embedding_idx
    ON pictures USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);