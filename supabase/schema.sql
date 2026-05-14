CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Voice sessions
CREATE TABLE IF NOT EXISTS voice_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  scenario_name TEXT,
  status TEXT DEFAULT 'active',
  active_language TEXT DEFAULT 'en',
  total_turns INT DEFAULT 0
);

-- Conversation messages
CREATE TABLE IF NOT EXISTS conversation_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id TEXT NOT NULL,
  turn_number INT,
  role TEXT,
  transcript TEXT,
  detected_language TEXT,
  response_language TEXT,
  response_text TEXT,
  latency_ms FLOAT,
  memory_snapshot JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conv_messages_session ON conversation_messages(session_id);

-- Language switch events
CREATE TABLE IF NOT EXISTS language_switch_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id TEXT NOT NULL,
  turn_number INT,
  from_language TEXT,
  to_language TEXT,
  confidence FLOAT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_lang_switch_session ON language_switch_events(session_id);

-- Latency logs
CREATE TABLE IF NOT EXISTS latency_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id TEXT NOT NULL,
  turn_number INT,
  audio_upload_ms FLOAT,
  asr_ms FLOAT,
  language_detection_ms FLOAT,
  memory_update_ms FLOAT,
  tool_ms FLOAT,
  llm_ms FLOAT,
  total_ms FLOAT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_latency_logs_session ON latency_logs(session_id);

-- Scenario runs
CREATE TABLE IF NOT EXISTS scenario_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id TEXT,
  scenario_name TEXT,
  passed_language_switch BOOLEAN,
  passed_memory_check BOOLEAN,
  passed_response_language BOOLEAN,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
