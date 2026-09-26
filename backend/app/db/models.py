"""SQLAlchemy ORM models."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.session import Base


class Account(Base):
  __tablename__ = "accounts"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  name: Mapped[str] = mapped_column(String(128), nullable=False)
  capital: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=100_000)
  broker: Mapped[str] = mapped_column(String(32), default="paper")
  is_active: Mapped[bool] = mapped_column(Boolean, default=True)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
  updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

  trades: Mapped[list["Trade"]] = relationship(back_populates="account")


class BrokerToken(Base):
  __tablename__ = "broker_tokens"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  broker: Mapped[str] = mapped_column(String(32))
  account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"))
  access_token: Mapped[str] = mapped_column(Text)
  metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
  updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class RiskState(Base):
  __tablename__ = "risk_state"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
  trade_date: Mapped[date] = mapped_column(Date)
  daily_pnl: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
  trades_today: Mapped[int] = mapped_column(Integer, default=0)
  peak_equity: Mapped[Decimal] = mapped_column(Numeric(18, 2))
  current_drawdown_pct: Mapped[Decimal] = mapped_column(Numeric(8, 4), default=0)
  kill_switch_active: Mapped[bool] = mapped_column(Boolean, default=False)
  kill_switch_reason: Mapped[str | None] = mapped_column(Text)
  updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Signal(Base):
  __tablename__ = "signals"

  id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"))
  symbol: Mapped[str] = mapped_column(String(32))
  exchange: Mapped[str] = mapped_column(String(8), default="NSE")
  direction: Mapped[str] = mapped_column(String(8))
  setup_type: Mapped[str] = mapped_column(String(64))
  entry_price: Mapped[Decimal] = mapped_column(Numeric(18, 4))
  stop_loss: Mapped[Decimal] = mapped_column(Numeric(18, 4))
  target_price: Mapped[Decimal] = mapped_column(Numeric(18, 4))
  risk_reward: Mapped[Decimal] = mapped_column(Numeric(8, 4))
  confidence: Mapped[Decimal] = mapped_column(Numeric(5, 2))
  approved: Mapped[bool] = mapped_column(Boolean, default=False)
  rejection_reasons: Mapped[dict | None] = mapped_column(JSONB)
  technical_snapshot: Mapped[dict | None] = mapped_column(JSONB)
  ai_reasoning: Mapped[dict | None] = mapped_column(JSONB)
  quality_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
  mtf_alignment_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
  market_regime: Mapped[str | None] = mapped_column(String(32))
  rank_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Trade(Base):
  __tablename__ = "trades"

  id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  signal_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("signals.id"))
  account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
  symbol: Mapped[str] = mapped_column(String(32))
  exchange: Mapped[str] = mapped_column(String(8), default="NSE")
  direction: Mapped[str] = mapped_column(String(8))
  status: Mapped[str] = mapped_column(String(32), default="open")
  entry_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
  exit_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
  stop_loss: Mapped[Decimal] = mapped_column(Numeric(18, 4))
  target_price: Mapped[Decimal] = mapped_column(Numeric(18, 4))
  quantity: Mapped[int] = mapped_column(Integer)
  pnl: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
  pnl_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
  is_paper: Mapped[bool] = mapped_column(Boolean, default=True)
  opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
  closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

  account: Mapped["Account"] = relationship(back_populates="trades")


class BacktestRun(Base):
  __tablename__ = "backtest_runs"

  id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  strategy_name: Mapped[str] = mapped_column(String(128))
  symbol: Mapped[str] = mapped_column(String(32))
  start_date: Mapped[date] = mapped_column(Date)
  end_date: Mapped[date] = mapped_column(Date)
  parameters: Mapped[dict | None] = mapped_column(JSONB)
  metrics: Mapped[dict] = mapped_column(JSONB)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Watchlist(Base):
  __tablename__ = "watchlists"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  name: Mapped[str] = mapped_column(String(64), unique=True)
  symbols: Mapped[list] = mapped_column(JSONB, default=list)
  is_active: Mapped[bool] = mapped_column(Boolean, default=True)
  scan_interval_minutes: Mapped[int] = mapped_column(Integer, default=3)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class ScannerLog(Base):
  __tablename__ = "scanner_logs"

  id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
  symbol: Mapped[str] = mapped_column(String(32))
  approved: Mapped[bool] = mapped_column(Boolean, default=False)
  quality_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
  mtf_alignment_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
  regime: Mapped[str | None] = mapped_column(String(32))
  rank_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
  signal_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("signals.id"))
  rejection_reasons: Mapped[dict | None] = mapped_column(JSONB)
  duration_ms: Mapped[int | None] = mapped_column(Integer)
  structure_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class TradeJournal(Base):
  __tablename__ = "trade_journal"

  id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  trade_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("trades.id", ondelete="CASCADE"))
  setup_type: Mapped[str | None] = mapped_column(String(64))
  strategy_name: Mapped[str | None] = mapped_column(String(64))
  ai_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
  quality_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
  market_regime: Mapped[str | None] = mapped_column(String(32))
  outcome: Mapped[str | None] = mapped_column(String(16))
  mfe: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
  mae: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
  emotional_override: Mapped[bool] = mapped_column(Boolean, default=False)
  notes: Mapped[str | None] = mapped_column(Text)
  screenshot_path: Mapped[str | None] = mapped_column(String(512))
  trade_reasoning: Mapped[str | None] = mapped_column(Text)
  execution_quality: Mapped[str | None] = mapped_column(String(32))
  duration_minutes: Mapped[int | None] = mapped_column(Integer)
  metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class MarketRegimeRecord(Base):
  __tablename__ = "market_regimes"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  symbol: Mapped[str] = mapped_column(String(32))
  exchange: Mapped[str] = mapped_column(String(8), default="NSE")
  regime: Mapped[str] = mapped_column(String(32))
  confidence: Mapped[Decimal] = mapped_column(Numeric(5, 2))
  metrics: Mapped[dict | None] = mapped_column(JSONB)
  recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class CopilotSession(Base):
  __tablename__ = "copilot_sessions"

  id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"), default=1)
  language: Mapped[str] = mapped_column(String(16), default="hinglish")
  title: Mapped[str | None] = mapped_column(String(256))
  metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
  updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class CopilotMessage(Base):
  __tablename__ = "copilot_messages"

  id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("copilot_sessions.id", ondelete="CASCADE"))
  role: Mapped[str] = mapped_column(String(16))
  content: Mapped[str] = mapped_column(Text)
  language: Mapped[str | None] = mapped_column(String(16))
  intent: Mapped[str | None] = mapped_column(String(64))
  audio_url: Mapped[str | None] = mapped_column(String(512))
  metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class VoiceAlert(Base):
  __tablename__ = "voice_alerts"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"))
  alert_type: Mapped[str] = mapped_column(String(32))
  message: Mapped[str] = mapped_column(Text)
  language: Mapped[str] = mapped_column(String(16), default="hinglish")
  delivered: Mapped[bool] = mapped_column(Boolean, default=False)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class ChartAnalysisRecord(Base):
  __tablename__ = "chart_analyses"

  id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  symbol: Mapped[str | None] = mapped_column(String(32))
  file_path: Mapped[str | None] = mapped_column(String(512))
  analysis: Mapped[dict] = mapped_column(JSONB)
  risk_assessment: Mapped[dict | None] = mapped_column(JSONB)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class MarketStructureSnapshot(Base):
  __tablename__ = "market_structure_snapshots"

  id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  symbol: Mapped[str] = mapped_column(String(32))
  timeframe: Mapped[str] = mapped_column(String(8), default="15m")
  structure_type: Mapped[str | None] = mapped_column(String(32))
  trend_quality: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
  structure_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
  bos_detected: Mapped[bool] = mapped_column(Boolean, default=False)
  choch_detected: Mapped[bool] = mapped_column(Boolean, default=False)
  liquidity_sweep: Mapped[bool] = mapped_column(Boolean, default=False)
  fake_breakout_risk: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
  zones: Mapped[dict | None] = mapped_column(JSONB)
  analysis: Mapped[dict] = mapped_column(JSONB)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class SetupPerformance(Base):
  __tablename__ = "setup_performance"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  setup_type: Mapped[str] = mapped_column(String(64))
  market_regime: Mapped[str | None] = mapped_column(String(32))
  trade_count: Mapped[int] = mapped_column(Integer, default=0)
  win_count: Mapped[int] = mapped_column(Integer, default=0)
  avg_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
  avg_ai_accuracy: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
  false_breakout_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
  expectancy: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
  last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class SignalOutcome(Base):
  __tablename__ = "signal_outcomes"

  id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  signal_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("signals.id"))
  setup_type: Mapped[str | None] = mapped_column(String(64))
  market_regime: Mapped[str | None] = mapped_column(String(32))
  ai_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
  structure_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
  approved: Mapped[bool] = mapped_column(Boolean, default=False)
  outcome: Mapped[str | None] = mapped_column(String(16))
  pnl: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
  false_breakout: Mapped[bool] = mapped_column(Boolean, default=False)
  recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class MarketBriefing(Base):
  __tablename__ = "market_briefings"

  id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  briefing_type: Mapped[str] = mapped_column(String(32))
  content: Mapped[str] = mapped_column(Text)
  summary: Mapped[dict | None] = mapped_column(JSONB)
  language: Mapped[str] = mapped_column(String(16), default="hinglish")
  voice_delivered: Mapped[bool] = mapped_column(Boolean, default=False)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class ScannerRun(Base):
  __tablename__ = "scanner_runs"

  id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True)
  symbols_scanned: Mapped[int] = mapped_column(Integer)
  approved_count: Mapped[int] = mapped_column(Integer)
  avg_latency_ms: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
  health_status: Mapped[str] = mapped_column(String(16), default="ok")
  errors: Mapped[dict | None] = mapped_column(JSONB)
  started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
  completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ExecutionLog(Base):
  __tablename__ = "execution_logs"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  trade_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("trades.id"))
  broker: Mapped[str] = mapped_column(String(32))
  order_type: Mapped[str] = mapped_column(String(32))
  request_payload: Mapped[dict | None] = mapped_column(JSONB)
  response_payload: Mapped[dict | None] = mapped_column(JSONB)
  status: Mapped[str] = mapped_column(String(32))
  error_message: Mapped[str | None] = mapped_column(Text)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class ExecutionSafetyLog(Base):
  __tablename__ = "execution_safety_log"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"))
  check_type: Mapped[str] = mapped_column(String(64))
  passed: Mapped[bool] = mapped_column(Boolean)
  details: Mapped[dict | None] = mapped_column(JSONB)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class WalkForwardRun(Base):
  __tablename__ = "walk_forward_runs"

  id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  strategy_name: Mapped[str] = mapped_column(String(128))
  symbol: Mapped[str] = mapped_column(String(32))
  parameters: Mapped[dict | None] = mapped_column(JSONB)
  window_config: Mapped[dict] = mapped_column(JSONB)
  in_sample_metrics: Mapped[dict] = mapped_column(JSONB)
  out_of_sample_metrics: Mapped[dict] = mapped_column(JSONB)
  rolling_metrics: Mapped[dict | None] = mapped_column(JSONB)
  stability_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
  overfitting_flag: Mapped[bool] = mapped_column(Boolean, default=False)
  decay_detected: Mapped[bool] = mapped_column(Boolean, default=False)
  regime_breakdown: Mapped[dict | None] = mapped_column(JSONB)
  report: Mapped[dict] = mapped_column(JSONB)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class MonteCarloRun(Base):
  __tablename__ = "monte_carlo_runs"

  id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"))
  strategy_name: Mapped[str | None] = mapped_column(String(128))
  simulations: Mapped[int] = mapped_column(Integer, default=1000)
  config: Mapped[dict] = mapped_column(JSONB)
  probability_of_ruin: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
  worst_drawdown_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
  expected_drawdown_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
  survival_probability: Mapped[Decimal | None] = mapped_column(Numeric(8, 6))
  tail_risk_var_99: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
  drawdown_distribution: Mapped[dict | None] = mapped_column(JSONB)
  stress_scenarios: Mapped[dict | None] = mapped_column(JSONB)
  report: Mapped[dict] = mapped_column(JSONB)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class PortfolioSnapshot(Base):
  __tablename__ = "portfolio_snapshots"

  id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
  positions: Mapped[list] = mapped_column(JSONB, default=list)
  sector_exposure: Mapped[dict | None] = mapped_column(JSONB)
  correlation_matrix: Mapped[dict | None] = mapped_column(JSONB)
  var_95: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
  var_99: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
  portfolio_heat: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
  beta_exposure: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
  concentration_risk: Mapped[dict | None] = mapped_column(JSONB)
  risk_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class StrategyResearchReport(Base):
  __tablename__ = "strategy_research_reports"

  id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  report_type: Mapped[str] = mapped_column(String(64))
  scope: Mapped[dict | None] = mapped_column(JSONB)
  findings: Mapped[dict] = mapped_column(JSONB)
  evidence: Mapped[dict] = mapped_column(JSONB)
  uncertainty_notes: Mapped[str | None] = mapped_column(Text)
  ai_summary: Mapped[str | None] = mapped_column(Text)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class ExecutionQualityLog(Base):
  __tablename__ = "execution_quality_logs"

  id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  trade_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("trades.id"))
  order_id: Mapped[str | None] = mapped_column(String(128))
  symbol: Mapped[str | None] = mapped_column(String(32))
  expected_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
  fill_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
  slippage_bps: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
  latency_ms: Mapped[int | None] = mapped_column(Integer)
  partial_fill: Mapped[bool] = mapped_column(Boolean, default=False)
  rejected: Mapped[bool] = mapped_column(Boolean, default=False)
  rejection_reason: Mapped[str | None] = mapped_column(Text)
  spread_bps: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
  simulated: Mapped[bool] = mapped_column(Boolean, default=True)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class RegimePerformance(Base):
  __tablename__ = "regime_performance"

  id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  strategy_name: Mapped[str | None] = mapped_column(String(128))
  setup_type: Mapped[str | None] = mapped_column(String(64))
  regime: Mapped[str] = mapped_column(String(32))
  trade_count: Mapped[int] = mapped_column(Integer, default=0)
  win_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
  expectancy: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
  avg_pnl: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
  sharpe: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
  confidence_adjustment: Mapped[Decimal | None] = mapped_column(Numeric(6, 4), default=0)
  updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class DataQualityEvent(Base):
  __tablename__ = "data_quality_events"

  id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  symbol: Mapped[str | None] = mapped_column(String(32))
  provider: Mapped[str | None] = mapped_column(String(32))
  event_type: Mapped[str] = mapped_column(String(64))
  severity: Mapped[str] = mapped_column(String(16))
  details: Mapped[dict | None] = mapped_column(JSONB)
  feed_healthy: Mapped[bool] = mapped_column(Boolean, default=True)
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class AuditLog(Base):
  __tablename__ = "audit_logs"

  id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  actor: Mapped[str | None] = mapped_column(String(128))
  action: Mapped[str] = mapped_column(String(128))
  resource: Mapped[str | None] = mapped_column(String(256))
  details: Mapped[dict | None] = mapped_column(JSONB)
  ip_address: Mapped[str | None] = mapped_column(String(64))
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class CapitalSafetyState(Base):
  __tablename__ = "capital_safety_state"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), unique=True)
  deployment_stage: Mapped[str] = mapped_column(String(32), default="sandbox")
  max_live_capital: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
  human_approval_required: Mapped[bool] = mapped_column(Boolean, default=True)
  emergency_shutdown: Mapped[bool] = mapped_column(Boolean, default=False)
  shutdown_reason: Mapped[str | None] = mapped_column(Text)
  daily_loss_limit_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), default=1.0)
  updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class EdgeTracking(Base):
  __tablename__ = "edge_tracking"

  id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  setup_type: Mapped[str] = mapped_column(String(64))
  regime: Mapped[str | None] = mapped_column(String(32))
  rolling_expectancy: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
  rolling_win_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
  rolling_sharpe: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
  edge_status: Mapped[str | None] = mapped_column(String(32))
  sample_size: Mapped[int | None] = mapped_column(Integer)
  window_days: Mapped[int] = mapped_column(Integer, default=30)
  updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
