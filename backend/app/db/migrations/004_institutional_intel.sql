-- v2.2 Institutional Market Intelligence

CREATE TABLE IF NOT EXISTS market_structure_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(32) NOT NULL,
    timeframe VARCHAR(8) NOT NULL DEFAULT '15m',
    structure_type VARCHAR(32),
    trend_quality DECIMAL(5, 4),
    structure_confidence DECIMAL(5, 2),
    bos_detected BOOLEAN DEFAULT FALSE,
    choch_detected BOOLEAN DEFAULT FALSE,
    liquidity_sweep BOOLEAN DEFAULT FALSE,
    fake_breakout_risk DECIMAL(5, 4),
    zones JSONB,
    analysis JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_structure_symbol ON market_structure_snapshots(symbol, created_at DESC);

CREATE TABLE IF NOT EXISTS setup_performance (
    id SERIAL PRIMARY KEY,
    setup_type VARCHAR(64) NOT NULL,
    market_regime VARCHAR(32),
    trade_count INTEGER NOT NULL DEFAULT 0,
    win_count INTEGER NOT NULL DEFAULT 0,
    avg_confidence DECIMAL(5, 2),
    avg_ai_accuracy DECIMAL(5, 4),
    false_breakout_rate DECIMAL(5, 4),
    expectancy DECIMAL(12, 4),
    last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (setup_type, market_regime)
);

CREATE TABLE IF NOT EXISTS signal_outcomes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    signal_id UUID REFERENCES signals(id),
    setup_type VARCHAR(64),
    market_regime VARCHAR(32),
    ai_confidence DECIMAL(5, 2),
    structure_confidence DECIMAL(5, 2),
    approved BOOLEAN,
    outcome VARCHAR(16),
    pnl DECIMAL(18, 2),
    false_breakout BOOLEAN DEFAULT FALSE,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS market_briefings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    briefing_type VARCHAR(32) NOT NULL,
    content TEXT NOT NULL,
    summary JSONB,
    language VARCHAR(16) DEFAULT 'hinglish',
    voice_delivered BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS scanner_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id UUID NOT NULL UNIQUE,
    symbols_scanned INTEGER NOT NULL,
    approved_count INTEGER NOT NULL,
    avg_latency_ms DECIMAL(10, 2),
    health_status VARCHAR(16) DEFAULT 'ok',
    errors JSONB DEFAULT '[]',
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS execution_safety_log (
    id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES accounts(id),
    check_type VARCHAR(64) NOT NULL,
    passed BOOLEAN NOT NULL,
    details JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE trade_journal ADD COLUMN IF NOT EXISTS screenshot_path VARCHAR(512);
ALTER TABLE trade_journal ADD COLUMN IF NOT EXISTS trade_reasoning TEXT;
ALTER TABLE trade_journal ADD COLUMN IF NOT EXISTS execution_quality VARCHAR(32);
ALTER TABLE trade_journal ADD COLUMN IF NOT EXISTS duration_minutes INTEGER;
ALTER TABLE scanner_logs ADD COLUMN IF NOT EXISTS structure_score DECIMAL(5, 2);
ALTER TABLE scanner_logs ADD COLUMN IF NOT EXISTS latency_ms INTEGER;
