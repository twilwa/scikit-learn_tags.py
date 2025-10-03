/*
  # Knowledge Base Sharing and Feedback System

  1. Schema Changes
    - Add `visibility` to kb_documents (private/shared/public)
    - Add `contributed_by` to track contributors
    - Create `kb_feedback` table for user ratings and corrections
    - Create `shared_kb_pool` table for curated shared knowledge
    - Add session pricing and voice features tables

  2. New Tables
    - `kb_feedback` - user feedback on KB quality and relevance
    - `shared_kb_pool` - curated shared knowledge base
    - `voice_sessions` - paid voice session tracking
    - `session_participants` - who's in each session
    - `repl_executions` - Python REPL history in sessions

  3. Features
    - Users can mark their KB as shared (opt-in)
    - Shared KB is searchable by all users
    - Feedback improves shared KB quality over time
    - Voice sessions have time limits and pricing
    - Collaborative REPL execution tracking
*/

-- Add visibility column to kb_documents
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'kb_documents' AND column_name = 'visibility'
  ) THEN
    ALTER TABLE kb_documents ADD COLUMN visibility text DEFAULT 'private';
    ALTER TABLE kb_documents ADD COLUMN contributed_at timestamptz;
    ALTER TABLE kb_documents ADD COLUMN contribution_approved boolean DEFAULT false;
  END IF;
END $$;

-- Add constraint for visibility values
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.constraint_column_usage
    WHERE constraint_name = 'valid_visibility'
  ) THEN
    ALTER TABLE kb_documents ADD CONSTRAINT valid_visibility 
      CHECK (visibility IN ('private', 'shared', 'public'));
  END IF;
END $$;

-- Create kb_feedback table
CREATE TABLE IF NOT EXISTS kb_feedback (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id uuid REFERENCES kb_documents(id) ON DELETE CASCADE,
  chunk_id uuid REFERENCES kb_chunks(id) ON DELETE CASCADE,
  user_id uuid REFERENCES discord_users(id) ON DELETE CASCADE,
  feedback_type text NOT NULL,
  rating integer,
  correction_text text,
  is_helpful boolean,
  tags text[],
  created_at timestamptz DEFAULT now(),
  CONSTRAINT valid_feedback_type CHECK (feedback_type IN ('rating', 'correction', 'helpful', 'tag_suggestion')),
  CONSTRAINT valid_rating CHECK (rating IS NULL OR (rating >= 1 AND rating <= 5))
);

-- Create shared_kb_pool table (curated shared knowledge)
CREATE TABLE IF NOT EXISTS shared_kb_pool (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_document_id uuid REFERENCES kb_documents(id) ON DELETE SET NULL,
  title text NOT NULL,
  category text NOT NULL,
  content text NOT NULL,
  embedding vector(384),
  metadata jsonb DEFAULT '{}'::jsonb,
  quality_score numeric DEFAULT 0.5,
  usage_count integer DEFAULT 0,
  contributor_count integer DEFAULT 1,
  last_updated timestamptz DEFAULT now(),
  created_at timestamptz DEFAULT now()
);

-- Create voice_sessions table
CREATE TABLE IF NOT EXISTS voice_sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  session_url text UNIQUE NOT NULL,
  host_user_id uuid REFERENCES discord_users(id) ON DELETE CASCADE,
  session_type text NOT NULL,
  mode text NOT NULL,
  status text NOT NULL DEFAULT 'waiting',
  price_cents integer NOT NULL,
  duration_minutes integer NOT NULL,
  minutes_used integer DEFAULT 0,
  repo_url text,
  log_session_id uuid REFERENCES sessions(id) ON DELETE SET NULL,
  started_at timestamptz,
  expires_at timestamptz,
  ended_at timestamptz,
  metadata jsonb DEFAULT '{}'::jsonb,
  created_at timestamptz DEFAULT now(),
  CONSTRAINT valid_session_type CHECK (session_type IN ('log_analysis', 'repo_review', 'collaborative_coding', 'debugging')),
  CONSTRAINT valid_mode CHECK (mode IN ('text_only', 'voice_browser', 'voice_discord')),
  CONSTRAINT valid_session_status CHECK (status IN ('waiting', 'active', 'paused', 'completed', 'expired', 'cancelled'))
);

-- Create session_participants table
CREATE TABLE IF NOT EXISTS session_participants (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id uuid NOT NULL REFERENCES voice_sessions(id) ON DELETE CASCADE,
  user_id uuid REFERENCES discord_users(id) ON DELETE CASCADE,
  role text NOT NULL,
  joined_at timestamptz DEFAULT now(),
  left_at timestamptz,
  is_active boolean DEFAULT true,
  CONSTRAINT valid_participant_role CHECK (role IN ('host', 'guest', 'ai_assistant', 'observer'))
);

-- Create repl_executions table
CREATE TABLE IF NOT EXISTS repl_executions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id uuid NOT NULL REFERENCES voice_sessions(id) ON DELETE CASCADE,
  user_id uuid REFERENCES discord_users(id) ON DELETE CASCADE,
  code text NOT NULL,
  output text,
  output_type text,
  visualization_data jsonb,
  execution_time_ms integer,
  error_message text,
  created_at timestamptz DEFAULT now(),
  CONSTRAINT valid_output_type CHECK (output_type IN ('text', 'json', 'graph', 'dataframe', 'image', 'error'))
);

-- Enable RLS
ALTER TABLE kb_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE shared_kb_pool ENABLE ROW LEVEL SECURITY;
ALTER TABLE voice_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_participants ENABLE ROW LEVEL SECURITY;
ALTER TABLE repl_executions ENABLE ROW LEVEL SECURITY;

-- Policies for kb_feedback
CREATE POLICY "Users can view feedback on shared KB"
  ON kb_feedback FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM kb_documents
      WHERE kb_documents.id = kb_feedback.document_id
      AND kb_documents.visibility IN ('shared', 'public')
    )
  );

CREATE POLICY "Users can submit feedback"
  ON kb_feedback FOR INSERT
  TO authenticated
  WITH CHECK (true);

-- Policies for shared_kb_pool
CREATE POLICY "Anyone can view shared KB pool"
  ON shared_kb_pool FOR SELECT
  TO authenticated, anon
  USING (true);

CREATE POLICY "Service can manage shared KB pool"
  ON shared_kb_pool FOR ALL
  TO authenticated
  USING (true)
  WITH CHECK (true);

-- Policies for voice_sessions
CREATE POLICY "Users can view their own sessions"
  ON voice_sessions FOR SELECT
  TO authenticated
  USING (
    host_user_id = auth.uid()::uuid
    OR id IN (
      SELECT session_id FROM session_participants
      WHERE user_id = auth.uid()::uuid
    )
  );

CREATE POLICY "Users can create sessions"
  ON voice_sessions FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Session hosts can update their sessions"
  ON voice_sessions FOR UPDATE
  TO authenticated
  USING (host_user_id = auth.uid()::uuid)
  WITH CHECK (host_user_id = auth.uid()::uuid);

-- Policies for session_participants
CREATE POLICY "Users can view session participants"
  ON session_participants FOR SELECT
  TO authenticated
  USING (
    user_id = auth.uid()::uuid
    OR session_id IN (
      SELECT id FROM voice_sessions
      WHERE host_user_id = auth.uid()::uuid
    )
  );

CREATE POLICY "System can manage participants"
  ON session_participants FOR ALL
  TO authenticated
  USING (true)
  WITH CHECK (true);

-- Policies for repl_executions
CREATE POLICY "Session participants can view REPL history"
  ON repl_executions FOR SELECT
  TO authenticated
  USING (
    session_id IN (
      SELECT session_id FROM session_participants
      WHERE user_id = auth.uid()::uuid
    )
  );

CREATE POLICY "Session participants can execute code"
  ON repl_executions FOR INSERT
  TO authenticated
  WITH CHECK (
    session_id IN (
      SELECT session_id FROM session_participants
      WHERE user_id = auth.uid()::uuid AND is_active = true
    )
  );

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_kb_documents_visibility ON kb_documents(visibility);
CREATE INDEX IF NOT EXISTS idx_kb_documents_contributed ON kb_documents(contributed_at DESC) WHERE visibility = 'shared';

CREATE INDEX IF NOT EXISTS idx_kb_feedback_document ON kb_feedback(document_id);
CREATE INDEX IF NOT EXISTS idx_kb_feedback_user ON kb_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_kb_feedback_helpful ON kb_feedback(is_helpful) WHERE is_helpful = true;

CREATE INDEX IF NOT EXISTS idx_shared_kb_category ON shared_kb_pool(category);
CREATE INDEX IF NOT EXISTS idx_shared_kb_quality ON shared_kb_pool(quality_score DESC);
CREATE INDEX IF NOT EXISTS idx_shared_kb_usage ON shared_kb_pool(usage_count DESC);
CREATE INDEX IF NOT EXISTS idx_shared_kb_embedding ON shared_kb_pool USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_voice_sessions_host ON voice_sessions(host_user_id);
CREATE INDEX IF NOT EXISTS idx_voice_sessions_status ON voice_sessions(status);
CREATE INDEX IF NOT EXISTS idx_voice_sessions_created ON voice_sessions(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_session_participants_session ON session_participants(session_id);
CREATE INDEX IF NOT EXISTS idx_session_participants_user ON session_participants(user_id);

CREATE INDEX IF NOT EXISTS idx_repl_executions_session ON repl_executions(session_id);
CREATE INDEX IF NOT EXISTS idx_repl_executions_created ON repl_executions(created_at DESC);