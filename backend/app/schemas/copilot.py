from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
  role: Literal["user", "assistant", "system"]
  content: str
  created_at: datetime | None = None


class CopilotChatRequest(BaseModel):
  message: str = Field(..., min_length=1, max_length=4000)
  session_id: str | None = None
  language: Literal["en", "hi", "hinglish"] = "hinglish"
  account_id: int = 1
  stream: bool = False


class CopilotChatResponse(BaseModel):
  session_id: str
  reply: str
  language: str
  intent: str
  context_used: list[str] = []
  disclaimer: str = (
    "Probabilistic analysis only — not financial advice. "
    "Past performance does not guarantee future results."
  )
  audio_base64: str | None = None
  audio_mime: str | None = None


class VoiceTranscribeResponse(BaseModel):
  text: str
  language: str
  confidence: float = 1.0


class VoiceSynthesizeRequest(BaseModel):
  text: str = Field(..., max_length=2000)
  language: Literal["en", "hi", "hinglish"] = "hinglish"


class SessionResponse(BaseModel):
  session_id: str
  messages: list[ChatMessage]
  language: str
