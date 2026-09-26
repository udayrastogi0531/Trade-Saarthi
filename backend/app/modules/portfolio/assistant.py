"""Portfolio Assistant Engine for calculating buy/hold/sell/reduce advice with advanced metrics."""

import pandas as pd
from backend.app.core.logging import get_logger
from backend.app.modules.market_data.engine import MarketDataEngine
from backend.app.modules.technical_analysis.engine import TechnicalAnalysisEngine
from backend.app.modules.intelligence.news import NewsIntelligenceEngine
from backend.app.schemas.market import CandleRequest

logger = get_logger(__name__)


class PortfolioAssistantEngine:
  """Calculates portfolio position health with trend, risk, sentiment, volume, and relative strength."""

  def __init__(self) -> None:
    self._market = MarketDataEngine()
    self._ta = TechnicalAnalysisEngine()
    self._news = NewsIntelligenceEngine()

  async def analyze_position(
    self,
    symbol: str,
    quantity: int,
    avg_buy_price: float,
    exchange: str = "NSE"
  ) -> dict:
    try:
      # Fetch recent daily and 15m candles
      df_daily = await self._market.get_candles(
        CandleRequest(symbol=symbol, exchange=exchange, interval="1d", limit=100)
      )
      df_15m = await self._market.get_candles(
        CandleRequest(symbol=symbol, exchange=exchange, interval="15m", limit=100)
      )
      
      # Fetch Nifty index for relative strength comparison
      try:
        df_nifty = await self._market.get_candles(
          CandleRequest(symbol="NIFTY", exchange="NSE", interval="1d", limit=100)
        )
      except Exception:
        df_nifty = pd.DataFrame()

      # Perform technical analysis
      snap_daily = self._ta.analyze(df_daily, symbol, "1d")
      snap_15m = self._ta.analyze(df_15m, symbol, "15m")

      current_price = snap_daily.indicators.get("close", avg_buy_price)
      pnl = (current_price - avg_buy_price) * quantity
      pnl_pct = (current_price - avg_buy_price) / avg_buy_price * 100 if avg_buy_price else 0.0

      # 1. Trend Score (0 to 100)
      trend_score = int(snap_daily.trend_strength * 100)
      if snap_daily.trend_direction == "bullish":
        trend_score = min(100, 50 + int(trend_score / 2))
      elif snap_daily.trend_direction == "bearish":
        trend_score = max(0, 50 - int(trend_score / 2))
      else:
        trend_score = 50

      # 2. Risk Score (0 to 100)
      risk_score = 30
      if snap_daily.atr_pct > 4.0:
        risk_score += 25
      if snap_daily.rsi > 75 or snap_daily.rsi < 25:
        risk_score += 15
      if snap_daily.trend_direction == "bearish":
        risk_score += 20
      risk_score = min(100, risk_score)

      # 3. News Sentiment Score (-1 to 1)
      news_list = await self._news.fetch_stock_news(symbol, limit=5)
      sent_scores = [n.get("sentiment_score", 0.0) for n in news_list]
      news_sentiment_score = sum(sent_scores) / len(sent_scores) if sent_scores else 0.0

      # 4. Volume Strength
      vol_ratio = snap_daily.indicators.get("volume_ratio", 1.0)
      if vol_ratio > 1.8:
        volume_strength = "Very Strong"
      elif vol_ratio > 1.2:
        volume_strength = "Strong"
      elif vol_ratio > 0.8:
        volume_strength = "Average"
      else:
        volume_strength = "Weak"

      # 5. Relative Strength vs NIFTY index
      relative_strength = 0.0
      if not df_nifty.empty and len(df_daily) >= 50:
        try:
          stock_ret = (current_price - df_daily["close"].iloc[0]) / df_daily["close"].iloc[0] * 100
          nifty_ret = (df_nifty["close"].iloc[-1] - df_nifty["close"].iloc[0]) / df_nifty["close"].iloc[0] * 100
          relative_strength = round(stock_ret - nifty_ret, 2)
        except Exception:
          pass

      # BUY / HOLD / REDUCE / EXIT recommendation logic
      if snap_daily.trend_direction == "bullish":
        if snap_daily.rsi > 72:
          status = "HOLD"
          reason_summary = "Trend is strong but RSI indicates short-term overbought zone. Hold your position to let profits run, but avoid buying new shares here."
        else:
          status = "BUY"
          reason_summary = "Strong bullish structure with healthy volume and standard momentum. Sector is showing strength. Adding/buying shares is recommended."
      elif snap_daily.trend_direction == "bearish":
        if pnl_pct < -8.0 or risk_score > 75:
          status = "EXIT"
          reason_summary = "Stop-loss margin exceeded or high risk score detected. Exiting the position is highly recommended to protect capital."
        else:
          status = "REDUCE"
          reason_summary = "Bearish trend structure forming. Trim your holdings/quantity to reduce market risk exposure."
      else:
        status = "HOLD"
        reason_summary = "Range-bound sideways structure. Volume and relative strength are average. Maintain status quo."

      # Confidence rating
      confidence = 70.0
      if snap_daily.trend_strength > 0.5:
        confidence += 15
      if snap_15m.trend_direction == snap_daily.trend_direction:
        confidence += 10
      confidence = min(95.0, confidence)

      atr = snap_daily.indicators.get("atr", current_price * 0.03) or (current_price * 0.03)
      target_min = avg_buy_price + (2.0 * atr)
      target_max = avg_buy_price + (3.5 * atr)
      stop_min = avg_buy_price - (2.0 * atr)
      stop_max = avg_buy_price - (1.5 * atr)
      trailing_stop = max(avg_buy_price - (1.5 * atr), current_price - (1.5 * atr))
      
      from datetime import datetime, timedelta
      review_date = (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d")
      expected_window = "Medium-term (1-3 months)" if snap_daily.trend_strength > 0.4 else "Short-term (2-4 weeks)"

      return {
        "symbol": symbol,
        "exchange": exchange,
        "quantity": quantity,
        "avg_buy_price": avg_buy_price,
        "current_price": round(current_price, 2),
        "unrealized_pnl": round(pnl, 2),
        "pnl_pct": round(pnl_pct, 2),
        "status": status,
        "trend_score": trend_score,
        "risk_score": risk_score,
        "news_sentiment_score": round(news_sentiment_score, 2),
        "volume_strength": volume_strength,
        "relative_strength": relative_strength,
        "confidence": confidence,
        "reason_summary": reason_summary,
        "position_management": {
          "target_zone": f"₹{target_min:,.2f} - ₹{target_max:,.2f}",
          "stoploss_zone": f"₹{stop_min:,.2f} - ₹{stop_max:,.2f}",
          "trailing_stop": round(trailing_stop, 2),
          "review_date": review_date,
          "expected_holding_window": expected_window
        },
        "technical_data": {
          "rsi": round(snap_daily.rsi, 2),
          "trend": snap_daily.trend_direction,
          "trend_strength": round(snap_daily.trend_strength, 2),
          "is_sideways": snap_daily.is_sideways,
          "atr_pct": round(snap_daily.atr_pct, 2),
          "ema_9": round(snap_daily.ema_9, 2),
          "ema_21": round(snap_daily.ema_21, 2),
          "ema_50": round(snap_daily.ema_50, 2),
        }
      }

    except Exception as exc:
      logger.error("portfolio_assistant_analysis_failed", symbol=symbol, error=str(exc))
      return {
        "symbol": symbol,
        "exchange": exchange,
        "quantity": quantity,
        "avg_buy_price": avg_buy_price,
        "current_price": avg_buy_price,
        "unrealized_pnl": 0.0,
        "pnl_pct": 0.0,
        "status": "HOLD",
        "trend_score": 50,
        "risk_score": 50,
        "news_sentiment_score": 0.0,
        "volume_strength": "Average",
        "relative_strength": 0.0,
        "confidence": 50,
        "reason_summary": f"Indicator computation failed: {str(exc)}. Safe default HOLD recommended.",
        "technical_data": {
          "rsi": 50,
          "trend": "neutral",
          "trend_strength": 0.0,
          "is_sideways": True,
          "atr_pct": 0.0,
          "ema_9": avg_buy_price,
          "ema_21": avg_buy_price,
          "ema_50": avg_buy_price,
        }
      }
