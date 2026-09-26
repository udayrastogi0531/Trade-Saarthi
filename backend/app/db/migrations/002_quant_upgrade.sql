-- Quant platform upgrade — v2 schema extensions

-- Market regime snapshots
CREATE TABLE IF NOT EXISTS market_regimes (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(32) NOT NULL,
    exchange VARCHAR(8) NOT NULL DEFAULT 'NSE',
    regime VARCHAR(32) NOT NULL,
    confidence DECIMAL(5, 2) NOT NULL,
    metrics JSONB,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_market_regimes_symbol ON market_regimes(symbol, recorded_at DESC);

-- Scanner runs
CREATE TABLE IF NOT EXISTS scanner_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id UUID NOT NULL,
    symbol VARCHAR(32) NOT NULL,
    approved BOOLEAN NOT NULL DEFAULT FALSE,
    quality_score DECIMAL(5, 2),
    mtf_alignment_score DECIMAL(5, 4),
    regime VARCHAR(32),
    rank_score DECIMAL(8, 4),
    signal_id UUID REFERENCES signals(id),
    rejection_reasons JSONB DEFAULT '[]',
    duration_ms INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_scanner_logs_run ON scanner_logs(run_id, created_at DESC);

-- Watchlists
CREATE TABLE IF NOT EXISTS watchlists (
    id SERIAL PRIMARY KEY,
    name VARCHAR(64) NOT NULL UNIQUE,
    symbols JSONB NOT NULL DEFAULT '[]',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    scan_interval_minutes INTEGER NOT NULL DEFAULT 3,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO watchlists (name, symbols, scan_interval_minutes)
SELECT 'default', '["RELIANCE","TCS","INFY","HDFCBANK","NIFTY"]'::jsonb, 3
WHERE NOT EXISTS (SELECT 1 FROM watchlists WHERE name = 'default');

-- Trade journal / analytics
CREATE TABLE IF NOT EXISTS trade_journal (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trade_id UUID REFERENCES trades(id) ON DELETE CASCADE,
    setup_type VARCHAR(64),
    strategy_name VARCHAR(64),
    ai_confidence DECIMAL(5, 2),
    quality_score DECIMAL(5, 2),
    market_regime VARCHAR(32),
    outcome VARCHAR(16),
    mfe DECIMAL(18, 4),
    mae DECIMAL(18, 4),
    emotional_override BOOLEAN NOT NULL DEFAULT FALSE,
    notes TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Portfolio exposure tracking
CREATE TABLE IF NOT EXISTS portfolio_exposure (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id),
    sector VARCHAR(64) NOT NULL,
    symbol VARCHAR(32) NOT NULL,
    exposure_pct DECIMAL(8, 4) NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Strategy performance aggregates
CREATE TABLE IF NOT EXISTS strategy_performance (
    id SERIAL PRIMARY KEY,
    strategy_name VARCHAR(64) NOT NULL,
    setup_type VARCHAR(64),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    trade_count INTEGER NOT NULL DEFAULT 0,
    win_rate DECIMAL(5, 2),
    expectancy DECIMAL(12, 4),
    profit_factor DECIMAL(8, 4),
    sharpe_ratio DECIMAL(8, 4),
    max_drawdown_pct DECIMAL(8, 4),
    metrics JSONB,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (strategy_name, setup_type, period_start, period_end)
);

-- AI explanations archive
CREATE TABLE IF NOT EXISTS ai_explanations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_type VARCHAR(32) NOT NULL,
    source_id UUID,
    model VARCHAR(64),
    prompt_hash VARCHAR(64),
    response JSONB NOT NULL,
    latency_ms INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Chart analysis uploads
CREATE TABLE IF NOT EXISTS chart_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(32),
    file_path VARCHAR(512),
    analysis JSONB NOT NULL,
    risk_assessment JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Extend signals with quality metrics
ALTER TABLE signals ADD COLUMN IF NOT EXISTS quality_score DECIMAL(5, 2);
ALTER TABLE signals ADD COLUMN IF NOT EXISTS mtf_alignment_score DECIMAL(5, 4);
ALTER TABLE signals ADD COLUMN IF NOT EXISTS market_regime VARCHAR(32);
ALTER TABLE signals ADD COLUMN IF NOT EXISTS rank_score DECIMAL(8, 4);

-- Sector mapping reference
CREATE TABLE IF NOT EXISTS symbol_sectors (
    symbol VARCHAR(32) PRIMARY KEY,
    sector VARCHAR(64) NOT NULL
);

INSERT INTO symbol_sectors (symbol, sector) VALUES
    ('RELIANCE', 'Energy'),
    ('TCS', 'IT'),
    ('INFY', 'IT'),
    ('HDFCBANK', 'Financials'),
    ('NIFTY', 'Index')
ON CONFLICT (symbol) DO NOTHING;
