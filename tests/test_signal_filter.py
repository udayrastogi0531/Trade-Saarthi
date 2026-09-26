from backend.app.modules.market_regime.engine import RegimeEngine
from backend.app.modules.mtf_analysis.engine import MTFAnalysisEngine
from backend.app.modules.signal_filter.engine import SignalFilterEngine
from backend.app.modules.technical_analysis.engine import TechnicalAnalysisEngine
from backend.app.schemas.trade import TradeSetup


def test_signal_filter(sample_ohlcv):
  ta = TechnicalAnalysisEngine()
  snap = ta.analyze(sample_ohlcv, "RELIANCE", "15m")
  regime = RegimeEngine().detect(sample_ohlcv, "RELIANCE", snap)
  mtf = MTFAnalysisEngine().analyze({"15m": snap}, "BUY")

  setup = TradeSetup(
    symbol="RELIANCE",
    direction="BUY",
    entry=100,
    stop_loss=98,
    target=106,
    risk_reward=3,
    position_size=10,
    position_value=1000,
    risk_amount=20,
    confidence=80,
    setup_type="pullback",
    timeframe="15m",
  )
  result = SignalFilterEngine().evaluate(setup, snap, regime, mtf)
  assert hasattr(result, "quality_score")
  assert isinstance(result.passed, bool)
