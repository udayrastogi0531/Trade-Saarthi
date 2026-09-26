from backend.app.modules.mtf_analysis.engine import MTFAnalysisEngine
from backend.app.modules.technical_analysis.engine import TechnicalAnalysisEngine


def test_mtf_alignment(sample_ohlcv):
  ta = TechnicalAnalysisEngine()
  snapshots = {
    "5m": ta.analyze(sample_ohlcv, "X", "5m"),
    "15m": ta.analyze(sample_ohlcv, "X", "15m"),
    "1h": ta.analyze(sample_ohlcv, "X", "1h"),
  }
  result = MTFAnalysisEngine().analyze(snapshots, "BUY")
  assert 0 <= result.alignment_score <= 1
  assert result.dominant_trend in ("bullish", "bearish", "neutral")
