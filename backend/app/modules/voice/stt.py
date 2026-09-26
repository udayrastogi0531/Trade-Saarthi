"""Speech-to-text — Groq Whisper, optional Faster-Whisper / Deepgram."""

import io
import tempfile
from pathlib import Path

import httpx
from groq import AsyncGroq

from backend.app.config import get_settings
from backend.app.core.logging import get_logger
from backend.app.modules.copilot.nlp import detect_language

logger = get_logger(__name__)


class SpeechToTextService:
  def __init__(self) -> None:
    self._settings = get_settings()

  async def transcribe(
    self,
    audio_bytes: bytes,
    filename: str = "audio.webm",
    language_hint: str | None = None,
  ) -> tuple[str, str, float]:
    provider = self._settings.stt_provider

    if provider == "groq" and self._settings.groq_api_key:
      return await self._transcribe_groq(audio_bytes, filename, language_hint)
    if provider == "deepgram" and self._settings.deepgram_api_key:
      return await self._transcribe_deepgram(audio_bytes, language_hint)
    if provider == "faster_whisper":
      return await self._transcribe_faster_whisper(audio_bytes, language_hint)

    raise ValueError("STT not configured — set GROQ_API_KEY or DEEPGRAM_API_KEY")

  async def _transcribe_groq(
    self,
    audio_bytes: bytes,
    filename: str,
    language_hint: str | None,
  ) -> tuple[str, str, float]:
    client = AsyncGroq(api_key=self._settings.groq_api_key)
    lang_map = {"en": "en", "hi": "hi", "hinglish": "hi"}
    kwargs: dict = {"model": self._settings.groq_whisper_model}
    if language_hint:
      kwargs["language"] = lang_map.get(language_hint, "hi")

    transcription = await client.audio.transcriptions.create(
      file=(filename, audio_bytes),
      **kwargs,
    )
    text = transcription.text or ""
    detected = detect_language(text)
    logger.info("stt_groq_complete", chars=len(text))
    return text, detected, 0.95

  async def _transcribe_deepgram(
    self,
    audio_bytes: bytes,
    language_hint: str | None,
  ) -> tuple[str, str, float]:
    lang = "hi" if language_hint in ("hi", "hinglish") else "en"
    async with httpx.AsyncClient(timeout=30.0) as client:
      response = await client.post(
        "https://api.deepgram.com/v1/listen",
        params={"model": "nova-2", "language": lang, "smart_format": "true"},
        headers={"Authorization": f"Token {self._settings.deepgram_api_key}"},
        content=audio_bytes,
      )
      response.raise_for_status()
      data = response.json()
    text = data["results"]["channels"][0]["alternatives"][0]["transcript"]
    return text, detect_language(text), 0.9

  async def _transcribe_faster_whisper(
    self,
    audio_bytes: bytes,
    language_hint: str | None,
  ) -> tuple[str, str, float]:
    try:
      from faster_whisper import WhisperModel
    except ImportError as exc:
      raise ValueError("faster-whisper not installed") from exc

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
      tmp.write(audio_bytes)
      path = tmp.name

    try:
      model = WhisperModel(self._settings.faster_whisper_model, device="cpu")
      lang = "hi" if language_hint in ("hi", "hinglish") else language_hint
      segments, info = model.transcribe(path, language=lang)
      text = " ".join(s.text for s in segments).strip()
      return text, detect_language(text), info.language_probability or 0.8
    finally:
      Path(path).unlink(missing_ok=True)
