-- Copilot sessions & conversational memory

CREATE TABLE IF NOT EXISTS copilot_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id INTEGER REFERENCES accounts(id) DEFAULT 1,
    language VARCHAR(16) NOT NULL DEFAULT 'hinglish',
    title VARCHAR(256),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS copilot_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES copilot_sessions(id) ON DELETE CASCADE,
    role VARCHAR(16) NOT NULL,
    content TEXT NOT NULL,
    language VARCHAR(16),
    intent VARCHAR(64),
    audio_url VARCHAR(512),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_copilot_messages_session ON copilot_messages(session_id, created_at);

CREATE TABLE IF NOT EXISTS voice_alerts (
    id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES accounts(id),
    alert_type VARCHAR(32) NOT NULL,
    message TEXT NOT NULL,
    language VARCHAR(16) DEFAULT 'hinglish',
    delivered BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
