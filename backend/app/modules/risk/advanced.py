"""Advanced risk extensions — ATR stops, volatility sizing, correlation, circuit breaker."""

from dataclasses import dataclass, field
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import get_settings
from backend.app.core.logging import get_logger
from backend.app.db.models import RiskState, Trade
from backend.app.modules.market_regime.engine import MarketRegime
from backend.app.modules.technical_analysis.engine import TechnicalSnapshot
from backend.app.schemas.trade import TradeSetup

logger = get_logger(__name__)

SECTOR_MAP: dict[str, str] = {
  "RELIANCE": "Energy",
  "TCS": "IT",
  "INFY": "IT",
  "HDFCBANK": "Financials",
  "NIFTY": "Index",
}


@dataclass
class AdvancedRiskContext:
  atr_stop: float | None = None
  position_multiplier: float = 1.0
  sector_exposure_pct: float = 0.0
  portfolio_exposure_pct: float = 0.0
  correlation_warnings: list[str] = field(default_factory=list)
  circuit_breaker: bool = False
  daily_budget_remaining: float = 0.0
  consecutive_losses: int = 0


class AdvancedRiskEngine:
  """Volatility-adjusted sizing, sector limits, rolling drawdown protection."""

  def __init__(self) -> None:
    self._settings = get_settings()

  def compute_atr_stop(
    self,
    setup: TradeSetup,
    snap: TechnicalSnapshot,
    multiplier: float | None = None,
  ) -> float:
    mult = multiplier or self._settings.atr_stop_multiplier
    atr = snap.atr
    if setup.direction == "BUY":
      return round(setup.entry - atr * mult, 2)
    return round(setup.entry + atr * mult, 2)

  def volatility_adjusted_size(
    self,
    base_size: int,
    snap: TechnicalSnapshot,
    regime: MarketRegime,
  ) -> int:
    if not self._settings.volatility_position_scale:
      return base_size

    scale = regime.position_size_multiplier
    if snap.atr_pct > 5:
      scale *= 0.5
    elif snap.atr_pct > 3:
      scale *= 0.75
    elif snap.atr_pct < 1:
      scale *= 0.8

    return max(1, int(base_size * scale))

  async def build_context(
    self,
    db: AsyncSession,
    account_id: int,
    equity: float,
    setup: TradeSetup,
    snap: TechnicalSnapshot,
    regime: MarketRegime,
    open_symbols: list[str],
  ) -> tuple[AdvancedRiskContext, list[str]]:
    reasons: list[str] = []
    ctx = AdvancedRiskContext()
    ctx.atr_stop = self.compute_atr_stop(setup, snap)

    ctx.consecutive_losses = await self._consecutive_losses(db, account_id)
    if ctx.consecutive_losses >= self._settings.consecutive_loss_reduction:
      ctx.position_multiplier *= 0.5
      reasons.append(
        f"Risk reduced after {ctx.consecutive_losses} consecutive losses"
      )

    sector = SECTOR_MAP.get(setup.symbol.upper(), "Other")
    sector_symbols = [s for s in open_symbols if SECTOR_MAP.get(s.upper()) == sector]
    sector_count = len(sector_symbols) + 1
    ctx.sector_exposure_pct = (sector_count / max(len(open_symbols) + 1, 1)) * 100

    if ctx.sector_exposure_pct > self._settings.max_sector_exposure_pct and sector_symbols:
      reasons.append(
        f"Sector {sector} exposure limit ({self._settings.max_sector_exposure_pct}%)"
      )

    total_positions = len(open_symbols) + 1
    ctx.portfolio_exposure_pct = min(
      self._settings.max_portfolio_exposure_pct,
      total_positions * (self._settings.max_position_size_pct),
    )
    if ctx.portfolio_exposure_pct >= self._settings.max_portfolio_exposure_pct:
      reasons.append("Max portfolio exposure reached")

    ctx.correlation_warnings = self._correlation_check(setup.symbol, open_symbols)

    risk_state = await self._get_risk_state(db, account_id)
    daily_budget = equity * (self._settings.daily_risk_budget_pct / 100)
    used = abs(float(risk_state.daily_pnl)) if risk_state and float(risk_state.daily_pnl) < 0 else 0
    ctx.daily_budget_remaining = max(0, daily_budget - used)

    if ctx.daily_budget_remaining <= 0 and used > 0:
      reasons.append("Daily risk budget exhausted")
      ctx.circuit_breaker = True

    if risk_state and float(risk_state.current_drawdown_pct) >= self._settings.max_drawdown_pct * 0.8:
      ctx.circuit_breaker = True
      ctx.position_multiplier *= 0.5
      reasons.append("Rolling drawdown protection — reduced sizing")

    return ctx, reasons

  def correlation_matrix(self, symbols: list[str]) -> dict[str, dict[str, float]]:
    """Simplified sector-based correlation proxy for heatmap."""
    matrix: dict[str, dict[str, float]] = {}
    for a in symbols:
      matrix[a] = {}
      sa = SECTOR_MAP.get(a.upper(), "Other")
      for b in symbols:
        sb = SECTOR_MAP.get(b.upper(), "Other")
        matrix[a][b] = 1.0 if a == b else (0.75 if sa == sb else 0.2)
    return matrix

  @staticmethod
  def _correlation_check(symbol: str, open_symbols: list[str]) -> list[str]:
    sector = SECTOR_MAP.get(symbol.upper(), "Other")
    warnings = []
    correlated = [s for s in open_symbols if SECTOR_MAP.get(s.upper()) == sector]
    if len(correlated) >= 2:
      warnings.append(f"High correlation: {len(correlated)} open positions in {sector}")
    return warnings

  async def _consecutive_losses(self, db: AsyncSession, account_id: int) -> int:
    result = await db.execute(
      select(Trade)
      .where(Trade.account_id == account_id, Trade.status == "closed")
      .order_by(Trade.closed_at.desc())
      .limit(10)
    )
    trades = result.scalars().all()
    count = 0
    for t in trades:
      if t.pnl is not None and float(t.pnl) < 0:
        count += 1
      else:
        break
    return count

  async def _get_risk_state(self, db: AsyncSession, account_id: int) -> RiskState | None:
    result = await db.execute(
      select(RiskState).where(
        RiskState.account_id == account_id,
        RiskState.trade_date == date.today(),
      )
    )
    return result.scalar_one_or_none()
