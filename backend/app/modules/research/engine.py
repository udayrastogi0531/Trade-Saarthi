"""AI Strategy Research — evidence-driven analysis, no hallucinated edge."""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import get_settings
from backend.app.core.logging import get_logger
from backend.app.db.models import SetupPerformance, SignalOutcome, StrategyResearchReport, TradeJournal
from backend.app.modules.learning.engine import LearningEngine

logger = get_logger(__name__)


class StrategyResearchEngine:
  """
  Statistical strategy research assistant.

  Outputs are grounded in database evidence. AI summaries (if enabled) must
  cite the evidence payload — never invent performance numbers.
  """

  def __init__(self) -> None:
    self._settings = get_settings()
    self._learning = LearningEngine()

  async def generate_report(
    self,
    db: AsyncSession,
    report_type: str = "full",
    setup_type: str | None = None,
    regime: str | None = None,
    use_ai_summary: bool = False,
  ) -> dict:
    evidence = await self._gather_evidence(db, setup_type, regime)
    findings = self._analyze_evidence(evidence)
    uncertainty = self._uncertainty_notes(evidence)

    ai_summary = None
    if use_ai_summary and self._settings.groq_api_key:
      ai_summary = await self._ai_summarize(findings, evidence, uncertainty)

    narratives = self._narratives(findings, evidence)

    report_row = StrategyResearchReport(
      report_type=report_type,
      scope={"setup_type": setup_type, "regime": regime},
      findings=findings,
      evidence=evidence,
      uncertainty_notes=uncertainty,
      ai_summary=ai_summary,
    )
    db.add(report_row)
    await db.flush()

    return {
      "report_id": str(report_row.id),
      "report_type": report_type,
      "findings": findings,
      "evidence_summary": {k: v for k, v in evidence.items() if k != "raw_samples"},
      "narratives": narratives,
      "uncertainty_notes": uncertainty,
      "ai_summary": ai_summary,
      "disclaimer": "Statistical analysis only — not financial advice. Past performance does not guarantee future results.",
    }

  async def _gather_evidence(
    self, db: AsyncSession, setup_type: str | None, regime: str | None
  ) -> dict:
    perf_q = select(SetupPerformance)
    if setup_type:
      perf_q = perf_q.where(SetupPerformance.setup_type == setup_type)
    if regime:
      perf_q = perf_q.where(SetupPerformance.market_regime == regime)
    perf_rows = (await db.execute(perf_q)).scalars().all()

    outcomes_q = select(SignalOutcome).order_by(SignalOutcome.recorded_at.desc()).limit(500)
    outcomes = (await db.execute(outcomes_q)).scalars().all()

    journal_q = select(TradeJournal).limit(200)
    journals = (await db.execute(journal_q)).scalars().all()

    return {
      "setup_performance": [
        {
          "setup_type": p.setup_type,
          "regime": p.market_regime,
          "trade_count": p.trade_count,
          "win_rate": float(p.win_count / p.trade_count * 100) if p.trade_count else 0,
          "expectancy": float(p.expectancy or 0),
          "false_breakout_rate": float(p.false_breakout_rate or 0),
        }
        for p in perf_rows
      ],
      "recent_outcomes": len(outcomes),
      "approved_rate": round(
        sum(1 for o in outcomes if o.approved) / max(len(outcomes), 1) * 100, 2
      ),
      "journal_samples": len(journals),
      "raw_samples": {"outcomes": len(outcomes), "journals": len(journals)},
    }

  def _analyze_evidence(self, evidence: dict) -> dict:
    setups = evidence.get("setup_performance", [])
    strongest = sorted(setups, key=lambda x: x.get("expectancy", 0), reverse=True)[:3]
    weakest = sorted(setups, key=lambda x: x.get("expectancy", 0))[:3]
    decaying = [s for s in setups if s.get("win_rate", 0) < 40 and s.get("trade_count", 0) >= 5]
    overfit_risk = [s for s in setups if s.get("false_breakout_rate", 0) > 0.35]

    return {
      "strongest_setups": strongest,
      "weakest_setups": weakest,
      "decaying_setups": decaying,
      "overfitting_risk_setups": overfit_risk,
      "total_regimes_tracked": len({s.get("regime") for s in setups}),
    }

  def _narratives(self, findings: dict, evidence: dict) -> list[str]:
    lines = []
    for s in findings.get("weakest_setups", [])[:2]:
      if s.get("trade_count", 0) >= 3:
        lines.append(
          f"Setup '{s['setup_type']}' in '{s.get('regime', 'unknown')}' regime shows weak expectancy "
          f"({s.get('expectancy', 0):.2f}) over {s['trade_count']} samples."
        )
    for s in findings.get("decaying_setups", [])[:2]:
      lines.append(
        f"'{s['setup_type']}' win rate ({s.get('win_rate', 0):.1f}%) suggests possible strategy decay — review parameters."
      )
    for s in findings.get("overfitting_risk_setups", [])[:1]:
      lines.append(
        f"Elevated false breakout rate ({s.get('false_breakout_rate', 0):.0%}) on '{s['setup_type']}' — overfitting risk."
      )
    if not lines:
      lines.append("Insufficient historical samples for high-confidence regime-specific conclusions.")
    return lines

  @staticmethod
  def _uncertainty_notes(evidence: dict) -> str:
    n = sum(s.get("trade_count", 0) for s in evidence.get("setup_performance", []))
    if n < 30:
      return f"Low sample size ({n} trades) — conclusions are preliminary. More data required."
    if n < 100:
      return f"Moderate sample ({n} trades) — use findings as directional, not definitive."
    return "Adequate sample for directional analysis; still subject to regime change."

  async def _ai_summarize(self, findings: dict, evidence: dict, uncertainty: str) -> str | None:
    try:
      from groq import Groq

      client = Groq(api_key=self._settings.groq_api_key)
      prompt = (
        "Summarize this TRADING RESEARCH evidence in 3-4 sentences. "
        "Use ONLY the numbers provided. State uncertainty. Never guarantee profits.\n"
        f"Findings: {findings}\nEvidence counts: {evidence.get('recent_outcomes')} outcomes\n"
        f"Uncertainty: {uncertainty}"
      )
      resp = client.chat.completions.create(
        model=self._settings.groq_model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
      )
      return resp.choices[0].message.content
    except Exception as exc:
      logger.warning("research_ai_summary_failed", error=str(exc))
      return None
