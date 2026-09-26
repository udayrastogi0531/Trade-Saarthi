import numpy as np
import pandas as pd
import pytest

from backend.app.modules.validation.monte_carlo import MonteCarloConfig, MonteCarloRiskEngine
from backend.app.modules.validation.walk_forward import WalkForwardEngine
from backend.app.modules.data_quality.engine import DataQualityEngine
from backend.app.modules.analytics.institutional import InstitutionalAnalyticsEngine


@pytest.fixture
def ohlcv_df(sample_ohlcv):
  return sample_ohlcv


def test_walk_forward_produces_report(ohlcv_df):
  engine = WalkForwardEngine()
  report = engine.run(ohlcv_df, "RELIANCE", windows=3)
  assert report.symbol == "RELIANCE"
  assert 0 <= report.stability_score <= 1.0


def test_monte_carlo_ruin_probability():
  pnls = [500, -300, 400, -200, -150, 600, -400] * 5
  report = MonteCarloRiskEngine().simulate(pnls, MonteCarloConfig(simulations=200))
  assert 0 <= report.probability_of_ruin <= 1
  assert report.survival_probability == pytest.approx(1 - report.probability_of_ruin, abs=0.01)


def test_data_quality_rejects_empty():
  report = DataQualityEngine().validate_candles(pd.DataFrame(), "X")
  assert not report.healthy


def test_institutional_metrics():
  pnls = [100, -50, 80, -40, 120, -60]
  m = InstitutionalAnalyticsEngine().compute(pnls)
  assert m.total_trades == 6
  assert m.win_rate > 0
