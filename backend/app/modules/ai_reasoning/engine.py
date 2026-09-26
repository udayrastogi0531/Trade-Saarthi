"""AI Reasoning Engine — structured explanations via Groq / DeepSeek."""

import hashlib
import json
import time
from typing import Any

import httpx
from groq import AsyncGroq

from backend.app.config import get_settings
from backend.app.core.logging import get_logger
from backend.app.core.metrics import AI_LATENCY
from backend.app.schemas.trade import AIReasoningResponse, TradeSetup
from backend.app.services.redis_client import cache_json_get, cache_json_set

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are an institutional trading analyst assistant.
You provide probabilistic, evidence-based analysis — NEVER guarantee profits.
You MUST respond with valid JSON only, matching this schema:
{
  "trade_valid": boolean,
  "confidence_score": number (0-100),
  "market_summary": string,
  "trend_structure": string,
  "volume_analysis": string,
  "risk_flags": array of strings,
  "fake_breakout_probability": number (0-1),
  "explanation": string
}
Base your analysis ONLY on the provided technical data. Do not invent prices or events.
If data is insufficient, set trade_valid to false and explain why."""


class AIReasoningEngine:
  def __init__(self) -> None:
    self._settings = get_settings()

  async def analyze_trade(
    self,
    setup: TradeSetup | None,
    technical_summary: dict,
    approved: bool,
    rejection_reasons: list[str],
  ) -> AIReasoningResponse:
    context = self._build_context(setup, technical_summary, approved, rejection_reasons)
    cache_key = "ai_reason:v1:" + hashlib.sha256(context.encode("utf-8")).hexdigest()[:40]
    cached = await cache_json_get(cache_key)
    if isinstance(cached, dict) and "trade_valid" in cached:
      return AIReasoningResponse(**cached)

    t0 = time.perf_counter()
    try:
      if self._settings.ai_provider == "groq" and self._settings.groq_api_key:
        raw = await self._call_groq(context)
      elif self._settings.ai_provider == "deepseek" and self._settings.deepseek_api_key:
        raw = await self._call_deepseek(context)
      else:
        return self._fallback_reasoning(setup, technical_summary, approved, rejection_reasons)

      parsed = self._parse_json_response(raw)
      result = AIReasoningResponse(**parsed)
      await cache_json_set(
        cache_key,
        result.model_dump(),
        ttl_seconds=self._settings.ai_reasoning_cache_ttl_seconds,
      )
      return result
    except Exception as exc:
      logger.error("ai_reasoning_failed", error=str(exc))
      fb = self._fallback_reasoning(setup, technical_summary, approved, rejection_reasons)
      return fb
    finally:
      AI_LATENCY.observe(time.perf_counter() - t0)

  async def _call_groq(self, context: str) -> str:
    client = AsyncGroq(api_key=self._settings.groq_api_key)
    response = await client.chat.completions.create(
      model=self._settings.groq_model,
      messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": context},
      ],
      temperature=0.2,
      max_tokens=800,
      response_format={"type": "json_object"},
    )
    return response.choices[0].message.content or "{}"

  async def _call_deepseek(self, context: str) -> str:
    async with httpx.AsyncClient(timeout=30.0) as client:
      response = await client.post(
        f"{self._settings.deepseek_base_url}/v1/chat/completions",
        headers={"Authorization": f"Bearer {self._settings.deepseek_api_key}"},
        json={
          "model": "deepseek-reasoner",
          "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": context},
          ],
          "temperature": 0.2,
          "max_tokens": 800,
          "response_format": {"type": "json_object"},
        },
      )
      response.raise_for_status()
      data = response.json()
      return data["choices"][0]["message"]["content"]

  @staticmethod
  def _build_context(
    setup: TradeSetup | None,
    technical_summary: dict,
    approved: bool,
    rejection_reasons: list[str],
  ) -> str:
    payload: dict[str, Any] = {
      "trade_approved_by_system": approved,
      "rejection_reasons": rejection_reasons,
      "technical_indicators": technical_summary,
    }
    if setup:
      payload["proposed_trade"] = setup.model_dump()
    return json.dumps(payload, indent=2)

  @staticmethod
  def _parse_json_response(raw: str) -> dict:
    data = json.loads(raw)
    required = [
      "trade_valid",
      "confidence_score",
      "market_summary",
      "trend_structure",
      "volume_analysis",
      "risk_flags",
      "fake_breakout_probability",
      "explanation",
    ]
    for key in required:
      if key not in data:
        data[key] = "" if key != "risk_flags" else []
    data["confidence_score"] = max(0, min(100, float(data.get("confidence_score", 0))))
    data["fake_breakout_probability"] = max(
      0, min(1, float(data.get("fake_breakout_probability", 0.5)))
    )
    return data

  @staticmethod
  def _fallback_reasoning(
    setup: TradeSetup | None,
    technical_summary: dict,
    approved: bool,
    rejection_reasons: list[str],
  ) -> AIReasoningResponse:
    trend = technical_summary.get("trend", "neutral")
    vol_spike = technical_summary.get("volume_spike", False)
    if approved and setup:
      explanation = (
        f"{setup.setup_type.title()} {setup.direction} on {setup.symbol}. "
        f"Trend is {trend} with RR {setup.risk_reward}:1. "
        f"{'Volume confirms the move.' if vol_spike else 'Volume confirmation is weak.'}"
      )
      confidence = setup.confidence
    else:
      explanation = "Trade rejected: " + "; ".join(rejection_reasons or ["No valid setup"])
      confidence = 0.0

    return AIReasoningResponse(
      trade_valid=approved,
      confidence_score=confidence,
      market_summary=f"Trend: {trend}, RSI zone per technical engine.",
      trend_structure=f"Current structure: {trend} with strength {technical_summary.get('trend_strength', 0):.2f}",
      volume_analysis="Volume spike detected" if vol_spike else "Normal volume — no spike",
      risk_flags=rejection_reasons,
      fake_breakout_probability=0.4 if not vol_spike else 0.2,
      explanation=explanation,
    )
