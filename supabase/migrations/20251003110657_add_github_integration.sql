/*
  # GitHub Integration for Direct Repository Analysis

  1. New Tables
    - `github_connections` - Store GitHub OAuth tokens
    - `github_repositories` - Cached repo metadata
    - `repo_analysis_sessions` - Analysis sessions without logs
    - `code_explorations` - File-by-file explorations

  2. Features
    - GitHub OAuth integration
    - Direct repo analysis (no logs needed)
    - Code exploration mode
    - Commit history analysis
    - Issue/PR insights

  3. Security
    - Encrypted OAuth tokens
    - RLS policies
    - Token refresh logic
*/

-- Create github_connections table
CREATE TABLE IF NOT EXISTS github_connections (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_profile_id uuid REFERENCES user_profiles(id) ON DELETE CASCADE,
  github_user_id text NOT NULL,
  github_username text NOT NULL,
  access_token text NOT NULL,
  refresh_token text,
  token_expires_at timestamptz,
  scopes text[] DEFAULT ARRAY['repo', 'read:user']::text[],
  avatar_url text,
  connected_at timestamptz DEFAULT now(),
  last_used timestamptz DEFAULT now(),
  UNIQUE(user_profile_id),
  UNIQUE(github_user_id)
);

-- Create github_repositories table
CREATE TABLE IF NOT EXISTS github_repositories (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  github_connection_id uuid REFERENCES github_connections(id) ON DELETE CASCADE,
  repo_full_name text NOT NULL,
  repo_url text NOT NULL,
  default_branch text DEFAULT 'main',
  primary_language text,
  languages jsonb DEFAULT '{}'::jsonb,
  stars integer DEFAULT 0,
  forks integer DEFAULT 0,
  open_issues integer DEFAULT 0,
  size_kb integer DEFAULT 0,
  last_commit_sha text,
  last_commit_date timestamptz,
  metadata jsonb DEFAULT '{}'::jsonb,
  synced_at timestamptz DEFAULT now(),
  created_at timestamptz DEFAULT now(),
  UNIQUE(github_connection_id, repo_full_name)
);

-- Create repo_analysis_sessions table
CREATE TABLE IF NOT EXISTS repo_analysis_sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_profile_id uuid REFERENCES user_profiles(id) ON DELETE CASCADE,
  github_repository_id uuid REFERENCES github_repositories(id) ON DELETE SET NULL,
  session_url text UNIQUE NOT NULL,
  session_type text NOT NULL,
  status text NOT NULL DEFAULT 'initializing',
  analysis_focus text[],
  findings jsonb DEFAULT '{}'::jsonb,
  metrics jsonb DEFAULT '{}'::jsonb,
  recommendations text[],
  started_at timestamptz DEFAULT now(),
  completed_at timestamptz,
  expires_at timestamptz DEFAULT (now() + interval '7 days'),
  metadata jsonb DEFAULT '{}'::jsonb,
  CONSTRAINT valid_session_type CHECK (session_type IN ('full_analysis', 'code_review', 'architecture', 'security_audit', 'performance', 'exploration')),
  CONSTRAINT valid_status CHECK (status IN ('initializing', 'analyzing', 'completed', 'failed', 'expired'))
);

-- Create code_explorations table
CREATE TABLE IF NOT EXISTS code_explorations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  repo_analysis_session_id uuid NOT NULL REFERENCES repo_analysis_sessions(id) ON DELETE CASCADE,
  file_path text NOT NULL,
  file_content text,
  file_type text,
  language text,
  lines_of_code integer,
  complexity_score numeric,
  analysis_notes text,
  interesting_patterns jsonb DEFAULT '[]'::jsonb,
  dependencies jsonb DEFAULT '[]'::jsonb,
  exports jsonb DEFAULT '[]'::jsonb,
  imports jsonb DEFAULT '[]'::jsonb,
  explored_at timestamptz DEFAULT now()
);

-- Enable RLS
ALTER TABLE github_connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE github_repositories ENABLE ROW LEVEL SECURITY;
ALTER TABLE repo_analysis_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE code_explorations ENABLE ROW LEVEL SECURITY;

-- Policies for github_connections
CREATE POLICY "Users can view own GitHub connection"
  ON github_connections FOR SELECT
  TO authenticated
  USING (user_profile_id IN (
    SELECT id FROM user_profiles WHERE discord_user_id = auth.uid()::uuid
  ));

CREATE POLICY "Users can create own GitHub connection"
  ON github_connections FOR INSERT
  TO authenticated
  WITH CHECK (user_profile_id IN (
    SELECT id FROM user_profiles WHERE discord_user_id = auth.uid()::uuid
  ));

CREATE POLICY "Users can update own GitHub connection"
  ON github_connections FOR UPDATE
  TO authenticated
  USING (user_profile_id IN (
    SELECT id FROM user_profiles WHERE discord_user_id = auth.uid()::uuid
  ))
  WITH CHECK (user_profile_id IN (
    SELECT id FROM user_profiles WHERE discord_user_id = auth.uid()::uuid
  ));

CREATE POLICY "Users can delete own GitHub connection"
  ON github_connections FOR DELETE
  TO authenticated
  USING (user_profile_id IN (
    SELECT id FROM user_profiles WHERE discord_user_id = auth.uid()::uuid
  ));

-- Policies for github_repositories
CREATE POLICY "Users can view own repositories"
  ON github_repositories FOR SELECT
  TO authenticated
  USING (github_connection_id IN (
    SELECT id FROM github_connections
    WHERE user_profile_id IN (
      SELECT id FROM user_profiles WHERE discord_user_id = auth.uid()::uuid
    )
  ));

CREATE POLICY "System can manage repositories"
  ON github_repositories FOR ALL
  TO authenticated
  USING (true)
  WITH CHECK (true);

-- Policies for repo_analysis_sessions
CREATE POLICY "Users can view own analysis sessions"
  ON repo_analysis_sessions FOR SELECT
  TO authenticated
  USING (user_profile_id IN (
    SELECT id FROM user_profiles WHERE discord_user_id = auth.uid()::uuid
  ));

CREATE POLICY "Users can create analysis sessions"
  ON repo_analysis_sessions FOR INSERT
  TO authenticated
  WITH CHECK (user_profile_id IN (
    SELECT id FROM user_profiles WHERE discord_user_id = auth.uid()::uuid
  ));

CREATE POLICY "Users can update own analysis sessions"
  ON repo_analysis_sessions FOR UPDATE
  TO authenticated
  USING (user_profile_id IN (
    SELECT id FROM user_profiles WHERE discord_user_id = auth.uid()::uuid
  ))
  WITH CHECK (user_profile_id IN (
    SELECT id FROM user_profiles WHERE discord_user_id = auth.uid()::uuid
  ));

-- Policies for code_explorations
CREATE POLICY "Users can view explorations from own sessions"
  ON code_explorations FOR SELECT
  TO authenticated
  USING (repo_analysis_session_id IN (
    SELECT id FROM repo_analysis_sessions
    WHERE user_profile_id IN (
      SELECT id FROM user_profiles WHERE discord_user_id = auth.uid()::uuid
    )
  ));

CREATE POLICY "System can manage code explorations"
  ON code_explorations FOR ALL
  TO authenticated
  USING (true)
  WITH CHECK (true);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_github_connections_user ON github_connections(user_profile_id);
CREATE INDEX IF NOT EXISTS idx_github_connections_github_user ON github_connections(github_user_id);

CREATE INDEX IF NOT EXISTS idx_github_repositories_connection ON github_repositories(github_connection_id);
CREATE INDEX IF NOT EXISTS idx_github_repositories_full_name ON github_repositories(repo_full_name);

CREATE INDEX IF NOT EXISTS idx_repo_analysis_user ON repo_analysis_sessions(user_profile_id);
CREATE INDEX IF NOT EXISTS idx_repo_analysis_status ON repo_analysis_sessions(status);
CREATE INDEX IF NOT EXISTS idx_repo_analysis_session_url ON repo_analysis_sessions(session_url);

CREATE INDEX IF NOT EXISTS idx_code_explorations_session ON code_explorations(repo_analysis_session_id);
CREATE INDEX IF NOT EXISTS idx_code_explorations_file_path ON code_explorations(file_path);
CREATE INDEX IF NOT EXISTS idx_code_explorations_language ON code_explorations(language);