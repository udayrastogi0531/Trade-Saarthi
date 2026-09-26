-- v4.0.2 operational broker tokens

CREATE TABLE IF NOT EXISTS broker_tokens (
    id SERIAL PRIMARY KEY,
    broker VARCHAR(32) NOT NULL,
    account_id INTEGER REFERENCES accounts(id),
    access_token TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_broker_tokens_broker_created
ON broker_tokens (broker, created_at DESC);
