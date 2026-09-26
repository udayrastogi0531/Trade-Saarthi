"""Conversational session memory — Redis + PostgreSQL."""

import json
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import get_settings
from backend.app.core.logging import get_logger
from backend.app.db.models import CopilotMessage, CopilotSession
from backend.app.services.redis_client import cache_get, cache_set

logger = get_logger(__name__)


class SessionManager:
  def __init__(self) -> None:
    self._settings = get_settings()
    self._ttl = self._settings.copilot_session_ttl_hours * 3600

  def _cache_key(self, session_id: str) -> str:
    return f"copilot:session:{session_id}"

  async def get_or_create(
    self,
    db: AsyncSession,
    session_id: str | None,
    language: str,
    account_id: int = 1,
  ) -> tuple[str, list[dict]]:
    if session_id:
      cached = await cache_get(self._cache_key(session_id))
      if cached:
        data = json.loads(cached)
        return session_id, data.get("messages", [])

      try:
        sid = uuid.UUID(session_id)
      except ValueError:
        sid = None

      if sid:
        result = await db.execute(
          select(CopilotMessage)
          .where(CopilotMessage.session_id == sid)
          .order_by(CopilotMessage.created_at)
          .limit(self._settings.copilot_max_history)
        )
        msgs = result.scalars().all()
        if msgs:
          history = [{"role": m.role, "content": m.content} for m in msgs]
          await self._cache_session(session_id, history, language)
          return session_id, history

    new_id = str(uuid.uuid4())
    session = CopilotSession(
      id=uuid.UUID(new_id),
      account_id=account_id,
      language=language,
    )
    db.add(session)
    await db.flush()
    await self._cache_session(new_id, [], language)
    return new_id, []

  async def append(
    self,
    db: AsyncSession,
    session_id: str,
    role: str,
    content: str,
    language: str,
    intent: str | None = None,
  ) -> None:
    history_key = self._cache_key(session_id)
    cached = await cache_get(history_key)
    messages = json.loads(cached)["messages"] if cached else []
    messages.append({"role": role, "content": content})
    messages = messages[-self._settings.copilot_max_history :]
    await self._cache_session(session_id, messages, language)

    msg = CopilotMessage(
      session_id=uuid.UUID(session_id),
      role=role,
      content=content,
      language=language,
      intent=intent,
    )
    db.add(msg)

  async def _cache_session(
    self, session_id: str, messages: list[dict], language: str
  ) -> None:
    await cache_set(
      self._cache_key(session_id),
      json.dumps({"messages": messages, "language": language, "updated": datetime.utcnow().isoformat()}),
      ttl_seconds=self._ttl,
    )
