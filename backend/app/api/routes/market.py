from fastapi import APIRouter, HTTPException, Query

from backend.app.core.exceptions import MarketDataError, http_exception_from_domain
from backend.app.modules.market_data.engine import MarketDataEngine
from backend.app.schemas.market import CandleRequest, MultiTimeframeRequest, OHLCVBar

router = APIRouter(prefix="/market", tags=["Market Data"])


@router.post("/candles", response_model=list[OHLCVBar])
async def get_candles(request: CandleRequest) -> list[OHLCVBar]:
  engine = MarketDataEngine()
  try:
    df = await engine.get_candles(request)
  except MarketDataError as exc:
    raise http_exception_from_domain(exc) from exc

  return [
    OHLCVBar(
      timestamp=row["timestamp"].to_pydatetime(),
      open=row["open"],
      high=row["high"],
      low=row["low"],
      close=row["close"],
      volume=row["volume"],
    )
    for _, row in df.iterrows()
  ]


@router.post("/multi-timeframe")
async def get_multi_timeframe(request: MultiTimeframeRequest) -> dict:
  engine = MarketDataEngine()
  try:
    data = await engine.get_multi_timeframe(request)
  except MarketDataError as exc:
    raise http_exception_from_domain(exc) from exc

  result = {}
  for tf, df in data.items():
    result[tf] = [
      OHLCVBar(
        timestamp=row["timestamp"].to_pydatetime(),
        open=row["open"],
        high=row["high"],
        low=row["low"],
        close=row["close"],
        volume=row["volume"],
      ).model_dump()
      for _, row in df.tail(50).iterrows()
    ]
  return result


@router.get("/option-chain")
async def get_option_chain(symbol: str = Query("RELIANCE"), exchange: str = Query("NSE")) -> dict:
  engine = MarketDataEngine()
  try:
    df = await engine.get_candles(CandleRequest(symbol=symbol, exchange=exchange, interval="1d", limit=10))
    if df.empty:
      spot_price = 1000.0
      vol = 1.5
    else:
      spot_price = float(df["close"].iloc[-1])
      pct_changes = df["close"].pct_change().dropna()
      vol = float(pct_changes.iloc[-1]) * 100 if not pct_changes.empty else 1.5
      vol = max(0.5, abs(vol))
  except Exception:
    spot_price = 1000.0
    vol = 1.5

  from backend.app.modules.market_data.option_chain import OptionChainEngine
  oc_engine = OptionChainEngine()
  return oc_engine.calculate_option_chain(symbol, spot_price, vol)


@router.get("/pre-market")
async def get_pre_market() -> dict:
  from backend.app.modules.intelligence.market_summary import MarketSummaryEngine
  engine = MarketSummaryEngine()
  return await engine.get_briefing("pre_market")


@router.get("/briefing")
async def get_briefing(type: str = Query("pre_market")) -> dict:
  from backend.app.modules.intelligence.market_summary import MarketSummaryEngine
  engine = MarketSummaryEngine()
  return await engine.get_briefing(type)
