"""Portfolio intelligence — exposure, correlation, VaR, concentration risk."""

from dataclasses import asdict, dataclass, field
from decimal import Decimal

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import get_settings
from backend.app.core.logging import get_logger
from backend.app.db.models import PortfolioSnapshot, Trade
from backend.app.modules.risk.advanced import SECTOR_MAP, AdvancedRiskEngine

logger = get_logger(__name__)


@dataclass
class PositionExposure:
  symbol: str
  direction: str
  notional: float
  sector: str
  weight_pct: float


@dataclass
class PortfolioReport:
  account_id: int
  positions: list[PositionExposure] = field(default_factory=list)
  sector_exposure: dict[str, float] = field(default_factory=dict)
  correlation_matrix: dict[str, dict[str, float]] = field(default_factory=dict)
  var_95: float = 0.0
  var_99: float = 0.0
  portfolio_heat: float = 0.0
  beta_exposure: float = 1.0
  concentration_risk: list[str] = field(default_factory=list)
  risk_score: float = 0.0
  blocks: list[str] = field(default_factory=list)

  def to_dict(self) -> dict:
    return {
      "account_id": self.account_id,
      "sector_exposure": self.sector_exposure,
      "correlation_matrix": self.correlation_matrix,
      "var_95": self.var_95,
      "var_99": self.var_99,
      "portfolio_heat": self.portfolio_heat,
      "beta_exposure": self.beta_exposure,
      "concentration_risk": self.concentration_risk,
      "risk_score": self.risk_score,
      "blocks": self.blocks,
      "positions": [
        {"symbol": p.symbol, "direction": p.direction, "notional": p.notional, "sector": p.sector, "weight_pct": p.weight_pct}
        for p in self.positions
      ],
    }


class PortfolioIntelligenceEngine:
  """Portfolio-level risk aggregation and correlated trade blocking."""

  def __init__(self) -> None:
    self._settings = get_settings()
    self._risk = AdvancedRiskEngine()

  async def analyze(
    self,
    db: AsyncSession,
    account_id: int = 1,
    price_returns: dict[str, list[float]] | None = None,
  ) -> PortfolioReport:
    result = await db.execute(
      select(Trade).where(Trade.account_id == account_id, Trade.status == "open")
    )
    open_trades = list(result.scalars().all())

    capital = float(self._settings.default_account_capital)
    report = PortfolioReport(account_id=account_id)
    total_notional = 0.0
    sector_notionals: dict[str, float] = {}

    for t in open_trades:
      entry = float(t.entry_price or 0)
      notional = entry * t.quantity
      sector = SECTOR_MAP.get(t.symbol.upper(), "Other")
      weight = notional / capital * 100 if capital else 0
      report.positions.append(
        PositionExposure(t.symbol, t.direction, notional, sector, round(weight, 2))
      )
      total_notional += notional
      sector_notionals[sector] = sector_notionals.get(sector, 0) + notional

    report.portfolio_heat = round(total_notional / capital * 100, 2) if capital else 0
    report.sector_exposure = {
      s: round(v / capital * 100, 2) if capital else 0 for s, v in sector_notionals.items()
    }

    symbols = [p.symbol for p in report.positions]
    if price_returns and len(symbols) >= 2:
      report.correlation_matrix = self._correlation_matrix(price_returns, symbols)
      report.blocks.extend(self._correlation_blocks(report.correlation_matrix))

    for sector, pct in report.sector_exposure.items():
      if pct > self._settings.max_sector_exposure_pct:
        report.concentration_risk.append(f"Sector {sector} exposure {pct}% exceeds limit")
        report.blocks.append(f"sector_overexposure:{sector}")

    if report.portfolio_heat > self._settings.max_portfolio_exposure_pct:
      report.concentration_risk.append(
        f"Portfolio heat {report.portfolio_heat}% exceeds {self._settings.max_portfolio_exposure_pct}%"
      )
      report.blocks.append("portfolio_heat_exceeded")

    returns = self._portfolio_returns(price_returns, symbols) if price_returns else []
    if returns:
      arr = np.array(returns)
      report.var_95 = round(float(np.percentile(arr, 5) * capital / 100), 2)
      report.var_99 = round(float(np.percentile(arr, 1) * capital / 100), 2)
      report.beta_exposure = round(float(np.mean(arr) / (np.std(arr) + 1e-9)), 4)

    report.risk_score = self._risk_score(report)
    return report

  async def persist(self, db: AsyncSession, report: PortfolioReport) -> PortfolioSnapshot:
    row = PortfolioSnapshot(
      account_id=report.account_id,
      positions=[asdict(p) for p in report.positions],
      sector_exposure=report.sector_exposure,
      correlation_matrix=report.correlation_matrix,
      var_95=Decimal(str(report.var_95)),
      var_99=Decimal(str(report.var_99)),
      portfolio_heat=Decimal(str(report.portfolio_heat)),
      beta_exposure=Decimal(str(report.beta_exposure)),
      concentration_risk={"alerts": report.concentration_risk},
      risk_score=Decimal(str(report.risk_score)),
    )
    db.add(row)
    await db.flush()
    return row

  def should_block_new_trade(
    self,
    report: PortfolioReport,
    symbol: str,
    correlation_threshold: float = 0.85,
  ) -> tuple[bool, str | None]:
    if report.blocks:
      return True, report.blocks[0]
    sym = symbol.upper()
    if sym in report.correlation_matrix:
      for other, corr in report.correlation_matrix[sym].items():
        if other != sym and abs(corr) >= correlation_threshold:
          open_other = any(p.symbol == other for p in report.positions)
          if open_other:
            return True, f"Correlated exposure with {other} (ρ={corr:.2f})"
    return False, None

  @staticmethod
  def _correlation_matrix(returns: dict[str, list[float]], symbols: list[str]) -> dict:
    series = {}
    min_len = min(len(returns.get(s, [])) for s in symbols if s in returns)
    if min_len < 10:
      return {}
    for s in symbols:
      if s in returns and len(returns[s]) >= min_len:
        series[s] = returns[s][-min_len:]
    if len(series) < 2:
      return {}
    df = pd.DataFrame(series)
    corr = df.corr()
    return {a: {b: round(float(corr.loc[a, b]), 4) for b in corr.columns} for a in corr.index}

  @staticmethod
  def _correlation_blocks(matrix: dict) -> list[str]:
    blocks = []
    seen = set()
    for a, row in matrix.items():
      for b, c in row.items():
        if a >= b or (a, b) in seen:
          continue
        seen.add((a, b))
        if abs(c) >= 0.85:
          blocks.append(f"high_correlation:{a}:{b}:{c}")
    return blocks

  @staticmethod
  def _portfolio_returns(price_returns: dict[str, list[float]], symbols: list[str]) -> list[float]:
    if not symbols:
      return []
    mins = [price_returns.get(s, []) for s in symbols if price_returns.get(s)]
    if not mins:
      return []
    min_len = min(len(m) for m in mins)
    if min_len < 5:
      return []
    combined = np.mean([price_returns[s][-min_len:] for s in symbols if s in price_returns], axis=0)
    return list(combined)

  @staticmethod
  def _risk_score(report: PortfolioReport) -> float:
    score = min(100, report.portfolio_heat * 2)
    score += len(report.concentration_risk) * 10
    score += len(report.blocks) * 15
    return round(min(100, score), 2)
