/*
  # Gamification and Leaderboard System

  1. New Tables
    - `user_profiles` - RPG-style user progression
    - `achievements` - Achievement definitions
    - `user_achievements` - Unlocked achievements
    - `leaderboard_entries` - Top 10 mysterious scoring
    - `quest_completions` - Module/quest tracking

  2. Scoring System
    - Session completions
    - KB contributions quality
    - Artifacts generated
    - Insights discovered
    - Build successes
    - Mysterious bonus multipliers

  3. Features
    - Top 10 leaderboard (mysterious scoring)
    - Achievement system
    - Level progression
    - Quest modules
*/

-- Create user_profiles table
CREATE TABLE IF NOT EXISTS user_profiles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  discord_user_id uuid REFERENCES discord_users(id) ON DELETE CASCADE,
  username text NOT NULL,
  level integer DEFAULT 1,
  experience_points integer DEFAULT 0,
  mysterious_score numeric DEFAULT 0,
  title text DEFAULT 'Novice Debugger',
  avatar_url text,
  stats jsonb DEFAULT '{
    "sessions_completed": 0,
    "kb_contributions": 0,
    "insights_discovered": 0,
    "builds_successful": 0,
    "artifacts_generated": 0,
    "voice_hours": 0,
    "repl_executions": 0
  }'::jsonb,
  metadata jsonb DEFAULT '{}'::jsonb,
  created_at timestamptz DEFAULT now(),
  last_active timestamptz DEFAULT now()
);

-- Create achievements table
CREATE TABLE IF NOT EXISTS achievements (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  achievement_key text UNIQUE NOT NULL,
  name text NOT NULL,
  description text NOT NULL,
  icon text,
  tier text NOT NULL,
  points integer NOT NULL,
  unlock_criteria jsonb NOT NULL,
  hidden boolean DEFAULT false,
  created_at timestamptz DEFAULT now(),
  CONSTRAINT valid_tier CHECK (tier IN ('bronze', 'silver', 'gold', 'platinum', 'mysterious'))
);

-- Create user_achievements table
CREATE TABLE IF NOT EXISTS user_achievements (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_profile_id uuid NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
  achievement_id uuid NOT NULL REFERENCES achievements(id) ON DELETE CASCADE,
  unlocked_at timestamptz DEFAULT now(),
  metadata jsonb DEFAULT '{}'::jsonb,
  UNIQUE(user_profile_id, achievement_id)
);

-- Create leaderboard_entries table
CREATE TABLE IF NOT EXISTS leaderboard_entries (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_profile_id uuid NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
  rank integer NOT NULL,
  mysterious_score numeric NOT NULL,
  score_breakdown jsonb DEFAULT '{}'::jsonb,
  season text DEFAULT 'eternal',
  updated_at timestamptz DEFAULT now(),
  UNIQUE(season, user_profile_id)
);

-- Create quest_completions table
CREATE TABLE IF NOT EXISTS quest_completions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_profile_id uuid NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
  quest_key text NOT NULL,
  quest_name text NOT NULL,
  completed_at timestamptz DEFAULT now(),
  completion_data jsonb DEFAULT '{}'::jsonb,
  score_awarded numeric DEFAULT 0
);

-- Enable RLS
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE achievements ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_achievements ENABLE ROW LEVEL SECURITY;
ALTER TABLE leaderboard_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE quest_completions ENABLE ROW LEVEL SECURITY;

-- Policies for user_profiles
CREATE POLICY "Anyone can view public profiles"
  ON user_profiles FOR SELECT
  TO authenticated, anon
  USING (true);

CREATE POLICY "Users can update own profile"
  ON user_profiles FOR UPDATE
  TO authenticated
  USING (discord_user_id = auth.uid()::uuid)
  WITH CHECK (discord_user_id = auth.uid()::uuid);

-- Policies for achievements
CREATE POLICY "Anyone can view achievements"
  ON achievements FOR SELECT
  TO authenticated, anon
  USING (NOT hidden OR id IN (
    SELECT achievement_id FROM user_achievements
    WHERE user_profile_id IN (
      SELECT id FROM user_profiles WHERE discord_user_id = auth.uid()::uuid
    )
  ));

-- Policies for user_achievements
CREATE POLICY "Anyone can view unlocked achievements"
  ON user_achievements FOR SELECT
  TO authenticated, anon
  USING (true);

CREATE POLICY "System can grant achievements"
  ON user_achievements FOR INSERT
  TO authenticated
  WITH CHECK (true);

-- Policies for leaderboard_entries
CREATE POLICY "Anyone can view leaderboard"
  ON leaderboard_entries FOR SELECT
  TO authenticated, anon
  USING (true);

CREATE POLICY "System can update leaderboard"
  ON leaderboard_entries FOR ALL
  TO authenticated
  USING (true)
  WITH CHECK (true);

-- Policies for quest_completions
CREATE POLICY "Users can view own quest completions"
  ON quest_completions FOR SELECT
  TO authenticated
  USING (user_profile_id IN (
    SELECT id FROM user_profiles WHERE discord_user_id = auth.uid()::uuid
  ));

CREATE POLICY "System can record quest completions"
  ON quest_completions FOR INSERT
  TO authenticated
  WITH CHECK (true);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_user_profiles_discord_user ON user_profiles(discord_user_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_mysterious_score ON user_profiles(mysterious_score DESC);
CREATE INDEX IF NOT EXISTS idx_user_profiles_level ON user_profiles(level DESC);

CREATE INDEX IF NOT EXISTS idx_achievements_key ON achievements(achievement_key);
CREATE INDEX IF NOT EXISTS idx_achievements_tier ON achievements(tier);

CREATE INDEX IF NOT EXISTS idx_user_achievements_user ON user_achievements(user_profile_id);
CREATE INDEX IF NOT EXISTS idx_user_achievements_achievement ON user_achievements(achievement_id);

CREATE INDEX IF NOT EXISTS idx_leaderboard_season_rank ON leaderboard_entries(season, rank);
CREATE INDEX IF NOT EXISTS idx_leaderboard_score ON leaderboard_entries(mysterious_score DESC);

CREATE INDEX IF NOT EXISTS idx_quest_completions_user ON quest_completions(user_profile_id);
CREATE INDEX IF NOT EXISTS idx_quest_completions_quest ON quest_completions(quest_key);

-- Insert starter achievements
INSERT INTO achievements (achievement_key, name, description, icon, tier, points, unlock_criteria, hidden) VALUES
  ('first_session', 'First Contact', 'Complete your first session', '🎯', 'bronze', 10, '{"sessions_completed": 1}', false),
  ('log_analyzer', 'Log Whisperer', 'Analyze 10 Claude Code logs', '📜', 'silver', 50, '{"sessions_completed": 10, "session_type": "log_analysis"}', false),
  ('kb_contributor', 'Knowledge Keeper', 'Contribute 5 documents to shared KB', '📚', 'silver', 75, '{"kb_contributions": 5}', false),
  ('helpful_feedback', 'Community Guide', 'Receive 50 helpful votes on your KB contributions', '⭐', 'gold', 150, '{"helpful_votes": 50}', false),
  ('voice_veteran', 'Voice Commander', 'Complete 10 voice sessions', '🎙️', 'gold', 200, '{"voice_sessions": 10}', false),
  ('build_master', 'Build Wizard', 'Successfully build 25 repositories', '🏗️', 'platinum', 500, '{"builds_successful": 25}', false),
  ('mysterious_one', '???', 'The path reveals itself to those who seek', '🌟', 'mysterious', 1000, '{"mysterious": true}', true),
  ('night_owl', 'Night Owl', 'Complete 5 sessions between 2 AM - 5 AM', '🦉', 'silver', 100, '{"late_night_sessions": 5}', false),
  ('speed_demon', 'Speed Demon', 'Complete a debugging session in under 10 minutes', '⚡', 'gold', 250, '{"fast_completion": true}', false),
  ('artifact_master', 'Artifact Collector', 'Generate 100 high-signal insights', '💎', 'platinum', 750, '{"insights_discovered": 100}', false)
ON CONFLICT (achievement_key) DO NOTHING;

-- Function to calculate mysterious score
CREATE OR REPLACE FUNCTION calculate_mysterious_score(profile_stats jsonb)
RETURNS numeric
LANGUAGE plpgsql
AS $$
DECLARE
  base_score numeric := 0;
  multiplier numeric := 1.0;
  sessions integer;
  contributions integer;
  insights integer;
  builds integer;
BEGIN
  sessions := COALESCE((profile_stats->>'sessions_completed')::integer, 0);
  contributions := COALESCE((profile_stats->>'kb_contributions')::integer, 0);
  insights := COALESCE((profile_stats->>'insights_discovered')::integer, 0);
  builds := COALESCE((profile_stats->>'builds_successful')::integer, 0);
  
  base_score := (sessions * 10) + (contributions * 25) + (insights * 5) + (builds * 50);
  
  IF sessions > 50 THEN multiplier := multiplier * 1.5; END IF;
  IF contributions > 20 THEN multiplier := multiplier * 1.3; END IF;
  IF builds > 10 THEN multiplier := multiplier * 2.0; END IF;
  
  IF (profile_stats->>'voice_hours')::numeric > 10 THEN
    multiplier := multiplier * 1.2;
  END IF;
  
  base_score := base_score * multiplier;
  
  base_score := base_score + (RANDOM() * 100);
  
  RETURN base_score;
END;
$$;

-- Function to update leaderboard
CREATE OR REPLACE FUNCTION update_leaderboard()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
  DELETE FROM leaderboard_entries WHERE season = 'eternal';
  
  INSERT INTO leaderboard_entries (user_profile_id, rank, mysterious_score, score_breakdown, season)
  SELECT 
    id,
    ROW_NUMBER() OVER (ORDER BY calculate_mysterious_score(stats) DESC),
    calculate_mysterious_score(stats),
    jsonb_build_object(
      'sessions', stats->'sessions_completed',
      'contributions', stats->'kb_contributions',
      'insights', stats->'insights_discovered',
      'builds', stats->'builds_successful'
    ),
    'eternal'
  FROM user_profiles
  ORDER BY calculate_mysterious_score(stats) DESC
  LIMIT 10;
END;
$$;