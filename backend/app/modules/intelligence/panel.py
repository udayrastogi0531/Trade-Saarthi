"""AI Market Intelligence Panel — real-time aggregated insights."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import get_settings
from backend.app.db.models import MarketRegimeRecord, ScannerLog, Signal
from backend.app.modules.learning.engine import LearningEngine
from backend.app.modules.risk.advanced import AdvancedRiskEngine


class IntelligencePanel:
  async def build(self, db: AsyncSession, account_id: int = 1) -> dict:
    settings = get_settings()

    sig_result = await db.execute(
      select(Signal).order_by(Signal.created_at.desc()).limit(30)
    )
    signals = sig_result.scalars().all()
    approved = [s for s in signals if s.approved]
    rejected = [s for s in signals if not s.approved]

    regime_result = await db.execute(
      select(MarketRegimeRecord).order_by(MarketRegimeRecord.recorded_at.desc()).limit(5)
    )
    regimes = regime_result.scalars().all()

    scan_result = await db.execute(
      select(ScannerLog).order_by(ScannerLog.created_at.desc()).limit(20)
    )
    scans = scan_result.scalars().all()

    learning = LearningEngine()
    best_setups = await learning.rank_setups(db)
    worst = sorted(best_setups, key=lambda x: x["score"])[:3] if best_setups else []

    top_setups = [
      {
        "symbol": s.symbol,
        "direction": s.direction,
        "confidence": float(s.confidence),
        "quality": float(s.quality_score or 0),
        "setup": s.setup_type,
        "regime": s.market_regime,
      }
      for s in approved[:5]
    ]

    regime_counts: dict[str, int] = {}
    for r in regimes:
      regime_counts[r.regime] = regime_counts.get(r.regime, 0) + 1
    dominant_regime = max(regime_counts, key=regime_counts.get) if regime_counts else "unknown"

    risk_flags = []
    if len(approved) > settings.max_trades_per_day:
      risk_flags.append("High signal volume — review overtrading")
    if dominant_regime in ("choppy", "volatile", "news_driven"):
      risk_flags.append(f"Elevated risk regime: {dominant_regime}")

    vol_ctx = self._directional_volatility_context(dominant_regime, settings, risk_flags)

    return {
      "market_regime": dominant_regime,
      "watchlist": settings.watchlist,
      "approved_signals_count": len(approved),
      "rejected_signals_count": len(rejected),
      "top_setups": top_setups,
      "weakest_setups": worst,
      "best_historical_setups": best_setups[:5],
      "scanner_recent": [
        {"symbol": sc.symbol, "approved": sc.approved, "rank": float(sc.rank_score or 0)}
        for sc in scans[:8]
      ],
      "confidence_heatmap": self._confidence_heatmap(approved),
      "volatility_note": dominant_regime,
      "directional_volatility_context": vol_ctx,
      "risk_flags": risk_flags,
      "sector_correlation": AdvancedRiskEngine().correlation_matrix(settings.watchlist[:5]),
      "structure_summary": "See per-symbol /regime and structure endpoints",
    }

  @staticmethod
  def _directional_volatility_context(
    dominant_regime: str,
    settings,
    risk_flags: list[str],
  ) -> dict:
    """Manual directional / options-awareness — advisory only, no options engine."""
    warnings: list[str] = []
    high_vol_regimes = ("volatile", "choppy", "news_driven", "high_volatility", "panic")
    if dominant_regime in high_vol_regimes:
      warnings.append(
        f"Unstable regime ({dominant_regime}) — reduce size; avoid aggressive short-dated options"
      )
    if getattr(settings, "volatility_shutdown_atr_pct", None):
      warnings.append(
        f"System volatility shutdown threshold: {settings.volatility_shutdown_atr_pct}% ATR (execution safety)"
      )
    if getattr(settings, "volatility_anomaly_atr_pct", None):
      warnings.append(
        f"Signal filter flags anomalies above {settings.volatility_anomaly_atr_pct}% ATR"
      )

    now = datetime.now(timezone.utc)
    if now.weekday() in (3, 4):
      warnings.append(
        "Weekly expiry window (Thu–Fri) — elevated gap/theta risk for short-dated directional options"
      )

    exhaustion_note = None
    if dominant_regime in ("volatile", "choppy"):
      exhaustion_note = (
        "Momentum exhaustion risk elevated — confirm structure before directional entries"
      )

    return {
      "dominant_regime": dominant_regime,
      "warnings": warnings,
      "momentum_exhaustion_note": exhaustion_note,
      "confidence_reduction_suggested": dominant_regime in high_vol_regimes,
      "disclaimer": "Advisory for manual decision-making only — not automated options execution",
    }

  @staticmethod
  def _confidence_heatmap(signals: list) -> dict:
    buckets = {"70-80": 0, "80-90": 0, "90+": 0}
    for s in signals:
      c = float(s.confidence)
      if c >= 90:
        buckets["90+"] += 1
      elif c >= 80:
        buckets["80-90"] += 1
      elif c >= 70:
        buckets["70-80"] += 1
    return buckets
