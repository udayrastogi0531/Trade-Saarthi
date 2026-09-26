"""Copilot REST API — chat, voice, sessions."""

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models import CopilotMessage, VoiceAlert
from backend.app.db.session import get_db
from backend.app.modules.copilot.engine import CopilotEngine
from backend.app.modules.copilot.session_manager import SessionManager
from backend.app.modules.voice.alerts import VoiceAlertService
from backend.app.modules.voice.stt import SpeechToTextService
from backend.app.modules.voice.tts import TextToSpeechService
from backend.app.schemas.copilot import (
  CopilotChatRequest,
  CopilotChatResponse,
  SessionResponse,
  VoiceSynthesizeRequest,
  VoiceTranscribeResponse,
)

router = APIRouter(prefix="/copilot", tags=["AI Copilot"])


@router.post("/chat", response_model=CopilotChatResponse)
async def chat(
  request: CopilotChatRequest,
  db: AsyncSession = Depends(get_db),
) -> CopilotChatResponse:
  """Multilingual trading copilot chat with live platform context."""
  engine = CopilotEngine()
  return await engine.chat(
    db,
    request.message,
    request.session_id,
    request.language,
    request.account_id,
    synthesize_voice=True,
  )


@router.post("/chat/stream")
async def chat_stream(
  request: CopilotChatRequest,
  db: AsyncSession = Depends(get_db),
):
  """Stream copilot response (newline-delimited JSON chunks)."""
  engine = CopilotEngine()

  async def generate():
    async for chunk in engine.stream_chat(
      db,
      request.message,
      request.session_id,
      request.language,
      request.account_id,
    ):
      yield chunk

  return StreamingResponse(generate(), media_type="application/x-ndjson")


@router.post("/voice/transcribe", response_model=VoiceTranscribeResponse)
async def transcribe_voice(
  file: UploadFile = File(...),
  language: str = Form("hinglish"),
) -> VoiceTranscribeResponse:
  """Speech-to-text for Hindi/English/Hinglish voice commands."""
  audio = await file.read()
  stt = SpeechToTextService()
  text, detected, confidence = await stt.transcribe(
    audio, file.filename or "audio.webm", language
  )
  return VoiceTranscribeResponse(text=text, language=detected, confidence=confidence)


@router.post("/voice/synthesize")
async def synthesize_voice(request: VoiceSynthesizeRequest) -> dict:
  """Text-to-speech for copilot responses."""
  tts = TextToSpeechService()
  audio_b64, mime = await tts.synthesize_base64(request.text, request.language)
  return {"audio_base64": audio_b64, "audio_mime": mime}


@router.post("/voice/chat")
async def voice_chat(
  file: UploadFile = File(...),
  session_id: str | None = Form(None),
  language: str = Form("hinglish"),
  account_id: int = Form(1),
  db: AsyncSession = Depends(get_db),
) -> CopilotChatResponse:
  """Voice in → transcribe → copilot → voice out."""
  stt = SpeechToTextService()
  audio = await file.read()
  text, detected, _ = await stt.transcribe(audio, file.filename or "audio.webm", language)

  engine = CopilotEngine()
  return await engine.chat(
    db, text, session_id, detected or language, account_id, synthesize_voice=True
  )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
  session_id: str,
  db: AsyncSession = Depends(get_db),
) -> SessionResponse:
  import uuid

  result = await db.execute(
    select(CopilotMessage)
    .where(CopilotMessage.session_id == uuid.UUID(session_id))
    .order_by(CopilotMessage.created_at)
  )
  msgs = result.scalars().all()
  from backend.app.schemas.copilot import ChatMessage

  return SessionResponse(
    session_id=session_id,
    messages=[
      ChatMessage(role=m.role, content=m.content, created_at=m.created_at) for m in msgs
    ],
    language=msgs[-1].language if msgs else "hinglish",
  )


@router.get("/voice/alerts")
async def list_voice_alerts(
  limit: int = 20,
  db: AsyncSession = Depends(get_db),
) -> dict:
  result = await db.execute(
    select(VoiceAlert).order_by(VoiceAlert.created_at.desc()).limit(limit)
  )
  alerts = result.scalars().all()
  return {
    "items": [
      {
        "id": a.id,
        "type": a.alert_type,
        "message": a.message,
        "language": a.language,
        "created_at": a.created_at.isoformat(),
      }
      for a in alerts
    ]
  }
