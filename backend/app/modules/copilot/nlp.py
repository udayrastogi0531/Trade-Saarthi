"""Multilingual NLP — Hindi/Hinglish trading term normalization."""

import re

# Normalize Hinglish/Hindi terms to canonical intents
TERM_MAP: dict[str, str] = {
  "trend kya hai": "trend_query",
  "trend kaisa": "trend_query",
  "bullish hai": "trend_bullish",
  "bearish hai": "trend_bearish",
  "support toot gaya": "support_break",
  "support break": "support_break",
  "resistance": "resistance",
  "volume weak": "volume_weak",
  "volume kam": "volume_weak",
  "breakout fake": "fake_breakout",
  "fake breakout": "fake_breakout",
  "genuine breakout": "breakout_check",
  "open trades": "open_trades",
  "open trade": "open_trades",
  "pnl kitna": "pnl_query",
  "aaj ka pnl": "pnl_query",
  "risk exposure": "risk_query",
  "risk kitna": "risk_query",
  "best setup": "setups_query",
  "scanner": "scanner_query",
  "nifty": "symbol_nifty",
  "banknifty": "symbol_banknifty",
  "bank nifty": "symbol_banknifty",
  "reliance": "symbol_reliance",
}


def detect_language(text: str) -> str:
  """Detect en / hi / hinglish from script and patterns."""
  devanagari = len(re.findall(r"[\u0900-\u097F]", text))
  latin = len(re.findall(r"[a-zA-Z]", text))
  if devanagari > latin:
    return "hi"
  if devanagari > 0 and latin > 0:
    return "hinglish"
  hinglish_markers = ["kya", "hai", "ka", "ki", "batao", "kitna", "lag", "raha", "nahi"]
  lower = text.lower()
  if any(m in lower for m in hinglish_markers):
    return "hinglish"
  return "en"


def normalize_query(text: str) -> tuple[str, str | None]:
  """Return normalized text and detected intent hint."""
  lower = text.lower().strip()
  intent = None
  for phrase, intent_id in TERM_MAP.items():
    if phrase in lower:
      intent = intent_id
      break

  normalized = lower
  replacements = {
    "batao": "show",
    "dikhao": "show",
    "kitna": "how much",
    "kaisa": "how is",
    "kya hai": "what is",
    "lag raha": "seems",
    "weak lag": "seems weak",
  }
  for hi, en in replacements.items():
    normalized = normalized.replace(hi, en)
  return normalized, intent


def extract_symbol(text: str) -> str | None:
  """Extract likely NSE symbol from message."""
  upper_words = re.findall(r"\b[A-Z]{2,12}\b", text.upper())
  known = {
    "NIFTY", "BANKNIFTY", "RELIANCE", "TCS", "INFY", "HDFCBANK",
    "ICICIBANK", "SBIN", "ITC", "WIPRO",
  }
  for w in upper_words:
    if w in known:
      return w
  lower = text.lower()
  if "nifty" in lower and "bank" not in lower:
    return "NIFTY"
  if "banknifty" in lower or "bank nifty" in lower:
    return "BANKNIFTY"
  if "reliance" in lower:
    return "RELIANCE"
  return None
