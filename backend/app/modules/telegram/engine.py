"""Telegram Alert Engine — professional trade notifications."""

import httpx

from backend.app.config import get_settings
from backend.app.core.logging import get_logger
from backend.app.schemas.trade import AIReasoningResponse, TradeSetup

logger = get_logger(__name__)


class TelegramAlertEngine:
  def __init__(self) -> None:
    self._settings = get_settings()

  def format_trade_alert(
    self, setup: TradeSetup, ai: AIReasoningResponse | None = None
  ) -> str:
    reason = ai.explanation if ai else f"{setup.setup_type} setup with system validation"
    return (
      f"{'🟢' if setup.direction == 'BUY' else '🔴'} *{setup.direction}*: {setup.symbol}\n\n"
      f"Entry: `{setup.entry}`\n"
      f"SL: `{setup.stop_loss}`\n"
      f"Target: `{setup.target}`\n"
      f"RR: 1:{setup.risk_reward}\n"
      f"Confidence: {setup.confidence}%\n"
      f"Qty: {setup.position_size}\n\n"
      f"*Reason:*\n{reason}\n\n"
      f"_Probabilistic analysis — not financial advice._"
    )

  def format_rejection_alert(self, symbol: str, reasons: list[str]) -> str:
    return (
      f"⛔ *TRADE REJECTED*: {symbol}\n\n"
      f"*Reasons:*\n" + "\n".join(f"• {r}" for r in reasons) + "\n\n"
      f"_Capital preservation — no trade taken._"
    )

  async def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
    if not self._settings.telegram_enabled:
      logger.debug("telegram_disabled")
      return False

    if not self._settings.telegram_bot_token or not self._settings.telegram_chat_id:
      logger.warning("telegram_not_configured")
      return False

    url = f"https://api.telegram.org/bot{self._settings.telegram_bot_token}/sendMessage"
    payload = {
      "chat_id": self._settings.telegram_chat_id,
      "text": text,
      "parse_mode": parse_mode,
      "disable_web_page_preview": True,
    }

    try:
      async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
      logger.info("telegram_sent")
      return True
    except Exception as exc:
      logger.error("telegram_send_failed", error=str(exc))
      return False

  async def send_trade_alert(
    self, setup: TradeSetup, ai: AIReasoningResponse | None = None
  ) -> bool:
    return await self.send_message(self.format_trade_alert(setup, ai))

  async def send_rejection_alert(self, symbol: str, reasons: list[str]) -> bool:
    return await self.send_message(self.format_rejection_alert(symbol, reasons))
