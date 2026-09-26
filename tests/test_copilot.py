from backend.app.modules.copilot.nlp import detect_language, extract_symbol, normalize_query
from backend.app.modules.copilot.engine import CopilotEngine


def test_detect_language_hinglish():
  assert detect_language("Nifty ka trend kya hai?") == "hinglish"


def test_detect_language_english():
  assert detect_language("What is the trend on RELIANCE?") == "en"


def test_extract_symbol():
  assert extract_symbol("BankNifty weak lag raha hai") == "BANKNIFTY"
  assert extract_symbol("RELIANCE breakout") == "RELIANCE"


def test_normalize_query():
  text, intent = normalize_query("open trades batao")
  assert "show" in text or "open" in text
  assert intent == "open_trades"


def test_copilot_fallback_reply():
  engine = CopilotEngine()
  reply = engine._fallback_reply(
    "mera pnl kitna hai",
    {"portfolio": {"total_pnl_recent": 1500, "win_rate_recent": 55}},
    "hinglish",
  )
  assert "1500" in reply or "PnL" in reply.lower() or "pnl" in reply.lower()
