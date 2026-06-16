-- Supabase Schema Initialization for EduLingo

-- 1. Learner Profiles Table
CREATE TABLE IF NOT EXISTS learner_profiles (
    learner_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    current_level TEXT DEFAULT 'A1',
    target_level TEXT DEFAULT 'B2',
    learning_goals JSONB DEFAULT '[]'::jsonb,
    weak_areas JSONB DEFAULT '[]'::jsonb,
    preferred_topics JSONB DEFAULT '[]'::jsonb,
    sessions_completed INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- 2. Sessions Table (for Progress Tracking)
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    learner_id TEXT REFERENCES learner_profiles(learner_id) ON DELETE CASCADE,
    session_id TEXT NOT NULL,
    session_type TEXT NOT NULL,
    duration_mins INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- 3. Feedback History Table (for Progress Analytics)
CREATE TABLE IF NOT EXISTS feedback_history (
    id TEXT PRIMARY KEY,
    learner_id TEXT REFERENCES learner_profiles(learner_id) ON DELETE CASCADE,
    session_id TEXT NOT NULL,
    grammar_score NUMERIC DEFAULT 0,
    vocabulary_score NUMERIC DEFAULT 0,
    clarity_score NUMERIC DEFAULT 0,
    job_readiness_score NUMERIC DEFAULT 0,
    corrections JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- 4. Session Memory Table (Long-term memory - Task 10)
CREATE TABLE IF NOT EXISTS session_memory (
    id TEXT PRIMARY KEY,
    learner_id TEXT REFERENCES learner_profiles(learner_id) ON DELETE CASCADE,
    session_id TEXT NOT NULL UNIQUE,
    agent_state JSONB NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- 5. Disable Row Level Security (RLS) to allow anonymous read/write access via public anon key
ALTER TABLE learner_profiles DISABLE ROW LEVEL SECURITY;
ALTER TABLE sessions DISABLE ROW LEVEL SECURITY;
ALTER TABLE feedback_history DISABLE ROW LEVEL SECURITY;
ALTER TABLE session_memory DISABLE ROW LEVEL SECURITY;
