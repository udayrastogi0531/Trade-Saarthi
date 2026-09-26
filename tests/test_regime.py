from backend.app.modules.market_regime.engine import RegimeEngine, RegimeType


def test_regime_detection(sample_ohlcv):
  from backend.app.modules.technical_analysis.engine import TechnicalAnalysisEngine

  ta = TechnicalAnalysisEngine()
  snap = ta.analyze(sample_ohlcv, "RELIANCE", "15m")
  regime = RegimeEngine().detect(sample_ohlcv, "RELIANCE", snap)

  assert isinstance(regime.regime, RegimeType)
  assert 0 <= regime.confidence <= 100
  assert isinstance(regime.allowed_setups, list)
