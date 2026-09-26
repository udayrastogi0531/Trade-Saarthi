"""Build live trading context for the copilot from platform data."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import get_settings
from backend.app.core.logging import get_logger
from backend.app.db.models import MarketRegimeRecord, Signal, Trade
from backend.app.modules.copilot.nlp import extract_symbol
from backend.app.modules.market_data.engine import MarketDataEngine
from backend.app.modules.market_regime.engine import RegimeEngine
from backend.app.modules.risk.advanced import AdvancedRiskEngine
from backend.app.modules.technical_analysis.engine import TechnicalAnalysisEngine
from backend.app.schemas.market import CandleRequest

logger = get_logger(__name__)


class CopilotContextBuilder:
  """Aggregates live signals, trades, risk, regime for conversational AI."""

  async def build(
    self,
    db: AsyncSession,
    account_id: int,
    user_message: str,
  ) -> tuple[dict, list[str]]:
    settings = get_settings()
    sources: list[str] = []
    ctx: dict = {
      "account_id": account_id,
      "paper_trading": settings.paper_trading,
      "watchlist": settings.watchlist,
    }

    # Open trades
    trades_result = await db.execute(
      select(Trade)
      .where(Trade.account_id == account_id, Trade.status == "open")
      .order_by(Trade.opened_at.desc())
      .limit(10)
    )
    open_trades = trades_result.scalars().all()
    ctx["open_trades"] = [
      {
        "symbol": t.symbol,
        "direction": t.direction,
        "entry": float(t.entry_price) if t.entry_price else None,
        "sl": float(t.stop_loss),
        "target": float(t.target_price),
        "qty": t.quantity,
      }
      for t in open_trades
    ]
    sources.append("open_trades")

    # Closed trades PnL today
    closed_result = await db.execute(
      select(Trade).where(Trade.account_id == account_id, Trade.status == "closed").limit(20)
    )
    closed = closed_result.scalars().all()
    total_pnl = sum(float(t.pnl or 0) for t in closed)
    wins = sum(1 for t in closed if t.pnl and float(t.pnl) > 0)
    ctx["portfolio"] = {
      "closed_trades_count": len(closed),
      "total_pnl_recent": round(total_pnl, 2),
      "win_rate_recent": round(wins / len(closed) * 100, 1) if closed else 0,
    }
    sources.append("portfolio")

    # Fetch Kite holdings and sync context
    try:
      from backend.app.modules.portfolio.kite_sync import KitePortfolioSync
      sync = KitePortfolioSync()
      p_data = await sync.fetch_portfolio(db)
      ctx["portfolio_holdings"] = p_data.get("holdings", [])
      ctx["portfolio_summary"] = p_data.get("summary", {})
      sources.append("kite_portfolio")
    except Exception as e:
      logger.error("copilot_portfolio_sync_failed", error=str(e))

    # Recent signals
    sig_result = await db.execute(
      select(Signal).order_by(Signal.created_at.desc()).limit(8)
    )
    signals = sig_result.scalars().all()
    ctx["recent_signals"] = [
      {
        "symbol": s.symbol,
        "direction": s.direction,
        "approved": s.approved,
        "setup": s.setup_type,
        "confidence": float(s.confidence),
        "regime": s.market_regime,
        "rejections": s.rejection_reasons or [],
      }
      for s in signals
    ]
    sources.append("signals")

    # Symbol-specific context
    symbol = extract_symbol(user_message)
    if symbol:
      ctx["focus_symbol"] = symbol
      try:
        market = MarketDataEngine()
        df = await market.get_candles(
          CandleRequest(symbol=symbol, exchange="NSE", interval="15m", limit=120)
        )
        snap = TechnicalAnalysisEngine().analyze(df, symbol, "15m")
        regime = RegimeEngine().detect(df, symbol, snap)
        ctx["symbol_analysis"] = {
          "trend": snap.trend_direction,
          "trend_strength": snap.trend_strength,
          "rsi": snap.rsi,
          "volume_spike": snap.volume_spike,
          "atr_pct": snap.atr_pct,
          "regime": regime.regime.value,
          "allowed_setups": regime.allowed_setups,
        }
        sources.append(f"market_data:{symbol}")
      except Exception as exc:
        logger.warning("copilot_symbol_context_failed", symbol=symbol, error=str(exc))
        ctx["symbol_analysis"] = {"error": "Could not fetch live data"}

    # Regime history for focus or NIFTY
    regime_sym = symbol or "NIFTY"
    reg_result = await db.execute(
      select(MarketRegimeRecord)
      .where(MarketRegimeRecord.symbol == regime_sym)
      .order_by(MarketRegimeRecord.recorded_at.desc())
      .limit(1)
    )
    latest_regime = reg_result.scalar_one_or_none()
    if latest_regime:
      ctx["latest_regime"] = {
        "symbol": latest_regime.symbol,
        "regime": latest_regime.regime,
        "confidence": float(latest_regime.confidence),
      }
      sources.append("regime")

    # Risk / correlation
    open_syms = [t.symbol for t in open_trades]
    if open_syms:
      ctx["correlation_matrix"] = AdvancedRiskEngine().correlation_matrix(
        open_syms + (settings.watchlist[:3] or [])
      )
      sources.append("risk_correlation")

    ctx["risk_policy"] = {
      "max_daily_loss_pct": settings.max_daily_loss_pct,
      "max_drawdown_pct": settings.max_drawdown_pct,
      "max_trades_per_day": settings.max_trades_per_day,
      "min_risk_reward": settings.min_risk_reward,
    }
    sources.append("risk_policy")

    return ctx, sources
