"""Monte Carlo risk engine — ruin probability, drawdown distribution, stress tests."""

from dataclasses import dataclass, field
from decimal import Decimal

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import get_settings
from backend.app.core.logging import get_logger
from backend.app.db.models import MonteCarloRun

logger = get_logger(__name__)


@dataclass
class MonteCarloConfig:
  simulations: int = 2000
  initial_capital: float = 100_000
  risk_per_trade_pct: float = 1.0
  slippage_bps: float = 8.0
  gap_shock_pct: float = 2.0
  execution_failure_rate: float = 0.02
  max_losing_streak: int = 10
  ruin_drawdown_pct: float = 25.0


@dataclass
class MonteCarloReport:
  probability_of_ruin: float
  survival_probability: float
  worst_drawdown_pct: float
  expected_drawdown_pct: float
  tail_risk_var_99: float
  drawdown_distribution: dict
  stress_scenarios: dict
  losing_streak_distribution: dict
  warnings: list[str] = field(default_factory=list)

  def to_dict(self) -> dict:
    return {
      "probability_of_ruin": self.probability_of_ruin,
      "survival_probability": self.survival_probability,
      "worst_drawdown_pct": self.worst_drawdown_pct,
      "expected_drawdown_pct": self.expected_drawdown_pct,
      "tail_risk_var_99": self.tail_risk_var_99,
      "drawdown_distribution": self.drawdown_distribution,
      "stress_scenarios": self.stress_scenarios,
      "losing_streak_distribution": self.losing_streak_distribution,
      "warnings": self.warnings,
    }


class MonteCarloRiskEngine:
  """Institutional Monte Carlo — streaks, slippage, gaps, execution failures."""

  def __init__(self) -> None:
    self._settings = get_settings()

  def simulate(
    self,
    trade_pnls: list[float],
    config: MonteCarloConfig | None = None,
  ) -> MonteCarloReport:
    config = config or MonteCarloConfig(
      simulations=self._settings.monte_carlo_simulations,
      ruin_drawdown_pct=self._settings.monte_carlo_ruin_threshold_pct,
    )

    if not trade_pnls:
      return MonteCarloReport(
        probability_of_ruin=0.0,
        survival_probability=1.0,
        worst_drawdown_pct=0.0,
        expected_drawdown_pct=0.0,
        tail_risk_var_99=0.0,
        drawdown_distribution={},
        stress_scenarios={},
        losing_streak_distribution={},
        warnings=["No trade PnL history — simulation uses synthetic bootstrap only if provided"],
      )

    rng = np.random.default_rng(42)
    n_trades = len(trade_pnls)
    ruin_count = 0
    max_drawdowns: list[float] = []
    final_returns: list[float] = []
    max_streaks: list[int] = []

    slippage_cost = config.initial_capital * (config.slippage_bps / 10000)

    for _ in range(config.simulations):
      equity = config.initial_capital
      peak = equity
      max_dd = 0.0
      streak = 0
      max_streak = 0

      order = rng.permutation(n_trades)
      for idx in order:
        if rng.random() < config.execution_failure_rate:
          continue
        pnl = trade_pnls[idx]
        pnl -= slippage_cost
        if rng.random() < 0.05:
          pnl -= config.initial_capital * (config.gap_shock_pct / 100)
        equity += pnl
        peak = max(peak, equity)
        dd = (peak - equity) / peak * 100 if peak > 0 else 0
        max_dd = max(max_dd, dd)
        if pnl < 0:
          streak += 1
          max_streak = max(max_streak, streak)
        else:
          streak = 0

      max_drawdowns.append(max_dd)
      final_returns.append((equity - config.initial_capital) / config.initial_capital * 100)
      max_streaks.append(max_streak)
      if max_dd >= config.ruin_drawdown_pct:
        ruin_count += 1

    ruin_prob = ruin_count / config.simulations
    report = MonteCarloReport(
      probability_of_ruin=round(ruin_prob, 6),
      survival_probability=round(1 - ruin_prob, 6),
      worst_drawdown_pct=round(float(np.max(max_drawdowns)), 4),
      expected_drawdown_pct=round(float(np.mean(max_drawdowns)), 4),
      tail_risk_var_99=round(float(np.percentile(final_returns, 1)), 4),
      drawdown_distribution={
        "p50": round(float(np.percentile(max_drawdowns, 50)), 4),
        "p75": round(float(np.percentile(max_drawdowns, 75)), 4),
        "p95": round(float(np.percentile(max_drawdowns, 95)), 4),
        "p99": round(float(np.percentile(max_drawdowns, 99)), 4),
      },
      stress_scenarios=self._stress_scenarios(trade_pnls, config),
      losing_streak_distribution={
        "mean": round(float(np.mean(max_streaks)), 2),
        "p95": round(float(np.percentile(max_streaks, 95)), 2),
        "max": int(np.max(max_streaks)),
      },
    )

    if ruin_prob > 0.15:
      report.warnings.append(f"Elevated ruin probability ({ruin_prob:.1%}) — reduce risk per trade")
    if report.expected_drawdown_pct > 15:
      report.warnings.append("Expected drawdown exceeds conservative institutional threshold")

    logger.info("monte_carlo_complete", ruin=ruin_prob, survival=report.survival_probability)
    return report

  async def persist(
    self,
    db: AsyncSession,
    report: MonteCarloReport,
    config: MonteCarloConfig,
    account_id: int = 1,
    strategy_name: str | None = None,
  ) -> MonteCarloRun:
    row = MonteCarloRun(
      account_id=account_id,
      strategy_name=strategy_name,
      simulations=config.simulations,
      config={
        "initial_capital": config.initial_capital,
        "slippage_bps": config.slippage_bps,
        "gap_shock_pct": config.gap_shock_pct,
        "execution_failure_rate": config.execution_failure_rate,
      },
      probability_of_ruin=Decimal(str(report.probability_of_ruin)),
      worst_drawdown_pct=Decimal(str(report.worst_drawdown_pct)),
      expected_drawdown_pct=Decimal(str(report.expected_drawdown_pct)),
      survival_probability=Decimal(str(report.survival_probability)),
      tail_risk_var_99=Decimal(str(report.tail_risk_var_99)),
      drawdown_distribution=report.drawdown_distribution,
      stress_scenarios=report.stress_scenarios,
      report=report.to_dict(),
    )
    db.add(row)
    await db.flush()
    return row

  @staticmethod
  def _stress_scenarios(pnls: list[float], config: MonteCarloConfig) -> dict:
    arr = np.array(pnls)
    return {
      "volatility_spike": {
        "description": "2x adverse variance on losses",
        "expected_impact_pct": round(float(arr[arr < 0].sum() * 2 / config.initial_capital * 100), 2)
        if len(arr[arr < 0]) else 0,
      },
      "slippage_shock": {
        "description": f"{config.slippage_bps * 3} bps slippage per trade",
        "cost_estimate": round(len(pnls) * config.initial_capital * (config.slippage_bps * 3 / 10000), 2),
      },
      "losing_streak_10": {
        "description": "10 consecutive losses at 1% risk",
        "drawdown_estimate_pct": round(min(10 * config.risk_per_trade_pct, config.ruin_drawdown_pct), 2),
      },
    }
