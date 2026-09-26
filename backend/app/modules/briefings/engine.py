"""Daily AI market briefings — pre-market, intraday, post-market."""

import json
from datetime import datetime

from groq import AsyncGroq
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import get_settings
from backend.app.core.logging import get_logger
from backend.app.db.models import MarketBriefing
from backend.app.modules.intelligence.panel import IntelligencePanel
from backend.app.modules.telegram.engine import TelegramAlertEngine
from backend.app.modules.voice.alerts import VoiceAlertService

logger = get_logger(__name__)

BRIEFING_PROMPT = """Generate a professional trading desk briefing. Use ONLY provided data.
Sections: Market Sentiment, Sector/Watchlist Strength, Volatility, Top Setups, Risk Flags.
Be concise. Never guarantee profits. Mark uncertainty clearly."""


class BriefingEngine:
  def __init__(self) -> None:
    self._settings = get_settings()
    self._panel = IntelligencePanel()

  async def generate(
    self,
    db: AsyncSession,
    briefing_type: str = "intraday",
    account_id: int = 1,
    deliver_voice: bool = True,
    deliver_telegram: bool = True,
  ) -> dict:
    intel = await self._panel.build(db, account_id)
    content = await self._generate_text(briefing_type, intel)
    summary = {
      "type": briefing_type,
      "regime": intel.get("market_regime"),
      "top_setups": intel.get("top_setups", [])[:3],
      "risk_flags": intel.get("risk_flags", []),
      "generated_at": datetime.utcnow().isoformat(),
    }

    record = MarketBriefing(
      briefing_type=briefing_type,
      content=content,
      summary=summary,
      language=self._settings.briefing_language,
    )
    db.add(record)
    await db.flush()

    if deliver_voice and self._settings.voice_alerts_enabled:
      vas = VoiceAlertService()
      preview = content[:400]
      await vas.create_alert(db, "briefing", preview, self._settings.briefing_language, account_id)
      record.voice_delivered = True

    if deliver_telegram and self._settings.telegram_enabled:
      tg = TelegramAlertEngine()
      await tg.send_message(f"📊 *{briefing_type.upper()} Briefing*\n\n{content[:3500]}")

    logger.info("briefing_generated", type=briefing_type, id=str(record.id))
    return {"id": str(record.id), "content": content, "summary": summary}

  async def _generate_text(self, briefing_type: str, intel: dict) -> str:
    if not self._settings.groq_api_key:
      return self._fallback_briefing(briefing_type, intel)

    client = AsyncGroq(api_key=self._settings.groq_api_key)
    lang = self._settings.briefing_language
    response = await client.chat.completions.create(
      model=self._settings.groq_model,
      messages=[
        {"role": "system", "content": BRIEFING_PROMPT},
        {
          "role": "user",
          "content": f"Type: {briefing_type}. Language: {lang}. Data:\n{json.dumps(intel, default=str)[:6000]}",
        },
      ],
      temperature=0.35,
      max_tokens=1200,
    )
    return response.choices[0].message.content or self._fallback_briefing(briefing_type, intel)

  @staticmethod
  def _fallback_briefing(briefing_type: str, intel: dict) -> str:
    return (
      f"## {briefing_type.title()} Briefing\n\n"
      f"**Regime:** {intel.get('market_regime', 'unknown')}\n"
      f"**Approved signals today:** {intel.get('approved_signals_count', 0)}\n"
      f"**Risk flags:** {', '.join(intel.get('risk_flags', []) or ['None'])}\n\n"
      f"Top setups: {intel.get('top_setups', [])}\n\n"
      "_Configure GROQ_API_KEY for full AI briefings. Not financial advice._"
    )
