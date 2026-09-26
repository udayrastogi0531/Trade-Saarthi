from backend.app.modules.market_structure.engine import MarketStructureEngine


def test_market_structure_analysis(sample_ohlcv):
  engine = MarketStructureEngine()
  result = engine.analyze(sample_ohlcv, "RELIANCE", "15m")
  assert result.structure_confidence >= 0
  assert result.trend_direction in ("bullish", "bearish", "neutral")
  assert 0 <= result.fake_breakout_risk <= 1
  assert result.explanation


def test_breakout_validation(sample_ohlcv):
  engine = MarketStructureEngine()
  analysis = engine.analyze(sample_ohlcv, "X", "15m")
  ok, reason = engine.is_breakout_valid(analysis, "BUY")
  assert isinstance(ok, bool)
  assert isinstance(reason, str)
