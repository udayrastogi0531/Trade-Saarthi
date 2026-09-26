"""AI Trading Copilot — multilingual conversational engine."""

import json
from collections.abc import AsyncGenerator

from groq import AsyncGroq
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import get_settings
from backend.app.core.logging import get_logger
from backend.app.core.metrics import AI_REQUESTS, COPILOT_MESSAGES
from backend.app.modules.copilot.context_builder import CopilotContextBuilder
from backend.app.modules.copilot.nlp import detect_language, normalize_query
from backend.app.modules.copilot.prompts import COPILOT_SYSTEM_PROMPT, INTENT_HINTS
from backend.app.modules.copilot.session_manager import SessionManager
from backend.app.modules.voice.tts import TextToSpeechService
from backend.app.schemas.copilot import CopilotChatResponse

logger = get_logger(__name__)


class CopilotEngine:
  def __init__(self) -> None:
    self._settings = get_settings()
    self._sessions = SessionManager()
    self._context = CopilotContextBuilder()
    self._tts = TextToSpeechService()

  async def chat(
    self,
    db: AsyncSession,
    message: str,
    session_id: str | None = None,
    language: str | None = None,
    account_id: int = 1,
    synthesize_voice: bool = False,
  ) -> CopilotChatResponse:
    detected = language or detect_language(message)
    _, intent_hint = normalize_query(message)

    session_id, history = await self._sessions.get_or_create(
      db, session_id, detected, account_id
    )

    live_ctx, sources = await self._context.build(db, account_id, message)
    intent = intent_hint or self._classify_intent(message)

    await self._sessions.append(db, session_id, "user", message, detected, intent)
    COPILOT_MESSAGES.labels(role="user").inc()

    reply = await self._generate_reply(message, detected, history, live_ctx, intent)

    await self._sessions.append(db, session_id, "assistant", reply, detected, intent)
    COPILOT_MESSAGES.labels(role="assistant").inc()

    audio_b64, audio_mime = None, None
    if synthesize_voice and self._settings.copilot_enabled:
      audio_b64, audio_mime = await self._tts.synthesize_base64(reply, detected)

    return CopilotChatResponse(
      session_id=session_id,
      reply=reply,
      language=detected,
      intent=intent,
      context_used=sources,
      audio_base64=audio_b64,
      audio_mime=audio_mime,
    )

  async def stream_chat(
    self,
    db: AsyncSession,
    message: str,
    session_id: str | None,
    language: str | None,
    account_id: int = 1,
  ) -> AsyncGenerator[str, None]:
    """Stream response tokens via SSE/WebSocket chunks."""
    detected = language or detect_language(message)
    session_id, history = await self._sessions.get_or_create(
      db, session_id, detected, account_id
    )
    live_ctx, sources = await self._context.build(db, account_id, message)
    await self._sessions.append(db, session_id, "user", message, detected)

    yield json.dumps({"type": "meta", "session_id": session_id, "sources": sources}) + "\n"

    full_reply = []
    if self._settings.groq_api_key:
      async for chunk in self._stream_groq(message, detected, history, live_ctx):
        full_reply.append(chunk)
        yield json.dumps({"type": "token", "content": chunk}) + "\n"
    else:
      fallback = self._fallback_reply(message, live_ctx, detected)
      full_reply.append(fallback)
      yield json.dumps({"type": "token", "content": fallback}) + "\n"

    complete = "".join(full_reply)
    await self._sessions.append(db, session_id, "assistant", complete, detected)
    yield json.dumps({"type": "done", "content": complete}) + "\n"

  async def _generate_reply(
    self,
    message: str,
    language: str,
    history: list[dict],
    live_ctx: dict,
    intent: str,
  ) -> str:
    if self._settings.groq_api_key:
      try:
        AI_REQUESTS.inc()
        return await self._call_groq(message, language, history, live_ctx)
      except Exception as exc:
        logger.error("copilot_groq_failed", error=str(exc))
    return self._fallback_reply(message, live_ctx, language)

  async def _call_groq(
    self,
    message: str,
    language: str,
    history: list[dict],
    live_ctx: dict,
  ) -> str:
    lang_instruction = {
      "en": "Respond in English.",
      "hi": "Respond in Hindi (Devanagari script).",
      "hinglish": "Respond in natural Hinglish (Hindi + English mix, Roman script).",
    }.get(language, "Respond in Hinglish.")

    messages = [
      {"role": "system", "content": COPILOT_SYSTEM_PROMPT + f"\n{lang_instruction}"},
      {
        "role": "system",
        "content": f"LIVE CONTEXT (use only this data):\n{json.dumps(live_ctx, indent=2, default=str)}",
      },
    ]
    for h in history[-8:]:
      messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})

    client = AsyncGroq(api_key=self._settings.groq_api_key)
    response = await client.chat.completions.create(
      model=self._settings.groq_model,
      messages=messages,
      temperature=0.4,
      max_tokens=900,
    )
    return response.choices[0].message.content or ""

  async def _stream_groq(
    self,
    message: str,
    language: str,
    history: list[dict],
    live_ctx: dict,
  ) -> AsyncGenerator[str, None]:
    lang_instruction = {
      "en": "Respond in English.",
      "hi": "Respond in Hindi.",
      "hinglish": "Respond in Hinglish.",
    }.get(language, "Respond in Hinglish.")

    messages = [
      {"role": "system", "content": COPILOT_SYSTEM_PROMPT + f"\n{lang_instruction}"},
      {
        "role": "system",
        "content": f"LIVE CONTEXT:\n{json.dumps(live_ctx, default=str)}",
      },
    ]
    for h in history[-6:]:
      messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})

    client = AsyncGroq(api_key=self._settings.groq_api_key)
    stream = await client.chat.completions.create(
      model=self._settings.groq_model,
      messages=messages,
      temperature=0.4,
      max_tokens=900,
      stream=True,
    )
    async for chunk in stream:
      delta = chunk.choices[0].delta.content
      if delta:
        yield delta

  @staticmethod
  def _classify_intent(message: str) -> str:
    lower = message.lower()
    for intent, keywords in INTENT_HINTS.items():
      if any(k in lower for k in keywords):
        return intent
    return "general"

  @staticmethod
  def _fallback_reply(message: str, ctx: dict, language: str) -> str:
    """Rule-based fallback when LLM unavailable."""
    lower = message.lower()
    disclaimer = "\n\n_Note: Probabilistic analysis — not financial advice._"

    if "pnl" in lower or "kitna" in lower:
      p = ctx.get("portfolio", {})
      if language == "hi":
        return f"Recent closed trades PnL: ₹{p.get('total_pnl_recent', 0)}. Win rate: {p.get('win_rate_recent', 0)}%.{disclaimer}"
      return (
        f"Aapka recent closed PnL roughly ₹{p.get('total_pnl_recent', 0)} hai. "
        f"Win rate {p.get('win_rate_recent', 0)}% dikha raha hai.{disclaimer}"
      )

    if "open" in lower or "trade" in lower:
      trades = ctx.get("open_trades", [])
      if not trades:
        return f"Koi open trade nahi hai abhi (paper mode: {ctx.get('paper_trading')}).{disclaimer}"
      summary = ", ".join(f"{t['symbol']} {t['direction']}" for t in trades[:5])
      return f"Open trades: {summary}.{disclaimer}"

    if "trend" in lower or "nifty" in lower:
      sa = ctx.get("symbol_analysis") or ctx.get("latest_regime")
      if sa:
        return (
          f"Focus analysis — trend/regime data available in context. "
          f"Details: {json.dumps(sa, default=str)[:300]}.{disclaimer}"
        )
      return f"Live trend data fetch karo — symbol specify karein (e.g. NIFTY, RELIANCE).{disclaimer}"

    return (
      "Main aapka AI Trading Copilot hoon. Trend, PnL, open trades, risk, ya setups "
      "ke baare mein pooch sakte ho. Groq API key configure karein for full AI responses."
      + disclaimer
    )
