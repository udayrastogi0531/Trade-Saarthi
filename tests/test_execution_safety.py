from backend.app.modules.execution.safety import ExecutionSafetyEngine
from backend.app.schemas.trade import TradeSetup


def test_safety_engine_instantiates():
  engine = ExecutionSafetyEngine()
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
    confidence=75,
    setup_type="breakout",
    timeframe="15m",
  )
  assert engine is not None
  assert setup.symbol == "RELIANCE"
