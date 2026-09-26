"""Backtesting Engine — VectorBT-based historical performance analysis."""

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from backend.app.core.logging import get_logger
from backend.app.modules.strategy.engine import StrategyEngine
from backend.app.modules.technical_analysis.engine import TechnicalAnalysisEngine

logger = get_logger(__name__)


@dataclass
class BacktestMetrics:
  total_trades: int
  win_rate: float
  profit_factor: float
  sharpe_ratio: float
  max_drawdown_pct: float
  expectancy: float
  total_return_pct: float
  avg_win: float
  avg_loss: float

  def to_dict(self) -> dict:
    return asdict(self)


class BacktestEngine:
  """
  Walk-forward backtest using strategy rules on historical OHLCV.
  Uses simplified bar-by-bar simulation (VectorBT optional for advanced runs).
  """

  def __init__(self) -> None:
    self._strategy = StrategyEngine()
    self._ta = TechnicalAnalysisEngine()

  def run(
    self,
    df: pd.DataFrame,
    symbol: str,
    timeframe: str = "15m",
    initial_capital: float = 100_000,
    risk_per_trade_pct: float = 1.0,
  ) -> tuple[BacktestMetrics, list[dict]]:
    trades_log: list[dict] = []
    equity = initial_capital
    equity_curve = [equity]
    wins: list[float] = []
    losses: list[float] = []

    window = 60
    for i in range(window, len(df) - 1):
      segment = df.iloc[: i + 1].copy()
      result = self._strategy.evaluate(symbol, segment, timeframe)

      if not result.approved or not result.setup:
        equity_curve.append(equity)
        continue

      setup = result.setup
      next_bar = df.iloc[i + 1]
      entry = setup.entry
      risk = abs(entry - setup.stop_loss)

      risk_amount = equity * (risk_per_trade_pct / 100)
      qty = int(risk_amount / risk) if risk > 0 else 0
      if qty < 1:
        equity_curve.append(equity)
        continue

      exit_price, outcome = self._simulate_exit(setup, next_bar, df.iloc[i + 1 : i + 10])

      if setup.direction == "BUY":
        pnl = (exit_price - entry) * qty
      else:
        pnl = (entry - exit_price) * qty

      equity += pnl
      equity_curve.append(equity)

      record = {
        "bar": i,
        "direction": setup.direction,
        "entry": entry,
        "exit": exit_price,
        "pnl": pnl,
        "outcome": outcome,
        "setup_type": setup.setup_type,
      }
      trades_log.append(record)

      if pnl > 0:
        wins.append(pnl)
      else:
        losses.append(abs(pnl))

    metrics = self._compute_metrics(equity_curve, wins, losses, initial_capital)
    logger.info("backtest_complete", symbol=symbol, trades=metrics.total_trades)
    return metrics, trades_log

  @staticmethod
  def _simulate_exit(setup, bar, forward_bars) -> tuple[float, str]:
    sl = setup.stop_loss
    target = setup.target

    for _, row in forward_bars.iterrows():
      if setup.direction == "BUY":
        if row["low"] <= sl:
          return sl, "stop_loss"
        if row["high"] >= target:
          return target, "target"
      else:
        if row["high"] >= sl:
          return sl, "stop_loss"
        if row["low"] <= target:
          return target, "target"

    return float(bar["close"]), "timeout"

  @staticmethod
  def _compute_metrics(
    equity_curve: list[float],
    wins: list[float],
    losses: list[float],
    initial_capital: float,
  ) -> BacktestMetrics:
    total_trades = len(wins) + len(losses)
    win_rate = len(wins) / total_trades * 100 if total_trades else 0
    gross_profit = sum(wins)
    gross_loss = sum(losses) or 1e-9
    profit_factor = gross_profit / gross_loss

    returns = pd.Series(equity_curve).pct_change().dropna()
    sharpe = (
      float(returns.mean() / returns.std() * np.sqrt(252))
      if len(returns) > 1 and returns.std() > 0
      else 0.0
    )

    eq = pd.Series(equity_curve)
    peak = eq.cummax()
    drawdown = (eq - peak) / peak * 100
    max_dd = float(abs(drawdown.min())) if len(drawdown) else 0

    avg_win = float(np.mean(wins)) if wins else 0
    avg_loss = float(np.mean(losses)) if losses else 0
    expectancy = (win_rate / 100 * avg_win) - ((100 - win_rate) / 100 * avg_loss)

    final = equity_curve[-1] if equity_curve else initial_capital
    total_return = (final - initial_capital) / initial_capital * 100

    return BacktestMetrics(
      total_trades=total_trades,
      win_rate=round(win_rate, 2),
      profit_factor=round(profit_factor, 2),
      sharpe_ratio=round(sharpe, 2),
      max_drawdown_pct=round(max_dd, 2),
      expectancy=round(expectancy, 2),
      total_return_pct=round(total_return, 2),
      avg_win=round(avg_win, 2),
      avg_loss=round(avg_loss, 2),
    )
