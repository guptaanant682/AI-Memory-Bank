-- Enable the vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    summary TEXT,
    tags TEXT[] DEFAULT '{}',
    file_type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create document_chunks table with vector embeddings
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    word_count INTEGER NOT NULL,
    embedding vector(384), -- all-MiniLM-L6-v2 produces 384-dimensional embeddings
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_documents_tags ON documents USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_documents_file_type ON documents(file_type);
CREATE INDEX IF NOT EXISTS idx_documents_uploaded_at ON documents(uploaded_at);

CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Create RLS (Row Level Security) policies
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;

-- For now, allow all operations (in production, implement proper user-based policies)
CREATE POLICY "Allow all operations on documents" ON documents
    FOR ALL USING (true);

CREATE POLICY "Allow all operations on document_chunks" ON document_chunks
    FOR ALL USING (true);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to auto-update updated_at
CREATE TRIGGER update_documents_updated_at 
    BEFORE UPDATE ON documents 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create function for similarity search
CREATE OR REPLACE FUNCTION match_chunks(
    query_embedding vector(384),
    match_threshold float DEFAULT 0.5,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    document_id UUID,
    content TEXT,
    chunk_index INTEGER,
    word_count INTEGER,
    similarity FLOAT
)
LANGUAGE SQL STABLE
AS $$
    SELECT
        document_chunks.id,
        document_chunks.document_id,
        document_chunks.content,
        document_chunks.chunk_index,
        document_chunks.word_count,
        1 - (document_chunks.embedding <=> query_embedding) AS similarity
    FROM document_chunks
    WHERE 1 - (document_chunks.embedding <=> query_embedding) > match_threshold
    ORDER BY similarity DESC
    LIMIT match_count;
$$;