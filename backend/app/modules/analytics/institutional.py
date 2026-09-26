"""Hedge-fund style performance analytics."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from backend.app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class InstitutionalMetrics:
  sharpe_ratio: float = 0.0
  sortino_ratio: float = 0.0
  calmar_ratio: float = 0.0
  profit_factor: float = 0.0
  expectancy: float = 0.0
  recovery_factor: float = 0.0
  max_drawdown_pct: float = 0.0
  win_rate: float = 0.0
  max_consecutive_losses: int = 0
  avg_mae: float = 0.0
  avg_mfe: float = 0.0
  risk_adjusted_return: float = 0.0
  total_trades: int = 0

  def to_dict(self) -> dict:
    return self.__dict__.copy()


class InstitutionalAnalyticsEngine:
  """Compute institutional-grade metrics from trade PnL series."""

  def compute(
    self,
    pnls: list[float],
    maes: list[float] | None = None,
    mfes: list[float] | None = None,
    initial_capital: float = 100_000,
  ) -> InstitutionalMetrics:
    if not pnls:
      return InstitutionalMetrics()

    arr = np.array(pnls)
    wins = arr[arr > 0]
    losses = arr[arr < 0]
    returns = arr / initial_capital

    equity = initial_capital + np.cumsum(arr)
    peak = np.maximum.accumulate(equity)
    drawdown = (peak - equity) / peak * 100
    max_dd = float(np.max(drawdown)) if len(drawdown) else 0

    sharpe = self._sharpe(returns)
    sortino = self._sortino(returns)
    total_return = float(arr.sum() / initial_capital * 100)
    calmar = total_return / max(max_dd, 0.01)
    pf = float(wins.sum() / abs(losses.sum())) if len(losses) and losses.sum() != 0 else 0
    expectancy = float(arr.mean())
    recovery = total_return / max(max_dd, 0.01)

    streak = 0
    max_streak = 0
    for p in pnls:
      if p < 0:
        streak += 1
        max_streak = max(max_streak, streak)
      else:
        streak = 0

    return InstitutionalMetrics(
      sharpe_ratio=round(sharpe, 3),
      sortino_ratio=round(sortino, 3),
      calmar_ratio=round(calmar, 3),
      profit_factor=round(pf, 3),
      expectancy=round(expectancy, 2),
      recovery_factor=round(recovery, 3),
      max_drawdown_pct=round(max_dd, 3),
      win_rate=round(len(wins) / len(arr) * 100, 2),
      max_consecutive_losses=max_streak,
      avg_mae=round(float(np.mean(maes)), 2) if maes else 0,
      avg_mfe=round(float(np.mean(mfes)), 2) if mfes else 0,
      risk_adjusted_return=round(total_return / max(max_dd, 0.01), 3),
      total_trades=len(pnls),
    )

  def rolling_series(self, pnls: list[float], window: int = 20) -> dict:
    if len(pnls) < window:
      return {"sharpe": [], "win_rate": [], "expectancy": []}
    sharpes, wrs, exps = [], [], []
    for i in range(window, len(pnls) + 1):
      chunk = pnls[i - window : i]
      m = self.compute(chunk)
      sharpes.append(m.sharpe_ratio)
      wrs.append(m.win_rate)
      exps.append(m.expectancy)
    return {"sharpe": sharpes, "win_rate": wrs, "expectancy": exps}

  @staticmethod
  def _sharpe(returns: np.ndarray, rf: float = 0.0) -> float:
    if len(returns) < 2 or returns.std() == 0:
      return 0.0
    return float((returns.mean() - rf) / returns.std() * np.sqrt(252))

  @staticmethod
  def _sortino(returns: np.ndarray, target: float = 0.0) -> float:
    downside = returns[returns < target]
    if len(downside) < 2 or downside.std() == 0:
      return 0.0
    return float((returns.mean() - target) / downside.std() * np.sqrt(252))
