"""AI Chart Analysis — vision-based structure detection."""

import base64
import json
from io import BytesIO
from pathlib import Path
from typing import Any

from groq import AsyncGroq
from PIL import Image

from backend.app.config import get_settings
from backend.app.core.logging import get_logger

logger = get_logger(__name__)

CHART_PROMPT = """Analyze this trading chart image (multi-modal). Respond with JSON only:
{
  "support_levels": [numbers],
  "resistance_levels": [numbers],
  "trend_lines": [{"direction": "up|down", "strength": "weak|moderate|strong"}],
  "patterns": ["candlestick/structure patterns"],
  "liquidity_zones": ["description"],
  "order_blocks": ["if visible"],
  "fair_value_gaps": ["if visible"],
  "breakout_structure": "none|forming|confirmed|failed|retest",
  "weak_momentum": boolean,
  "trend_exhaustion": boolean,
  "setup_quality_score": number 0-100,
  "continuation_probability": number 0-1,
  "chart_summary": "brief summary",
  "trade_quality": "poor|fair|good|excellent",
  "risk_assessment": "low|medium|high",
  "risk_flags": ["list"],
  "explanation": "detailed reasoning for a trader"
}
Do not invent exact prices if unreadable. State uncertainty clearly. Never guarantee profits."""


class ChartAnalysisEngine:
  def __init__(self) -> None:
    self._settings = get_settings()
    self._upload_dir = Path("data/chart_uploads")
    self._upload_dir.mkdir(parents=True, exist_ok=True)

  async def analyze_image(
    self,
    image_bytes: bytes,
    symbol: str | None = None,
    filename: str = "chart.png",
  ) -> dict[str, Any]:
    path = self._upload_dir / filename
    path.write_bytes(image_bytes)

    if self._settings.groq_api_key and self._settings.chart_analysis_enabled:
      try:
        result = await self._analyze_with_groq(image_bytes, symbol)
        result["source"] = "groq_vision"
        return result
      except Exception as exc:
        logger.warning("chart_vision_failed", error=str(exc))

    return self._fallback_analysis(symbol)

  async def _analyze_with_groq(self, image_bytes: bytes, symbol: str | None) -> dict:
    img = Image.open(BytesIO(image_bytes))
    if img.mode not in ("RGB", "L"):
      img = img.convert("RGB")
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    b64 = base64.standard_b64encode(buf.getvalue()).decode()

    client = AsyncGroq(api_key=self._settings.groq_api_key)
    response = await client.chat.completions.create(
      model=self._settings.groq_model,
      messages=[
        {
          "role": "user",
          "content": [
            {"type": "text", "text": f"{CHART_PROMPT}\nSymbol: {symbol or 'unknown'}"},
            {
              "type": "image_url",
              "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
            },
          ],
        }
      ],
      temperature=0.2,
      max_tokens=1000,
    )
    raw = response.choices[0].message.content or "{}"
    return json.loads(raw)

  @staticmethod
  def _fallback_analysis(symbol: str | None) -> dict:
    return {
      "source": "heuristic",
      "support_levels": [],
      "resistance_levels": [],
      "trend_lines": [],
      "patterns": [],
      "liquidity_zones": ["Unable to parse — configure GROQ_API_KEY for vision"],
      "breakout_structure": "none",
      "chart_summary": f"Chart uploaded for {symbol or 'unknown'}. Enable Groq vision for full analysis.",
      "trade_quality": "fair",
      "risk_assessment": "medium",
      "risk_flags": ["Vision API not configured"],
      "explanation": "Upload received. Connect Groq API for AI chart structure detection.",
    }
