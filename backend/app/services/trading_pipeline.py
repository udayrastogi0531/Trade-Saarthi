"""Orchestrates the full quant intelligence pipeline."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import get_settings
from backend.app.core.logging import get_logger
from backend.app.core.metrics import (
  AI_REQUESTS,
  PIPELINE_LATENCY,
  PORTFOLIO_RISK_BLOCKS,
  SIGNALS_APPROVED,
  SIGNALS_REJECTED,
)
from backend.app.db.models import MarketRegimeRecord, MarketStructureSnapshot, Signal
from backend.app.modules.data_quality.engine import DataQualityEngine
from backend.app.modules.learning.adaptive import AdaptiveLearningEngine
from backend.app.modules.portfolio.engine import PortfolioIntelligenceEngine
from backend.app.modules.regime.research import RegimeResearchEngine
from backend.app.modules.market_structure.engine import MarketStructureEngine
from backend.app.modules.ai_reasoning.engine import AIReasoningEngine
from backend.app.modules.journal.analytics import JournalAnalyticsEngine
from backend.app.modules.market_data.engine import MarketDataEngine
from backend.app.modules.mtf_analysis.engine import MTFAnalysisEngine
from backend.app.modules.paper_trading.engine import PaperTradingEngine
from backend.app.modules.risk.advanced import AdvancedRiskEngine
from backend.app.modules.risk.engine import RiskEngine
from backend.app.modules.signal_filter.engine import SignalFilterEngine
from backend.app.modules.strategy.engine import StrategyEngine
from backend.app.modules.telegram.engine import TelegramAlertEngine
from backend.app.modules.technical_analysis.engine import TechnicalAnalysisEngine
from backend.app.schemas.market import CandleRequest, MultiTimeframeRequest
from backend.app.schemas.trade import SignalRequest, SignalResponse

logger = get_logger(__name__)

MTF_INTERVALS = ["5m", "15m", "1h", "4h", "1d"]


class TradingPipeline:
  def __init__(self) -> None:
    self._market = MarketDataEngine()
    self._ta = TechnicalAnalysisEngine()
    self._strategy = StrategyEngine()
    self._risk = RiskEngine()
    self._advanced_risk = AdvancedRiskEngine()
    self._mtf = MTFAnalysisEngine()
    self._filter = SignalFilterEngine()
    self._ai = AIReasoningEngine()
    self._telegram = TelegramAlertEngine()
    self._paper = PaperTradingEngine()
    self._journal = JournalAnalyticsEngine()
    self._structure = MarketStructureEngine()
    self._learning = AdaptiveLearningEngine()
    self._regime_research = RegimeResearchEngine()
    self._data_quality = DataQualityEngine()
    self._portfolio = PortfolioIntelligenceEngine()
    self._settings = get_settings()

  async def generate_signal(
    self,
    db: AsyncSession,
    request: SignalRequest,
    persist_scanner: bool = False,
    run_id: str | None = None,
  ) -> SignalResponse:
    import time

    start = time.perf_counter()
    symbol = request.symbol.upper()

    candle_req = CandleRequest(symbol=symbol, exchange=request.exchange, interval="15m", limit=200)
    df = await self._market.get_candles(candle_req)

    dq_report = self._data_quality.validate_candles(df, symbol)
    if not dq_report.healthy:
      PIPELINE_LATENCY.observe(time.perf_counter() - start)
      return SignalResponse(
        approved=False,
        setup=None,
        rejection_reasons=[f"Data quality: {i}" for i in dq_report.issues],
        technical_summary={"data_quality": dq_report.to_dict()},
        risk_check={"approved": False, "reasons": dq_report.issues},
        ai_reasoning=None,
        generated_at=datetime.utcnow(),
      )

    primary_snap = self._ta.analyze(df, symbol, "15m")

    mtf_req = MultiTimeframeRequest(
      symbol=symbol, exchange=request.exchange, intervals=MTF_INTERVALS
    )
    mtf_data = await self._market.get_multi_timeframe(mtf_req)
    mtf_snapshots = {tf: self._ta.analyze(data, symbol, tf) for tf, data in mtf_data.items()}

    regime_research = self._regime_research.research(df, symbol, primary_snap)
    regime = regime_research.base_regime
    await self._persist_regime(db, symbol, request.exchange, regime)

    structure = self._structure.analyze(df, symbol, "15m")
    await self._persist_structure(db, structure)

    strategy_result = self._strategy.evaluate(
      symbol, df, "15m", mtf_snapshots=mtf_snapshots
    )

    all_rejections = list(strategy_result.rejection_reasons)
    setup = strategy_result.setup
    risk_check: dict = {"approved": False, "reasons": []}
    filter_result = None
    mtf_result = None
    quality_score = 0.0
    technical_summary_extra: str | None = None

    if regime.regime.value in ("choppy", "low_volatility") and not strategy_result.rejection_reasons:
      all_rejections.append(f"Regime filter: {regime.regime.value}")

    if setup and strategy_result.setup_type and not regime.allowed_setups:
      if strategy_result.setup_type not in regime.allowed_setups and regime.allowed_setups:
        all_rejections.append(
          f"Setup {strategy_result.setup_type} blocked in {regime.regime.value} regime"
        )

    if setup and strategy_result.approved:
      struct_ok, struct_reason = self._structure.is_breakout_valid(structure, setup.direction)
      if not struct_ok and self._settings.structure_block_fake_breakout:
        all_rejections.append(struct_reason)

      if setup.confidence and self._settings.learning_enabled:
        calibrated, learn_note = await self._learning.recalibrate_with_edge(
          db, strategy_result.setup_type, regime.regime.value, setup.confidence
        )
        calibrated = round(calibrated * regime_research.confidence_multiplier, 2)
        setup = setup.model_copy(update={"confidence": calibrated})
        if learn_note:
          technical_summary_extra = learn_note
        else:
          technical_summary_extra = None
      else:
        technical_summary_extra = None

      mtf_result = self._mtf.analyze(mtf_snapshots, setup.direction)
      if not mtf_result.aligned:
        all_rejections.extend(mtf_result.conflicts[:3])

      filter_result = self._filter.evaluate(
        setup,
        primary_snap,
        regime,
        mtf_result,
        fake_breakout_risk=structure.fake_breakout_risk,
      )
      quality_score = filter_result.quality_score
      if not filter_result.passed:
        all_rejections.extend(filter_result.rejection_reasons)

      risk_result = await self._risk.validate_trade(
        db, request.account_id, setup, capital=request.capital
      )
      open_symbols = await self._risk.get_open_symbols(db, request.account_id)

      adv_ctx, adv_reasons = await self._advanced_risk.build_context(
        db,
        request.account_id,
        float(request.capital or self._settings.default_account_capital),
        setup,
        primary_snap,
        regime,
        open_symbols,
      )
      all_rejections.extend(adv_reasons)

      if adv_ctx.atr_stop and setup.direction == "BUY":
        if adv_ctx.atr_stop > setup.stop_loss:
          setup = setup.model_copy(update={"stop_loss": adv_ctx.atr_stop})

      risk_check = {
        "approved": risk_result.approved and not adv_ctx.circuit_breaker,
        "reasons": risk_result.reasons + adv_reasons,
        "position_size": risk_result.position_size,
        "risk_amount": risk_result.risk_amount,
        "kill_switch": risk_result.kill_switch_active,
        "atr_stop": adv_ctx.atr_stop,
        "position_multiplier": adv_ctx.position_multiplier,
        "correlation_warnings": adv_ctx.correlation_warnings,
      }

      if risk_result.approved and not adv_ctx.circuit_breaker:
        adjusted_size = self._advanced_risk.volatility_adjusted_size(
          risk_result.position_size, primary_snap, regime
        )
        adjusted_size = max(
          1,
          int(adjusted_size * adv_ctx.position_multiplier * regime_research.position_size_multiplier),
        )
        risk_result.position_size = adjusted_size
        setup = self._risk.apply_sizing_to_setup(setup, risk_result)

        port_report = await self._portfolio.analyze(db, request.account_id)
        blocked, block_reason = self._portfolio.should_block_new_trade(port_report, symbol)
        if blocked:
          all_rejections.append(f"Portfolio risk: {block_reason}")
          PORTFOLIO_RISK_BLOCKS.inc()
      else:
        all_rejections.extend(risk_result.reasons)

    technical_summary = {
      **strategy_result.technical_summary,
      "market_regime": regime.regime.value,
      "regime_confidence": regime.confidence,
      "mtf_alignment_score": mtf_result.alignment_score if mtf_result else 0,
      "quality_score": quality_score,
      "mtf_summary": mtf_result.summary if mtf_result else "",
      "structure_confidence": structure.structure_confidence,
      "structure_explanation": structure.explanation,
      "bos": structure.bos_detected,
      "fake_breakout_risk": structure.fake_breakout_risk,
      "learning_note": technical_summary_extra if setup else None,
      "extended_regime": regime_research.extended_regime.value,
      "regime_research_notes": regime_research.research_notes,
      "data_quality_penalty": dq_report.confidence_penalty,
    }

    approved = bool(setup) and not all_rejections

    ai_reasoning = None
    if request.include_ai_reasoning:
      AI_REQUESTS.inc()
      ai_reasoning = await self._ai.analyze_trade(
        setup, technical_summary, approved, all_rejections
      )
      if ai_reasoning and not ai_reasoning.trade_valid and approved:
        all_rejections.append("AI validation layer rejected trade")
        approved = False

    signal_record = await self._persist_signal(
      db,
      request,
      setup,
      approved,
      all_rejections,
      technical_summary,
      ai_reasoning.model_dump() if ai_reasoning else None,
      strategy_result.setup_type,
      quality_score,
      mtf_result.alignment_score if mtf_result else None,
      regime.regime.value,
    )

    if approved and setup:
      SIGNALS_APPROVED.inc()
      await self._telegram.send_trade_alert(setup, ai_reasoning)
      await self._voice_signal_alert(db, setup, request.account_id)
      if self._settings.paper_trading:
        trade = await self._paper.open_trade(
          db, request.account_id, setup, signal_record.id
        )
        await self._journal.record_trade_entry(
          db,
          trade.id,
          strategy_result.setup_type,
          "multi_setup",
          ai_reasoning.confidence_score if ai_reasoning else setup.confidence,
          quality_score,
          regime.regime.value,
        )
    else:
      SIGNALS_REJECTED.inc()
      if all_rejections:
        await self._telegram.send_rejection_alert(symbol, all_rejections)
        await self._voice_rejection_alert(db, symbol, all_rejections, request.account_id)

    if self._settings.learning_enabled:
      await self._learning.record_signal_outcome(
        db,
        signal_record.id,
        strategy_result.setup_type,
        regime.regime.value,
        float(setup.confidence) if setup else 0,
        structure.structure_confidence,
        approved,
        false_breakout=structure.fake_breakout_risk > 0.6,
      )

    PIPELINE_LATENCY.observe(time.perf_counter() - start)

    return SignalResponse(
      approved=approved,
      setup=setup if approved else None,
      rejection_reasons=all_rejections,
      technical_summary=technical_summary,
      risk_check=risk_check,
      ai_reasoning=ai_reasoning,
      generated_at=datetime.utcnow(),
    )

  async def _persist_structure(self, db, structure) -> None:
    record = MarketStructureSnapshot(
      symbol=structure.symbol,
      timeframe=structure.timeframe,
      structure_type=structure.trend_direction,
      trend_quality=Decimal(str(structure.trend_quality)),
      structure_confidence=Decimal(str(structure.structure_confidence)),
      bos_detected=structure.bos_detected,
      choch_detected=structure.choch_detected,
      liquidity_sweep=structure.liquidity_sweep,
      fake_breakout_risk=Decimal(str(structure.fake_breakout_risk)),
      zones={
        "support": structure.support_zones,
        "resistance": structure.resistance_zones,
      },
      analysis=structure.to_dict(),
    )
    db.add(record)

  async def _voice_rejection_alert(
    self, db, symbol: str, reasons: list[str], account_id: int
  ) -> None:
    try:
      from backend.app.modules.voice.alerts import VoiceAlertService

      vas = VoiceAlertService()
      msg = vas.format_rejection_alert(symbol, reasons[0] if reasons else "unknown", "hinglish")
      alert = await vas.create_alert(db, "rejection", msg, "hinglish", account_id, priority="high")
      from backend.app.api.ws.copilot_ws import broadcast_alert

      await broadcast_alert(alert["message"], "rejection")
    except Exception as exc:
      logger.debug("voice_rejection_skipped", error=str(exc))

  async def _voice_signal_alert(self, db, setup, account_id: int) -> None:
    try:
      from backend.app.modules.voice.alerts import VoiceAlertService

      vas = VoiceAlertService()
      msg = vas.format_signal_alert(
        setup.symbol, setup.direction, setup.confidence, "hinglish", enhanced=True
      )
      alert = await vas.create_alert(db, "signal", msg, "hinglish", account_id)
      from backend.app.api.ws.copilot_ws import broadcast_alert

      await broadcast_alert(alert["message"], "signal")
    except Exception as exc:
      logger.debug("voice_alert_skipped", error=str(exc))

  async def _persist_regime(self, db, symbol: str, exchange: str, regime) -> None:
    record = MarketRegimeRecord(
      symbol=symbol,
      exchange=exchange,
      regime=regime.regime.value,
      confidence=Decimal(str(regime.confidence)),
      metrics=regime.metrics,
    )
    db.add(record)

  async def _persist_signal(
    self,
    db: AsyncSession,
    request: SignalRequest,
    setup,
    approved: bool,
    rejections: list[str],
    technical: dict,
    ai_data: dict | None,
    setup_type: str,
    quality_score: float,
    mtf_score: float | None,
    market_regime: str,
  ) -> Signal:
    record = Signal(
      account_id=request.account_id,
      symbol=request.symbol.upper(),
      exchange=request.exchange,
      direction=setup.direction if setup else "NONE",
      setup_type=setup_type,
      entry_price=Decimal(str(setup.entry)) if setup else Decimal("0"),
      stop_loss=Decimal(str(setup.stop_loss)) if setup else Decimal("0"),
      target_price=Decimal(str(setup.target)) if setup else Decimal("0"),
      risk_reward=Decimal(str(setup.risk_reward)) if setup else Decimal("0"),
      confidence=Decimal(str(setup.confidence)) if setup else Decimal("0"),
      approved=approved,
      rejection_reasons=rejections,
      technical_snapshot=technical,
      ai_reasoning=ai_data,
      quality_score=Decimal(str(quality_score)),
      mtf_alignment_score=Decimal(str(mtf_score or 0)),
      market_regime=market_regime,
    )
    db.add(record)
    await db.flush()
    return record
