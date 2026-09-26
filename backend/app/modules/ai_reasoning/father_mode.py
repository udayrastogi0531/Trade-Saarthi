"""Father Mode Engine to explain market indicators in simple Hindi/Hinglish."""

import json
from groq import AsyncGroq
from backend.app.config import get_settings
from backend.app.core.logging import get_logger

logger = get_logger(__name__)

FATHER_SYSTEM_PROMPT = """You are a helpful, wise financial advisor helping a loving father understand the stock market.
Explain the technical and news data in simple Hindi/Hinglish (mix of clean Hindi and English words in Latin script).
AVOID heavy quantitative jargon or formulas. Keep it simple, clear, and reassuring but objective.
Do NOT guarantee profits. Do NOT recommend blind gambling. Emphasize risk control.

You MUST respond strictly with a valid JSON containing these four exact keys:
{
  "kya_hua": "Hindi/Hinglish explanation of what happened in the stock recently",
  "kyun_farq_padta_hai": "Hindi/Hinglish explanation of why it matters to the investor",
  "kya_nuksaan_ho_sakta_hai": "Hindi/Hinglish explanation of what risks or losses could happen",
  "aage_nazar_kahan_rakhein": "Hindi/Hinglish explanation of what to watch next"
}
Ensure all keys are populated with high-quality descriptions. Use regular English characters for Hinglish writing."""


class FatherModeEngine:
  """Explains trade signals in a father-friendly plain Hindi/Hinglish layout."""

  def __init__(self) -> None:
    self._settings = get_settings()

  async def generate_explanation(self, symbol: str, technicals: dict, option_chain: dict, news: list[dict]) -> dict:
    context = {
      "symbol": symbol,
      "technicals": {
        "rsi": technicals.get("rsi", 50.0),
        "trend": technicals.get("trend", "neutral"),
        "trend_strength": technicals.get("trend_strength", 0.0),
        "atr_pct": technicals.get("atr_pct", 0.0),
        "close": technicals.get("close", 0.0),
      },
      "option_chain": {
        "pcr": option_chain.get("pcr", 1.0),
        "support": option_chain.get("support", 0.0),
        "resistance": option_chain.get("resistance", 0.0),
        "max_pain": option_chain.get("max_pain", 0.0),
      },
      "news": [n.get("title", "") for n in news[:3]]
    }

    try:
      if self._settings.groq_api_key:
        client = AsyncGroq(api_key=self._settings.groq_api_key)
        response = await client.chat.completions.create(
          model=self._settings.groq_model,
          messages=[
            {"role": "system", "content": FATHER_SYSTEM_PROMPT},
            {"role": "user", "content": f"Analyze this context and respond in strict JSON:\n{json.dumps(context, indent=2)}"},
          ],
          temperature=0.3,
          max_tokens=600,
          response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "{}"
        return json.loads(content)
    except Exception as e:
      logger.error("father_mode_llm_failed", symbol=symbol, error=str(e))

    # Fallback to local rule-based Hinglish generator if LLM is unavailable or fails
    return self._get_fallback_explanation(symbol, technicals, option_chain)

  def _get_fallback_explanation(self, symbol: str, technicals: dict, option_chain: dict) -> dict:
    trend = technicals.get("trend", "neutral")
    pcr = option_chain.get("pcr", 1.0)
    support = option_chain.get("support", 0.0)
    resistance = option_chain.get("resistance", 0.0)
    close = technicals.get("close", 0.0)

    if trend == "bullish":
      kya_hua = f"{symbol} ke shares me achhi kharidari chal rahi hai. Trend bullish hai aur buyers active hain."
      kyun_farq_padta_hai = f"Agar aapne yeh shares hold kiye hain toh aapka portfolio green me ho sakta hai. Achhi momentum hai."
      kya_nuksaan = f"Upar ke levels par stock me thodi profit booking aa sakti hai. RSI thoda high ho sakta hai."
    elif trend == "bearish":
      kya_hua = f"{symbol} me thodi bikwali dikh rahi hai. Price EMA levels ke niche trade kar raha hai."
      kyun_farq_padta_hai = f"Aapka capital protect rakhna sabse badi priority hai. Risk thoda jyada dikh raha hai."
      kya_nuksaan = f"Price aur niche ₹{support:.0f} tak slip ho sakta hai agar support breaks."
    else:
      kya_hua = f"{symbol} abhi ek range me fasa hua hai (sideways zone). Price flat move ho raha hai."
      kyun_farq_padta_hai = f"Abhi hold karke wait karne ka samay hai. Nayi buy ya sell ki jaldbazi na karein."
      kya_nuksaan = f"Market sideways hai, isliye options me premiums decay ho sakte hain."

    return {
      "kya_hua": kya_hua,
      "kyun_farq_padta_hai": kyun_farq_padta_hai,
      "kya_nuksaan_ho_sakta_hai": kya_nuksaan,
      "aage_nazar_kahan_rakhein": f"Upar ₹{resistance:.0f} ke resistance aur niche ₹{support:.0f} ke support levels par nazar rakhein. Inke break hone par naya breakout aa sakta hai."
    }
