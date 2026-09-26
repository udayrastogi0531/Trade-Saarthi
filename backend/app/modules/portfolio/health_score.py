"""Stock Health Score Calculator evaluating multiple quantitative dimensions on a 0-100 scale."""

from backend.app.modules.portfolio.assistant import PortfolioAssistantEngine


class StockHealthScore:
  """Aggregates indicators to produce a unified 0-100 health rating."""

  def __init__(self) -> None:
    self._assistant = PortfolioAssistantEngine()

  async def calculate_score(self, symbol: str) -> dict:
    # Run portfolio assistant analysis to fetch indicators
    analysis = await self._assistant.analyze_position(symbol, quantity=1, avg_buy_price=100.0)
    
    tech = analysis.get("technical_data", {})
    rsi = tech.get("rsi", 50.0)
    trend = tech.get("trend", "neutral")
    trend_strength = tech.get("trend_strength", 0.0)
    atr_pct = tech.get("atr_pct", 0.0)
    news_sent = analysis.get("news_sentiment_score", 0.0)
    rel_strength = analysis.get("relative_strength", 0.0)

    # 1. Trend component (max 25)
    trend_points = 12.5  # Neutral default
    if trend == "bullish":
      trend_points = 12.5 + (trend_strength * 12.5)
    elif trend == "bearish":
      trend_points = max(0.0, 12.5 - (trend_strength * 12.5))

    # 2. Volume component (max 15)
    vol_strength = analysis.get("volume_strength", "Average")
    vol_map = {"Very Strong": 15.0, "Strong": 12.0, "Average": 8.0, "Weak": 4.0}
    vol_points = vol_map.get(vol_strength, 8.0)

    # 3. Market Structure (RSI / sideways) (max 20)
    structure_points = 15.0
    if 45.0 <= rsi <= 65.0:
      structure_points = 20.0  # Perfect accumulation/markup zone
    elif rsi > 75.0 or rsi < 25.0:
      structure_points = 8.0  # Extreme overbought/oversold risk

    # 4. News Sentiment (max 15)
    # Scale from -1.0 to 1.0 into 0 to 15
    news_points = 7.5 + (news_sent * 7.5)

    # 5. Volatility (max 10)
    # Lower volatility is safer (higher points)
    volatility_points = 10.0
    if atr_pct > 5.0:
      volatility_points = 4.0
    elif atr_pct > 3.0:
      volatility_points = 7.0

    # 6. Relative Strength vs Nifty (max 15)
    # Positive outperformance yields higher points
    rs_points = 7.5
    if rel_strength > 10.0:
      rs_points = 15.0
    elif rel_strength > 0.0:
      rs_points = 11.0
    elif rel_strength < -10.0:
      rs_points = 3.0

    total_score = trend_points + vol_points + structure_points + news_points + volatility_points + rs_points
    total_score = max(0, min(100, int(total_score)))

    # Determine status rating
    if total_score >= 80:
      status = "Excellent"
    elif total_score >= 60:
      status = "Good"
    elif total_score >= 40:
      status = "Average"
    else:
      status = "Weak"

    return {
      "symbol": symbol,
      "health_score": total_score,
      "rating": status,
      "breakdown": {
        "trend_points": round(trend_points, 1),
        "vol_points": round(vol_points, 1),
        "structure_points": round(structure_points, 1),
        "news_points": round(news_points, 1),
        "volatility_points": round(volatility_points, 1),
        "relative_strength_points": round(rs_points, 1),
      }
    }
