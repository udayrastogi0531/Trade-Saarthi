"""Prometheus metrics for observability."""

from prometheus_client import Counter, Gauge, Histogram

SIGNALS_APPROVED = Counter("trading_signals_approved_total", "Approved signals")
SIGNALS_REJECTED = Counter("trading_signals_rejected_total", "Rejected signals")
SCANNER_RUNS = Counter("trading_scanner_runs_total", "Scanner runs completed")
AI_REQUESTS = Counter("trading_ai_requests_total", "AI reasoning requests")
AI_LATENCY = Histogram("trading_ai_latency_seconds", "AI reasoning latency (trade analysis path)")
PIPELINE_LATENCY = Histogram("trading_pipeline_latency_seconds", "Full pipeline latency")
SCANNER_LATENCY = Histogram("trading_scanner_latency_seconds", "Scanner run latency")
SCANNER_SYMBOL_LATENCY = Histogram(
  "trading_scanner_symbol_latency_seconds", "Per-symbol scan latency", ["symbol"]
)
SCANNER_ERRORS = Counter("trading_scanner_symbol_errors_total", "Symbol scan failures", ["symbol"])
COPILOT_MESSAGES = Counter("trading_copilot_messages_total", "Copilot messages", ["role"])
COPILOT_WS_CONNECTIONS = Counter("trading_copilot_ws_connections_total", "WebSocket connections")

# v4.0 observability
VALIDATION_RUNS = Counter("trading_validation_runs_total", "Validation runs", ["type"])
DATA_QUALITY_EVENTS = Counter("trading_data_quality_events_total", "Data quality events", ["severity"])
EXECUTION_FAILURES = Counter("trading_execution_failures_total", "Execution failures")
STRATEGY_DECAY_ALERTS = Counter("trading_strategy_decay_alerts_total", "Strategy decay detections")
PORTFOLIO_RISK_BLOCKS = Counter("trading_portfolio_risk_blocks_total", "Portfolio-level blocks")

# Stabilization — queue depth & WS health
SCANNER_QUEUE_DEPTH = Gauge("trading_scanner_queue_depth", "Scanner Redis job queue length")
WS_HEARTBEATS = Counter("trading_ws_heartbeat_total", "WebSocket ping/pong exchanges")
