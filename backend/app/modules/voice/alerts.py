"""Intelligent voice alerts — priority-based proactive desk assistant."""

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import get_settings
from backend.app.core.logging import get_logger
from backend.app.db.models import VoiceAlert
from backend.app.modules.voice.tts import TextToSpeechService

logger = get_logger(__name__)

PRIORITY_PREFIX = {"critical": "Urgent alert.", "high": "Alert.", "normal": "Notice."}


class VoiceAlertService:
  def __init__(self) -> None:
    self._settings = get_settings()
    self._tts = TextToSpeechService()

  async def create_alert(
    self,
    db: AsyncSession,
    alert_type: str,
    message: str,
    language: str = "hinglish",
    account_id: int = 1,
    priority: str = "normal",
  ) -> dict:
    prefix = PRIORITY_PREFIX.get(priority, "Alert.")
    full_message = f"{prefix} {message}" if not message.startswith("Alert") else message

    record = VoiceAlert(
      account_id=account_id,
      alert_type=alert_type,
      message=full_message,
      language=language,
    )
    db.add(record)
    await db.flush()

    audio_b64, mime = None, None
    if self._settings.voice_alerts_enabled:
      audio_b64, mime = await self._tts.synthesize_base64(full_message, language)
      record.delivered = audio_b64 is not None

    logger.info("voice_alert_created", type=alert_type, priority=priority)
    return {
      "id": record.id,
      "message": full_message,
      "audio_base64": audio_b64,
      "audio_mime": mime,
      "priority": priority,
    }

  @staticmethod
  def format_signal_alert(
    symbol: str,
    direction: str,
    confidence: float,
    lang: str,
    enhanced: bool = False,
  ) -> str:
    if lang in ("hi", "hinglish"):
      base = (
        f"{symbol} par {direction} breakout confirm hua hai, "
        f"strong higher timeframe alignment ke saath. Confidence {confidence:.0f} percent."
      )
    else:
      base = (
        f"{direction} breakout on {symbol} confirmed with higher timeframe alignment. "
        f"Confidence {confidence:.0f} percent."
      )
    if enhanced:
      base += " Risk rules active. Not financial advice."
    return base

  @staticmethod
  def format_rejection_alert(symbol: str, reason: str, lang: str) -> str:
    if lang in ("hi", "hinglish"):
      return f"{symbol} trade reject hua — {reason}. Capital protection priority."
    return f"Trade on {symbol} rejected — {reason}. Capital protection priority."

  @staticmethod
  def format_risk_alert(reason: str, lang: str) -> str:
    if lang in ("hi", "hinglish"):
      return f"Risk alert. {reason} Risk automatically reduce ho sakti hai."
    return f"Risk alert. {reason} Risk may be reduced automatically."

  @staticmethod
  def format_regime_alert(symbol: str, regime: str, lang: str) -> str:
    if lang in ("hi", "hinglish"):
      return f"{symbol} market regime ab {regime} hai. Position sizing adjust karein."
    return f"{symbol} market regime shifted to {regime}. Review position sizing."
