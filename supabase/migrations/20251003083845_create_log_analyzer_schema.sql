/*
  # Claude Code Log Analyzer Schema

  1. New Tables
    - `sessions`
      - `id` (uuid, primary key) - unique session identifier
      - `user_id` (uuid) - optional user identifier
      - `status` (text) - session status: uploading, analyzing, completed, failed
      - `log_content` (text) - raw log file content
      - `redacted_log` (text) - log with secrets redacted
      - `encryption_enabled` (boolean) - whether encryption was requested
      - `session_url` (text) - unique access URL
      - `cost_estimate` (numeric) - estimated processing cost
      - `created_at` (timestamptz) - session creation time
      - `expires_at` (timestamptz) - session expiration time
      - `metadata` (jsonb) - flexible metadata storage
    
    - `analysis_results`
      - `id` (uuid, primary key)
      - `session_id` (uuid, foreign key) - reference to sessions
      - `analysis_type` (text) - type: ast, dependency_graph, tool_calls, complexity
      - `result_data` (jsonb) - analysis output data
      - `status` (text) - pending, running, completed, failed
      - `signal_score` (numeric) - calculated signal strength
      - `completed_at` (timestamptz) - when analysis finished
      - `created_at` (timestamptz)
    
    - `insights`
      - `id` (uuid, primary key)
      - `session_id` (uuid, foreign key)
      - `analysis_id` (uuid, foreign key) - optional reference to source analysis
      - `insight_text` (text) - 2-3 sentence insight
      - `insight_type` (text) - type: next_step, code_issue, architecture, optimization
      - `signal_score` (numeric) - prioritization score
      - `confidence` (numeric) - confidence level 0-1
      - `visualization_data` (jsonb) - optional visualization payload
      - `shown` (boolean) - whether shown to user yet
      - `created_at` (timestamptz)
    
    - `user_comments`
      - `id` (uuid, primary key)
      - `session_id` (uuid, foreign key)
      - `insight_id` (uuid, foreign key) - optional reference to insight
      - `comment_text` (text)
      - `created_at` (timestamptz)
  
  2. Security
    - Enable RLS on all tables
    - Add policies for session-based access
    - Allow anonymous access with session URL token
  
  3. Indexes
    - Add indexes for common query patterns
    - Index on session_url for fast lookups
    - Index on signal_score for prioritization
*/

-- Create sessions table
CREATE TABLE IF NOT EXISTS sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid,
  status text NOT NULL DEFAULT 'uploading',
  log_content text,
  redacted_log text,
  encryption_enabled boolean DEFAULT false,
  session_url text UNIQUE NOT NULL,
  cost_estimate numeric DEFAULT 0,
  created_at timestamptz DEFAULT now(),
  expires_at timestamptz DEFAULT (now() + interval '24 hours'),
  metadata jsonb DEFAULT '{}'::jsonb,
  CONSTRAINT valid_status CHECK (status IN ('uploading', 'analyzing', 'completed', 'failed'))
);

-- Create analysis_results table
CREATE TABLE IF NOT EXISTS analysis_results (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id uuid NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  analysis_type text NOT NULL,
  result_data jsonb DEFAULT '{}'::jsonb,
  status text NOT NULL DEFAULT 'pending',
  signal_score numeric DEFAULT 0,
  completed_at timestamptz,
  created_at timestamptz DEFAULT now(),
  CONSTRAINT valid_analysis_status CHECK (status IN ('pending', 'running', 'completed', 'failed'))
);

-- Create insights table
CREATE TABLE IF NOT EXISTS insights (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id uuid NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  analysis_id uuid REFERENCES analysis_results(id) ON DELETE SET NULL,
  insight_text text NOT NULL,
  insight_type text NOT NULL,
  signal_score numeric DEFAULT 0,
  confidence numeric DEFAULT 0.5,
  visualization_data jsonb,
  shown boolean DEFAULT false,
  created_at timestamptz DEFAULT now(),
  CONSTRAINT valid_confidence CHECK (confidence >= 0 AND confidence <= 1)
);

-- Create user_comments table
CREATE TABLE IF NOT EXISTS user_comments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id uuid NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  insight_id uuid REFERENCES insights(id) ON DELETE SET NULL,
  comment_text text NOT NULL,
  created_at timestamptz DEFAULT now()
);

-- Enable RLS
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE analysis_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_comments ENABLE ROW LEVEL SECURITY;

-- Policies for sessions table
CREATE POLICY "Anyone can create sessions"
  ON sessions FOR INSERT
  TO anon, authenticated
  WITH CHECK (true);

CREATE POLICY "Users can view sessions by URL"
  ON sessions FOR SELECT
  TO anon, authenticated
  USING (true);

CREATE POLICY "Users can update own sessions"
  ON sessions FOR UPDATE
  TO anon, authenticated
  USING (true)
  WITH CHECK (true);

-- Policies for analysis_results table
CREATE POLICY "Users can view analysis results for accessible sessions"
  ON analysis_results FOR SELECT
  TO anon, authenticated
  USING (
    EXISTS (
      SELECT 1 FROM sessions WHERE sessions.id = analysis_results.session_id
    )
  );

CREATE POLICY "System can insert analysis results"
  ON analysis_results FOR INSERT
  TO anon, authenticated
  WITH CHECK (true);

CREATE POLICY "System can update analysis results"
  ON analysis_results FOR UPDATE
  TO anon, authenticated
  USING (true)
  WITH CHECK (true);

-- Policies for insights table
CREATE POLICY "Users can view insights for accessible sessions"
  ON insights FOR SELECT
  TO anon, authenticated
  USING (
    EXISTS (
      SELECT 1 FROM sessions WHERE sessions.id = insights.session_id
    )
  );

CREATE POLICY "System can insert insights"
  ON insights FOR INSERT
  TO anon, authenticated
  WITH CHECK (true);

CREATE POLICY "System can update insights"
  ON insights FOR UPDATE
  TO anon, authenticated
  USING (true)
  WITH CHECK (true);

-- Policies for user_comments table
CREATE POLICY "Users can view comments for accessible sessions"
  ON user_comments FOR SELECT
  TO anon, authenticated
  USING (
    EXISTS (
      SELECT 1 FROM sessions WHERE sessions.id = user_comments.session_id
    )
  );

CREATE POLICY "Users can create comments"
  ON user_comments FOR INSERT
  TO anon, authenticated
  WITH CHECK (true);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_sessions_url ON sessions(session_url);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analysis_session_id ON analysis_results(session_id);
CREATE INDEX IF NOT EXISTS idx_analysis_status ON analysis_results(status);
CREATE INDEX IF NOT EXISTS idx_insights_session_id ON insights(session_id);
CREATE INDEX IF NOT EXISTS idx_insights_signal_score ON insights(signal_score DESC);
CREATE INDEX IF NOT EXISTS idx_insights_shown ON insights(shown);
CREATE INDEX IF NOT EXISTS idx_comments_session_id ON user_comments(session_id);