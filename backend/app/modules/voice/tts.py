"""Text-to-speech — gTTS (Hindi/English), ElevenLabs, Azure."""

import base64
import io

import httpx

from backend.app.config import get_settings
from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class TextToSpeechService:
  def __init__(self) -> None:
    self._settings = get_settings()

  async def synthesize_base64(
    self, text: str, language: str = "hinglish"
  ) -> tuple[str | None, str | None]:
    try:
      audio_bytes, mime = await self.synthesize(text, language)
      return base64.standard_b64encode(audio_bytes).decode(), mime
    except Exception as exc:
      logger.warning("tts_failed", error=str(exc))
      return None, None

  async def synthesize(self, text: str, language: str = "hinglish") -> tuple[bytes, str]:
    provider = self._settings.tts_provider
    if provider == "elevenlabs" and self._settings.elevenlabs_api_key:
      return await self._elevenlabs(text)
    if provider == "azure" and self._settings.azure_tts_key:
      return await self._azure(text, language)
    return await self._gtts(text, language)

  async def _gtts(self, text: str, language: str) -> tuple[bytes, str]:
    from gtts import gTTS

    lang = "hi" if language in ("hi", "hinglish") else "en"
    # Truncate for TTS limits
    clean = text[:1500]
    buf = io.BytesIO()
    tts = gTTS(text=clean, lang=lang, slow=False)
    tts.write_to_fp(buf)
    buf.seek(0)
    return buf.read(), "audio/mpeg"

  async def _elevenlabs(self, text: str) -> tuple[bytes, str]:
    async with httpx.AsyncClient(timeout=30.0) as client:
      response = await client.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{self._settings.elevenlabs_voice_id}",
        headers={"xi-api-key": self._settings.elevenlabs_api_key},
        json={
          "text": text[:1500],
          "model_id": "eleven_multilingual_v2",
        },
      )
      response.raise_for_status()
      return response.content, "audio/mpeg"

  async def _azure(self, text: str, language: str) -> tuple[bytes, str]:
    lang_code = "hi-IN" if language in ("hi", "hinglish") else "en-IN"
    ssml = f"""<speak version='1.0' xml:lang='{lang_code}'>
      <voice xml:lang='{lang_code}' name='hi-IN-SwaraNeural'>{text[:1500]}</voice>
    </speak>"""
    url = f"https://{self._settings.azure_tts_region}.tts.speech.microsoft.com/cognitiveservices/v1"
    async with httpx.AsyncClient(timeout=30.0) as client:
      response = await client.post(
        url,
        headers={
          "Ocp-Apim-Subscription-Key": self._settings.azure_tts_key,
          "Content-Type": "application/ssml+xml",
          "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3",
        },
        content=ssml.encode(),
      )
      response.raise_for_status()
      return response.content, "audio/mpeg"
