from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class OHLCVBar(BaseModel):
  timestamp: datetime
  open: float
  high: float
  low: float
  close: float
  volume: float


class CandleRequest(BaseModel):
  symbol: str = Field(..., min_length=1, max_length=32, examples=["RELIANCE"])
  exchange: Literal["NSE", "BSE"] = "NSE"
  interval: Literal["1m", "5m", "15m", "1h", "4h", "1d"] = "15m"
  limit: int = Field(default=200, ge=10, le=1000)


class MultiTimeframeRequest(BaseModel):
  symbol: str
  exchange: Literal["NSE", "BSE"] = "NSE"
  intervals: list[Literal["5m", "15m", "1h", "4h", "1d"]] = ["5m", "15m", "1h", "4h", "1d"]
