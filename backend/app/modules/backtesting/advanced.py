"""Advanced backtesting — walk-forward, Monte Carlo, slippage, commission."""

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from backend.app.core.logging import get_logger
from backend.app.modules.backtesting.engine import BacktestEngine, BacktestMetrics

logger = get_logger(__name__)


@dataclass
class AdvancedBacktestMetrics(BacktestMetrics):
  sortino_ratio: float = 0.0
  calmar_ratio: float = 0.0
  recovery_factor: float = 0.0
  monte_carlo_var_95: float = 0.0
  monte_carlo_median_return: float = 0.0
  oos_win_rate: float = 0.0
  slippage_cost_total: float = 0.0
  commission_cost_total: float = 0.0

  def to_dict(self) -> dict:
    return asdict(self)


class AdvancedBacktestEngine(BacktestEngine):
  """Walk-forward, out-of-sample, Monte Carlo — no lookahead bias."""

  def run_advanced(
    self,
    df: pd.DataFrame,
    symbol: str,
    timeframe: str = "15m",
    initial_capital: float = 100_000,
    risk_per_trade_pct: float = 1.0,
    slippage_bps: float = 5.0,
    commission_per_trade: float = 20.0,
    walk_forward_splits: int = 4,
    monte_carlo_runs: int = 500,
    oos_pct: float = 0.2,
  ) -> tuple[AdvancedBacktestMetrics, dict]:
    in_sample_end = int(len(df) * (1 - oos_pct))
    is_df = df.iloc[:in_sample_end].copy()
    oos_df = df.iloc[in_sample_end:].copy()

    is_metrics, is_trades = self.run(
      is_df, symbol, timeframe, initial_capital, risk_per_trade_pct
    )
    oos_metrics, oos_trades = self.run(
      oos_df, symbol, timeframe, initial_capital, risk_per_trade_pct
    ) if len(oos_df) > 80 else (is_metrics, [])

    wf_results = []
    split_size = len(df) // walk_forward_splits
    for i in range(walk_forward_splits - 1):
      start = i * split_size
      end = start + split_size + split_size // 2
      segment = df.iloc[start:end]
      if len(segment) < 80:
        continue
      m, _ = self.run(segment, symbol, timeframe, initial_capital, risk_per_trade_pct)
      wf_results.append(m.win_rate)

    pnls = [t["pnl"] for t in is_trades]
    slippage_total = len(is_trades) * (slippage_bps / 10000) * initial_capital
    commission_total = len(is_trades) * commission_per_trade

    adjusted_pnls = [p - commission_per_trade - slippage_total / max(len(is_trades), 1) for p in pnls]
    returns = pd.Series(adjusted_pnls) / initial_capital if adjusted_pnls else pd.Series([0.0])

    sortino = self._sortino(returns)
    calmar = is_metrics.total_return_pct / max(is_metrics.max_drawdown_pct, 0.01)
    recovery = is_metrics.total_return_pct / max(is_metrics.max_drawdown_pct, 0.01)

    mc_returns = self._monte_carlo(adjusted_pnls, initial_capital, monte_carlo_runs)

    advanced = AdvancedBacktestMetrics(
      **is_metrics.to_dict(),
      sortino_ratio=round(sortino, 2),
      calmar_ratio=round(calmar, 2),
      recovery_factor=round(recovery, 2),
      monte_carlo_var_95=round(float(np.percentile(mc_returns, 5)), 2),
      monte_carlo_median_return=round(float(np.median(mc_returns)), 2),
      oos_win_rate=oos_metrics.win_rate,
      slippage_cost_total=round(slippage_total, 2),
      commission_cost_total=round(commission_total, 2),
    )

    detail = {
      "walk_forward_win_rates": wf_results,
      "in_sample_trades": len(is_trades),
      "oos_trades": len(oos_trades),
      "sample_trades": is_trades[-10:],
    }
    logger.info("advanced_backtest_complete", symbol=symbol, sharpe=advanced.sharpe_ratio)
    return advanced, detail

  @staticmethod
  def _sortino(returns: pd.Series, target: float = 0.0) -> float:
    downside = returns[returns < target]
    if len(downside) == 0 or downside.std() == 0:
      return 0.0
    return float((returns.mean() - target) / downside.std() * np.sqrt(252))

  @staticmethod
  def _monte_carlo(pnls: list[float], capital: float, runs: int) -> np.ndarray:
    if not pnls:
      return np.zeros(runs)
    rng = np.random.default_rng(42)
    results = []
    for _ in range(runs):
      sample = rng.choice(pnls, size=len(pnls), replace=True)
      total_return = sum(sample) / capital * 100
      results.append(total_return)
    return np.array(results)
