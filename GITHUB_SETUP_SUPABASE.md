/*
  # Simplify GitHub Integration with Supabase Auth

  1. Changes
    - Remove custom github_connections table
    - Link user_profiles to auth.users
    - Use Supabase's built-in OAuth handling
    - Keep github_repositories for caching
    - Update repo_analysis_sessions to reference auth_user_id

  2. Benefits
    - Less code to maintain
    - Automatic token refresh
    - Built-in security
    - Standard auth flow
*/

-- Drop old github_connections table if exists
DROP TABLE IF EXISTS github_connections CASCADE;

-- Add auth_user_id to user_profiles if not exists
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'user_profiles' AND column_name = 'auth_user_id'
  ) THEN
    ALTER TABLE user_profiles ADD COLUMN auth_user_id uuid REFERENCES auth.users(id);
    CREATE INDEX IF NOT EXISTS idx_user_profiles_auth_user ON user_profiles(auth_user_id);
  END IF;
END $$;

-- Update github_repositories to reference auth_user_id directly
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'github_repositories' AND column_name = 'github_connection_id'
  ) THEN
    ALTER TABLE github_repositories DROP COLUMN github_connection_id;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'github_repositories' AND column_name = 'auth_user_id'
  ) THEN
    ALTER TABLE github_repositories ADD COLUMN auth_user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE;
    CREATE INDEX IF NOT EXISTS idx_github_repositories_auth_user ON github_repositories(auth_user_id);
  END IF;
END $$;

-- Update RLS policies for github_repositories
DROP POLICY IF EXISTS "Users can view own repositories" ON github_repositories;
DROP POLICY IF EXISTS "System can manage repositories" ON github_repositories;

CREATE POLICY "Users can view own repositories"
  ON github_repositories FOR SELECT
  TO authenticated
  USING (auth_user_id = auth.uid());

CREATE POLICY "Users can insert own repositories"
  ON github_repositories FOR INSERT
  TO authenticated
  WITH CHECK (auth_user_id = auth.uid());

CREATE POLICY "Users can update own repositories"
  ON github_repositories FOR UPDATE
  TO authenticated
  USING (auth_user_id = auth.uid())
  WITH CHECK (auth_user_id = auth.uid());

CREATE POLICY "Users can delete own repositories"
  ON github_repositories FOR DELETE
  TO authenticated
  USING (auth_user_id = auth.uid());

-- Update repo_analysis_sessions to use auth_user_id
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'repo_analysis_sessions' AND column_name = 'auth_user_id'
  ) THEN
    ALTER TABLE repo_analysis_sessions ADD COLUMN auth_user_id uuid REFERENCES auth.users(id);
    CREATE INDEX IF NOT EXISTS idx_repo_analysis_auth_user ON repo_analysis_sessions(auth_user_id);
  END IF;
END $$;

-- Update RLS for repo_analysis_sessions
DROP POLICY IF EXISTS "Users can view own analysis sessions" ON repo_analysis_sessions;
DROP POLICY IF EXISTS "Users can create analysis sessions" ON repo_analysis_sessions;
DROP POLICY IF EXISTS "Users can update own analysis sessions" ON repo_analysis_sessions;

CREATE POLICY "Users can view own analysis sessions"
  ON repo_analysis_sessions FOR SELECT
  TO authenticated
  USING (
    auth_user_id = auth.uid() OR
    user_profile_id IN (
      SELECT id FROM user_profiles WHERE auth_user_id = auth.uid()
    )
  );

CREATE POLICY "Users can create analysis sessions"
  ON repo_analysis_sessions FOR INSERT
  TO authenticated
  WITH CHECK (
    auth_user_id = auth.uid() OR
    user_profile_id IN (
      SELECT id FROM user_profiles WHERE auth_user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update own analysis sessions"
  ON repo_analysis_sessions FOR UPDATE
  TO authenticated
  USING (
    auth_user_id = auth.uid() OR
    user_profile_id IN (
      SELECT id FROM user_profiles WHERE auth_user_id = auth.uid()
    )
  )
  WITH CHECK (
    auth_user_id = auth.uid() OR
    user_profile_id IN (
      SELECT id FROM user_profiles WHERE auth_user_id = auth.uid()
    )
  );