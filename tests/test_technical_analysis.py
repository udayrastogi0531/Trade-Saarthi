from backend.app.modules.technical_analysis.engine import TechnicalAnalysisEngine


def test_technical_snapshot(sample_ohlcv):
  engine = TechnicalAnalysisEngine()
  snap = engine.analyze(sample_ohlcv, "RELIANCE", "15m")

  assert 0 <= snap.rsi <= 100
  assert snap.trend_direction in ("bullish", "bearish", "neutral")
  assert snap.atr > 0
  assert isinstance(snap.volume_spike, bool)


def test_multi_timeframe_confirm(sample_ohlcv):
  engine = TechnicalAnalysisEngine()
  snap = engine.analyze(sample_ohlcv, "RELIANCE", "15m")
  snapshots = {"15m": snap, "1h": snap}
  confirmed, reasons = engine.multi_timeframe_confirm(snapshots, "bullish")
  assert isinstance(confirmed, bool)
  assert isinstance(reasons, list)
