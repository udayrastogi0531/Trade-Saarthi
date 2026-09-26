from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class TradeSetup(BaseModel):
  symbol: str
  direction: Literal["BUY", "SELL"]
  entry: float
  stop_loss: float
  target: float
  risk_reward: float
  position_size: int
  position_value: float
  risk_amount: float
  confidence: float = Field(ge=0, le=100)
  setup_type: str
  timeframe: str


class SignalRequest(BaseModel):
  symbol: str = Field(..., examples=["RELIANCE"])
  exchange: Literal["NSE", "BSE"] = "NSE"
  account_id: int = 1
  capital: float | None = None
  include_ai_reasoning: bool = True


class SignalResponse(BaseModel):
  approved: bool
  setup: TradeSetup | None = None
  rejection_reasons: list[str] = []
  technical_summary: dict = {}
  risk_check: dict = {}
  ai_reasoning: "AIReasoningResponse | None" = None
  generated_at: datetime


class AIReasoningResponse(BaseModel):
  trade_valid: bool
  confidence_score: float
  market_summary: str
  trend_structure: str
  volume_analysis: str
  risk_flags: list[str]
  fake_breakout_probability: float = Field(ge=0, le=1)
  explanation: str
  disclaimer: str = (
    "This is probabilistic analysis, not financial advice. "
    "Past performance does not guarantee future results."
  )


SignalResponse.model_rebuild()
