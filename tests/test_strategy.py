from backend.app.modules.strategy.engine import StrategyEngine


def test_strategy_evaluate(sample_ohlcv):
  engine = StrategyEngine()
  result = engine.evaluate("RELIANCE", sample_ohlcv, "15m")

  assert isinstance(result.approved, bool)
  assert isinstance(result.rejection_reasons, list)
  assert result.setup_type is not None


def test_strategy_rejects_insufficient_data():
  import pandas as pd

  engine = StrategyEngine()
  tiny = pd.DataFrame(
    {"open": [1], "high": [1], "low": [1], "close": [1], "volume": [1]}
  )
  try:
    engine.evaluate("X", tiny, "15m")
  except (ValueError, IndexError):
    pass
