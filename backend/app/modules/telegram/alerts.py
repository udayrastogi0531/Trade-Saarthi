"""Active Alert Manager to coordinate breakouts, breakdowns, and voice alerts."""

import os
from gtts import gTTS
from backend.app.config import get_settings
from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class ActiveAlertManager:
  """Monitors real-time alerts (breakout, volume) and generates Hinglish voice mp3 notifications."""

  def __init__(self) -> None:
    self._settings = get_settings()

  def identify_alerts(self, watchlist_data: list[dict]) -> list[dict]:
    alerts = []
    for r in watchlist_data:
      sym = r.get("symbol")
      rsi = r.get("rsi", 50.0)
      vol_ratio = r.get("vol_ratio", 1.0)
      trend = r.get("trend", "neutral")

      # 1. Breakout alert
      if rsi > 62.0 and vol_ratio > 1.4 and trend == "bullish":
        alerts.append({
          "symbol": sym,
          "type": "BREAKOUT",
          "title": f"🟢 BREAKOUT Alert: {sym}",
          "message": f"{sym} is breaking out! RSI at {rsi:.1f} with strong volume ratio {vol_ratio:.1f}x.",
          "voice_text": f"Dhyan dein! {sym} me strong bullish breakout dikh raha hai. Volume spike aur RSI high hai.",
          "risk": "Medium"
        })
      
      # 2. Breakdown alert
      elif rsi < 38.0 and vol_ratio > 1.4 and trend == "bearish":
        alerts.append({
          "symbol": sym,
          "type": "BREAKDOWN",
          "title": f"🔴 BREAKDOWN Alert: {sym}",
          "message": f"{sym} is breaking down! RSI is oversold at {rsi:.1f} with heavy volume ratio {vol_ratio:.1f}x.",
          "voice_text": f"Dhyan dein! {sym} me bearish breakdown ho raha hai. Stop loss check karein.",
          "risk": "High"
        })

      # 3. Unusual Volume alert
      elif vol_ratio > 2.0:
        alerts.append({
          "symbol": sym,
          "type": "UNUSUAL_VOLUME",
          "title": f"⚡ UNUSUAL VOLUME: {sym}",
          "message": f"{sym} is trading at {vol_ratio:.1f}x its average volume.",
          "voice_text": f"{sym} me unusual trading volume dekha gaya hai. Institutional buying interest ho sakti hai.",
          "risk": "Low"
        })

    return alerts

  def generate_voice_alert(self, text: str, filename: str = "alert.mp3") -> str | None:
    """Uses gTTS to compile a Hindi/Hinglish text payload into a local mp3 file for the UI."""
    try:
      # Ensure temp or output folder exists in the workspace
      output_dir = os.path.join("frontend", "dashboard", "static")
      os.makedirs(output_dir, exist_ok=True)
      
      file_path = os.path.join(output_dir, filename)
      
      # Compile gTTS audio
      tts = gTTS(text=text, lang="hi")
      tts.save(file_path)
      
      logger.info("voice_alert_generated", file_path=file_path)
      return file_path
    except Exception as e:
      logger.error("voice_alert_generation_failed", error=str(e))
      return None
