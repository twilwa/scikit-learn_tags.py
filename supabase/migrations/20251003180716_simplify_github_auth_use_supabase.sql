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
    
  3. Setup
    - Enable GitHub provider in Supabase dashboard
    - Set callback URL: https://your-project.supabase.co/auth/v1/callback
    - GitHub tokens managed by Supabase automatically
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
ALTER TABLE github_repositories DROP COLUMN IF EXISTS github_connection_id;
ALTER TABLE github_repositories ADD COLUMN IF NOT EXISTS auth_user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_github_repositories_auth_user ON github_repositories(auth_user_id);

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
ALTER TABLE repo_analysis_sessions ADD COLUMN IF NOT EXISTS auth_user_id uuid REFERENCES auth.users(id);
CREATE INDEX IF NOT EXISTS idx_repo_analysis_auth_user ON repo_analysis_sessions(auth_user_id);

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