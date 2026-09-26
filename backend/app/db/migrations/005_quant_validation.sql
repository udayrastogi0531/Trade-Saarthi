-- v4.0 Quantitative Validation & Survivability

CREATE TABLE IF NOT EXISTS walk_forward_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    strategy_name VARCHAR(128) NOT NULL,
    symbol VARCHAR(32) NOT NULL,
    parameters JSONB,
    window_config JSONB NOT NULL,
    in_sample_metrics JSONB NOT NULL,
    out_of_sample_metrics JSONB NOT NULL,
    rolling_metrics JSONB,
    stability_score DECIMAL(8, 4),
    overfitting_flag BOOLEAN DEFAULT FALSE,
    decay_detected BOOLEAN DEFAULT FALSE,
    regime_breakdown JSONB,
    report JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_wf_strategy ON walk_forward_runs(strategy_name, created_at DESC);

CREATE TABLE IF NOT EXISTS monte_carlo_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id INTEGER REFERENCES accounts(id),
    strategy_name VARCHAR(128),
    simulations INTEGER NOT NULL DEFAULT 1000,
    config JSONB NOT NULL,
    probability_of_ruin DECIMAL(8, 6),
    worst_drawdown_pct DECIMAL(8, 4),
    expected_drawdown_pct DECIMAL(8, 4),
    survival_probability DECIMAL(8, 6),
    tail_risk_var_99 DECIMAL(8, 4),
    drawdown_distribution JSONB,
    stress_scenarios JSONB,
    report JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id INTEGER NOT NULL REFERENCES accounts(id),
    positions JSONB NOT NULL DEFAULT '[]',
    sector_exposure JSONB,
    correlation_matrix JSONB,
    var_95 DECIMAL(12, 4),
    var_99 DECIMAL(12, 4),
    portfolio_heat DECIMAL(8, 4),
    beta_exposure DECIMAL(8, 4),
    concentration_risk JSONB,
    risk_score DECIMAL(8, 4),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_portfolio_account ON portfolio_snapshots(account_id, created_at DESC);

CREATE TABLE IF NOT EXISTS strategy_research_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_type VARCHAR(64) NOT NULL,
    scope JSONB,
    findings JSONB NOT NULL,
    evidence JSONB NOT NULL,
    uncertainty_notes TEXT,
    ai_summary TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS execution_quality_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    trade_id UUID REFERENCES trades(id),
    order_id VARCHAR(128),
    symbol VARCHAR(32),
    expected_price DECIMAL(18, 4),
    fill_price DECIMAL(18, 4),
    slippage_bps DECIMAL(8, 4),
    latency_ms INTEGER,
    partial_fill BOOLEAN DEFAULT FALSE,
    rejected BOOLEAN DEFAULT FALSE,
    rejection_reason TEXT,
    spread_bps DECIMAL(8, 4),
    simulated BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS regime_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    strategy_name VARCHAR(128),
    setup_type VARCHAR(64),
    regime VARCHAR(32) NOT NULL,
    trade_count INTEGER DEFAULT 0,
    win_rate DECIMAL(8, 4),
    expectancy DECIMAL(12, 4),
    avg_pnl DECIMAL(12, 4),
    sharpe DECIMAL(8, 4),
    confidence_adjustment DECIMAL(6, 4) DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(strategy_name, setup_type, regime)
);

CREATE TABLE IF NOT EXISTS data_quality_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(32),
    provider VARCHAR(32),
    event_type VARCHAR(64) NOT NULL,
    severity VARCHAR(16) NOT NULL,
    details JSONB,
    feed_healthy BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_dq_symbol ON data_quality_events(symbol, created_at DESC);

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    actor VARCHAR(128),
    action VARCHAR(128) NOT NULL,
    resource VARCHAR(256),
    details JSONB,
    ip_address VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS capital_safety_state (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id) UNIQUE,
    deployment_stage VARCHAR(32) DEFAULT 'sandbox',
    max_live_capital DECIMAL(18, 2),
    human_approval_required BOOLEAN DEFAULT TRUE,
    emergency_shutdown BOOLEAN DEFAULT FALSE,
    shutdown_reason TEXT,
    daily_loss_limit_pct DECIMAL(8, 4) DEFAULT 1.0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS edge_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    setup_type VARCHAR(64) NOT NULL,
    regime VARCHAR(32),
    rolling_expectancy DECIMAL(12, 4),
    rolling_win_rate DECIMAL(8, 4),
    rolling_sharpe DECIMAL(8, 4),
    edge_status VARCHAR(32),
    sample_size INTEGER,
    window_days INTEGER DEFAULT 30,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
