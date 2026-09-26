from fastapi.testclient import TestClient
import pytest

from backend.app.main import app

client = TestClient(app)


def test_root():
  response = client.get("/")
  assert response.status_code == 200
  assert "disclaimer" in response.json()


def test_health():
  response = client.get("/api/v1/health")
  assert response.status_code == 200
  data = response.json()
  assert data["status"] == "ok"


def test_market_candles():
  response = client.post(
    "/api/v1/market/candles",
    json={"symbol": "RELIANCE", "exchange": "NSE", "interval": "15m", "limit": 100},
  )
  assert response.status_code == 200
  assert len(response.json()) >= 50


def test_research_scorecards():
  try:
    response = client.get("/api/v1/research/scorecards")
  except Exception as exc:
    err = str(exc).lower()
    if "refused" in err or "1225" in err or "connect" in err:
      pytest.skip("Database / network unavailable for API test")
    raise
  assert response.status_code == 200
  body = response.json()
  assert "scorecards" in body
  assert "signal_analytics" in body
  assert "regime_summary" in body


def test_observability_data_quality():
  try:
    response = client.get("/api/v1/observability/data-quality")
  except Exception as exc:
    err = str(exc).lower()
    if "refused" in err or "1225" in err or "connect" in err:
      pytest.skip("Database / network unavailable for API test")
    raise
  assert response.status_code == 200
  body = response.json()
  assert "events" in body
  assert "feed_healthy" in body


def test_paper_summary():
  try:
    response = client.get("/api/v1/paper/summary?days=7")
  except Exception as exc:
    err = str(exc).lower()
    if "refused" in err or "1225" in err or "connect" in err:
      pytest.skip("Database / network unavailable for API test")
    raise
  assert response.status_code == 200
  assert "paper_trades_opened" in response.json()
