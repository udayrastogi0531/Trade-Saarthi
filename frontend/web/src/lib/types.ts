export type ObservabilityHealth = {
  status: string;
  version?: string;
  redis: boolean;
  scanner_health: string;
  scanner_last_latency_ms?: number | null;
  scanner_queue_depth?: number | null;
  execution_quality_score?: number;
  conservative_mode?: boolean;
  paper_trading?: boolean;
  execution_enabled?: boolean;
  data_quality_issues?: number;
  data_quality_recent?: Array<{
    symbol: string | null;
    event_type: string;
    severity: string;
    feed_healthy: boolean;
    created_at: string | null;
  }>;
  operational_alerts?: string[];
  governance?: { architecture_frozen: boolean; mode: string };
  disclaimer?: string;
};

export type ScorecardRow = {
  setup_type: string;
  regime: string;
  trade_count: number;
  win_rate_pct: number;
  expectancy: number;
  false_breakout_rate: number;
  avg_confidence: number;
  decay_score: number;
  stability_score: number;
  edge_quality: string;
};

export type RegimeSummaryRow = {
  regime: string;
  setup_count: number;
  trade_count: number;
  avg_win_rate_pct: number;
  avg_expectancy: number;
  survivability: string;
};

export type ScorecardsResponse = {
  scorecards: ScorecardRow[];
  regime_summary?: RegimeSummaryRow[];
  signal_analytics: {
    approved: number;
    rejected: number;
    false_positive_proxy_pct: number;
    note?: string;
  };
  recent_walk_forward?: Array<{
    id: string;
    symbol: string;
    stability: number;
    overfitting: boolean;
    decay: boolean;
  }>;
};

export type VolatilityContext = {
  dominant_regime: string;
  warnings: string[];
  momentum_exhaustion_note?: string | null;
  confidence_reduction_suggested?: boolean;
  disclaimer?: string;
};
