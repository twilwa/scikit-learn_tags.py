/*
  # Add Shared KB Vector Search Function

  1. Functions
    - `match_shared_kb` - performs cosine similarity search on shared KB pool
      - Parameters:
        - `query_embedding` (vector) - the embedded query
        - `match_threshold` (float) - minimum similarity threshold
        - `match_count` (int) - number of results
        - `category_filter` (text) - optional category filter
      - Returns: Shared KB entries with similarity scores

  2. Notes
    - Searches only the shared_kb_pool table
    - Optional category filtering
    - Orders by similarity score
*/

-- Create function for vector similarity search on shared KB
CREATE OR REPLACE FUNCTION match_shared_kb(
  query_embedding vector(384),
  match_threshold float DEFAULT 0.6,
  match_count int DEFAULT 10,
  category_filter text DEFAULT NULL
)
RETURNS TABLE (
  id uuid,
  source_document_id uuid,
  title text,
  category text,
  content text,
  metadata jsonb,
  quality_score numeric,
  usage_count int,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    shared_kb_pool.id,
    shared_kb_pool.source_document_id,
    shared_kb_pool.title,
    shared_kb_pool.category,
    shared_kb_pool.content,
    shared_kb_pool.metadata,
    shared_kb_pool.quality_score,
    shared_kb_pool.usage_count,
    1 - (shared_kb_pool.embedding <=> query_embedding) AS similarity
  FROM shared_kb_pool
  WHERE 
    1 - (shared_kb_pool.embedding <=> query_embedding) > match_threshold
    AND (category_filter IS NULL OR shared_kb_pool.category = category_filter)
  ORDER BY 
    shared_kb_pool.embedding <=> query_embedding,
    shared_kb_pool.quality_score DESC
  LIMIT match_count;
END;
$$;