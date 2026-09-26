"""Walk-forward validation — rolling OOS testing, overfitting & decay detection."""

from dataclasses import dataclass, field
from decimal import Decimal
from uuid import uuid4

import numpy as np
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import get_settings
from backend.app.core.logging import get_logger
from backend.app.db.models import WalkForwardRun
from backend.app.modules.backtesting.engine import BacktestEngine

logger = get_logger(__name__)


@dataclass
class WindowMetrics:
  window_index: int
  in_sample: dict
  out_of_sample: dict
  sharpe_gap: float
  win_rate_gap: float


@dataclass
class WalkForwardReport:
  strategy_name: str
  symbol: str
  windows: list[WindowMetrics] = field(default_factory=list)
  rolling_sharpe: list[float] = field(default_factory=list)
  rolling_expectancy: list[float] = field(default_factory=list)
  rolling_drawdown: list[float] = field(default_factory=list)
  rolling_win_rate: list[float] = field(default_factory=list)
  stability_score: float = 0.0
  overfitting_flag: bool = False
  decay_detected: bool = False
  aggregate_is: dict = field(default_factory=dict)
  aggregate_oos: dict = field(default_factory=dict)
  regime_breakdown: dict = field(default_factory=dict)
  warnings: list[str] = field(default_factory=list)

  def to_dict(self) -> dict:
    return {
      "strategy_name": self.strategy_name,
      "symbol": self.symbol,
      "stability_score": self.stability_score,
      "overfitting_flag": self.overfitting_flag,
      "decay_detected": self.decay_detected,
      "rolling_sharpe": self.rolling_sharpe,
      "rolling_expectancy": self.rolling_expectancy,
      "rolling_drawdown": self.rolling_drawdown,
      "rolling_win_rate": self.rolling_win_rate,
      "aggregate_in_sample": self.aggregate_is,
      "aggregate_out_of_sample": self.aggregate_oos,
      "regime_breakdown": self.regime_breakdown,
      "warnings": self.warnings,
      "windows": [
        {
          "index": w.window_index,
          "in_sample": w.in_sample,
          "out_of_sample": w.out_of_sample,
          "sharpe_gap": w.sharpe_gap,
          "win_rate_gap": w.win_rate_gap,
        }
        for w in self.windows
      ],
    }


class WalkForwardEngine:
  """Professional walk-forward analysis with stability and decay metrics."""

  def __init__(self) -> None:
    self._backtest = BacktestEngine()
    self._settings = get_settings()

  def run(
    self,
    df: pd.DataFrame,
    symbol: str,
    strategy_name: str = "default",
    windows: int | None = None,
    train_pct: float | None = None,
    oos_pct: float | None = None,
    initial_capital: float = 100_000,
  ) -> WalkForwardReport:
    windows = windows or self._settings.walk_forward_windows
    train_pct = train_pct or self._settings.walk_forward_train_pct
    oos_pct = oos_pct or self._settings.walk_forward_oos_pct

    report = WalkForwardReport(strategy_name=strategy_name, symbol=symbol)
    n = len(df)
    if n < 200:
      report.warnings.append("Insufficient data for reliable walk-forward validation")
      return report

    window_size = n // windows
    min_bars = 80

    for i in range(windows):
      start = i * window_size
      train_end = start + int(window_size * train_pct)
      oos_end = min(start + window_size, n)
      if train_end - start < min_bars or oos_end - train_end < min_bars // 2:
        continue

      train_df = df.iloc[start:train_end]
      oos_df = df.iloc[train_end:oos_end]

      is_m, _ = self._backtest.run(train_df, symbol, "15m", initial_capital)
      oos_m, _ = self._backtest.run(oos_df, symbol, "15m", initial_capital)

      is_dict = is_m.to_dict()
      oos_dict = oos_m.to_dict()
      sharpe_gap = is_dict.get("sharpe_ratio", 0) - oos_dict.get("sharpe_ratio", 0)
      wr_gap = is_dict.get("win_rate", 0) - oos_dict.get("win_rate", 0)

      wm = WindowMetrics(
        window_index=i,
        in_sample=is_dict,
        out_of_sample=oos_dict,
        sharpe_gap=round(sharpe_gap, 3),
        win_rate_gap=round(wr_gap, 3),
      )
      report.windows.append(wm)
      report.rolling_sharpe.append(oos_dict.get("sharpe_ratio", 0))
      report.rolling_expectancy.append(oos_dict.get("expectancy", 0))
      report.rolling_drawdown.append(oos_dict.get("max_drawdown_pct", 0))
      report.rolling_win_rate.append(oos_dict.get("win_rate", 0))

    if not report.windows:
      report.warnings.append("No valid walk-forward windows produced")
      return report

    report.aggregate_is = self._aggregate([w.in_sample for w in report.windows])
    report.aggregate_oos = self._aggregate([w.out_of_sample for w in report.windows])
    report.stability_score = self._stability_score(report.rolling_sharpe, report.rolling_win_rate)
    report.overfitting_flag = self._detect_overfitting(report.windows)
    report.decay_detected = self._detect_decay(report.rolling_win_rate)
    report.regime_breakdown = {"note": "Regime tagging requires trade-level regime labels"}

    if report.overfitting_flag:
      report.warnings.append(
        "Overfitting detected: in-sample performance significantly exceeds out-of-sample"
      )
    if report.decay_detected:
      report.warnings.append("Strategy decay: recent OOS win rate declining vs earlier windows")
    if report.stability_score < 0.4:
      report.warnings.append("Low parameter stability across rolling windows")

    logger.info(
      "walk_forward_complete",
      symbol=symbol,
      stability=report.stability_score,
      overfit=report.overfitting_flag,
    )
    return report

  async def persist(self, db: AsyncSession, report: WalkForwardReport, parameters: dict | None = None) -> WalkForwardRun:
    settings = get_settings()
    row = WalkForwardRun(
      strategy_name=report.strategy_name,
      symbol=report.symbol,
      parameters=parameters,
      window_config={
        "windows": settings.walk_forward_windows,
        "train_pct": settings.walk_forward_train_pct,
        "oos_pct": settings.walk_forward_oos_pct,
      },
      in_sample_metrics=report.aggregate_is,
      out_of_sample_metrics=report.aggregate_oos,
      rolling_metrics={
        "sharpe": report.rolling_sharpe,
        "expectancy": report.rolling_expectancy,
        "drawdown": report.rolling_drawdown,
        "win_rate": report.rolling_win_rate,
      },
      stability_score=Decimal(str(round(report.stability_score, 4))),
      overfitting_flag=report.overfitting_flag,
      decay_detected=report.decay_detected,
      regime_breakdown=report.regime_breakdown,
      report=report.to_dict(),
    )
    db.add(row)
    await db.flush()
    return row

  @staticmethod
  def _aggregate(metrics_list: list[dict]) -> dict:
    if not metrics_list:
      return {}
    keys = ["win_rate", "sharpe_ratio", "profit_factor", "max_drawdown_pct", "expectancy", "total_trades"]
    out = {}
    for k in keys:
      vals = [m.get(k, 0) for m in metrics_list if k in m]
      out[k] = round(float(np.mean(vals)), 4) if vals else 0
    return out

  @staticmethod
  def _stability_score(sharpes: list[float], win_rates: list[float]) -> float:
    if len(sharpes) < 2:
      return 0.5
    sharpe_cv = np.std(sharpes) / (abs(np.mean(sharpes)) + 0.01)
    wr_cv = np.std(win_rates) / (abs(np.mean(win_rates)) + 0.01)
    instability = min(1.0, (sharpe_cv + wr_cv) / 2)
    return round(max(0.0, 1.0 - instability), 4)

  def _detect_overfitting(self, windows: list[WindowMetrics]) -> bool:
    threshold = self._settings.overfitting_sharpe_gap_threshold
    gaps = [w.sharpe_gap for w in windows]
    return bool(gaps and np.mean(gaps) > threshold)

  def _detect_decay(self, rolling_wr: list[float]) -> bool:
    if len(rolling_wr) < 3:
      return False
    drop = self._settings.strategy_decay_win_rate_drop
    early = np.mean(rolling_wr[: len(rolling_wr) // 2])
    late = np.mean(rolling_wr[len(rolling_wr) // 2 :])
    return early - late > drop
