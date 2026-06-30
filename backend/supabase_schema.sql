-- ================================================================
-- Off The Mic — Supabase Database Schema
-- Run this entire file in:
--   Supabase Dashboard → SQL Editor → New Query → Paste → Run
-- ================================================================


-- ── 1. USERS ────────────────────────────────────────────────────
-- Stores registered users (managed by our Flask backend, NOT Supabase Auth)
CREATE TABLE IF NOT EXISTS users (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email         TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  display_name  TEXT NOT NULL,
  created_at    TIMESTAMPTZ DEFAULT now(),
  last_login    TIMESTAMPTZ,
  streak        INTEGER DEFAULT 0,
  sessions      INTEGER DEFAULT 0
);


-- ── 2. OTPs ─────────────────────────────────────────────────────
-- Stores one-time passwords for login verification
CREATE TABLE IF NOT EXISTS otps (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  otp_code   TEXT NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  used       BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Auto-delete OTPs older than 1 hour (keeps table clean)
CREATE INDEX IF NOT EXISTS idx_otps_user_id   ON otps(user_id);
CREATE INDEX IF NOT EXISTS idx_otps_expires_at ON otps(expires_at);


-- ── 3. LEARNED WORDS ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS learned_words (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  word       TEXT NOT NULL,
  learned_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(user_id, word)
);

CREATE INDEX IF NOT EXISTS idx_learned_words_user ON learned_words(user_id);


-- ── 4. SAVED TOPICS ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS saved_topics (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  topic      TEXT NOT NULL,
  category   TEXT,
  difficulty TEXT,
  saved_at   TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_saved_topics_user ON saved_topics(user_id);


-- ── 5. SAVED ANSWERS ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS saved_answers (
  id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id  UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  question TEXT NOT NULL,
  answer   TEXT NOT NULL,
  type     TEXT,
  saved_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_saved_answers_user ON saved_answers(user_id);


-- ================================================================
-- ROW LEVEL SECURITY (RLS)
-- The backend uses the service_role key which bypasses RLS,
-- so these policies protect against direct client-side access.
-- ================================================================

-- ALTER TABLE users         ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE otps          ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE learned_words ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE saved_topics  ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE saved_answers ENABLE ROW LEVEL SECURITY;

-- Block all direct client access (backend service_role bypasses this)
-- CREATE POLICY "No direct client access" ON users         FOR ALL USING (false);
-- CREATE POLICY "No direct client access" ON otps          FOR ALL USING (false);
-- CREATE POLICY "No direct client access" ON learned_words FOR ALL USING (false);
-- CREATE POLICY "No direct client access" ON saved_topics  FOR ALL USING (false);
-- CREATE POLICY "No direct client access" ON saved_answers FOR ALL USING (false);



-- ================================================================
-- DONE. Your database is ready.
-- ================================================================
