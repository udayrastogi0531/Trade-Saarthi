from backend.app.modules.risk.engine import RiskEngine
from backend.app.schemas.trade import TradeSetup


def test_position_sizing_logic():
  setup = TradeSetup(
    symbol="RELIANCE",
    direction="BUY",
    entry=100.0,
    stop_loss=98.0,
    target=106.0,
    risk_reward=3.0,
    position_size=0,
    position_value=0,
    risk_amount=0,
    confidence=75,
    setup_type="breakout",
    timeframe="15m",
  )

  risk_per_share = abs(setup.entry - setup.stop_loss)
  capital = 100_000
  max_risk = capital * 0.05
  qty = int(max_risk / risk_per_share)

  assert qty > 0
  assert risk_per_share == 2.0
