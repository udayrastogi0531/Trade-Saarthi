"""Strategy scorecards and edge-quality ranking — evidence from DB only."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models import SetupPerformance, Signal, Trade, WalkForwardRun
from backend.app.modules.analytics.institutional import InstitutionalAnalyticsEngine


class StrategyScorecardEngine:
  """
  Aggregates setup/regime performance into scorecards for research workflows.
  Does not invent metrics — uses persisted tables only.
  """

  async def build_scorecards(self, db: AsyncSession, account_id: int = 1) -> dict:
    perf_result = await db.execute(select(SetupPerformance))
    rows = list(perf_result.scalars().all())

    scorecards: list[dict] = []
    for p in rows:
      wr = (p.win_count / p.trade_count * 100) if p.trade_count else 0.0
      decay_score = self._decay_score(float(p.expectancy or 0), wr)
      stability = self._stability(float(p.false_breakout_rate or 0), wr)
      scorecards.append(
        {
          "setup_type": p.setup_type,
          "regime": p.market_regime,
          "trade_count": p.trade_count,
          "win_rate_pct": round(wr, 2),
          "expectancy": float(p.expectancy or 0),
          "false_breakout_rate": float(p.false_breakout_rate or 0),
          "avg_confidence": float(p.avg_confidence or 0),
          "decay_score": decay_score,
          "stability_score": stability,
          "edge_quality": self._edge_label(wr, float(p.expectancy or 0), p.trade_count),
        }
      )

    scorecards.sort(key=lambda x: (x["stability_score"], x["expectancy"]), reverse=True)
    regime_summary = self._regime_summary(scorecards)

    approved_ct = await db.scalar(
      select(func.count()).select_from(Signal).where(Signal.approved.is_(True), Signal.account_id == account_id)
    )
    rejected_ct = await db.scalar(
      select(func.count()).select_from(Signal).where(Signal.approved.is_(False), Signal.account_id == account_id)
    )
    approved = int(approved_ct or 0)
    rejected = int(rejected_ct or 0)
    total = approved + rejected
    fpr = round(rejected / total * 100, 2) if total else 0.0

    wf = await db.execute(
      select(WalkForwardRun).order_by(WalkForwardRun.created_at.desc()).limit(3)
    )
    wf_rows = list(wf.scalars().all())

    return {
      "scorecards": scorecards,
      "regime_summary": regime_summary,
      "signal_analytics": {
        "approved": approved,
        "rejected": rejected,
        "false_positive_proxy_pct": fpr,
        "note": "Rejection rate used as proxy for signal selectivity, not ground-truth FP rate",
      },
      "recent_walk_forward": [
        {
          "id": str(w.id),
          "symbol": w.symbol,
          "stability": float(w.stability_score or 0),
          "overfitting": w.overfitting_flag,
          "decay": w.decay_detected,
        }
        for w in wf_rows
      ],
    }

  async def edge_quality_report(self, db: AsyncSession, account_id: int = 1) -> dict:
    cards = await self.build_scorecards(db, account_id)
    tr = await db.execute(
      select(Trade).where(Trade.account_id == account_id, Trade.is_paper.is_(True), Trade.pnl.isnot(None))
    )
    paper = list(tr.scalars().all())
    pnls = [float(t.pnl) for t in paper if t.pnl is not None]
    inst = InstitutionalAnalyticsEngine().compute(pnls)

    ranked = cards["scorecards"]
    return {
      "summary": cards["signal_analytics"],
      "top_setups": ranked[:5],
      "bottom_setups": sorted(ranked, key=lambda x: x["expectancy"])[:3],
      "paper_portfolio_metrics": inst.to_dict(),
    }

  @staticmethod
  def _regime_summary(scorecards: list[dict]) -> list[dict]:
    buckets: dict[str, dict] = {}
    for s in scorecards:
      regime = s.get("regime") or "unknown"
      b = buckets.setdefault(
        regime,
        {"regime": regime, "setup_count": 0, "trade_count": 0, "win_rates": [], "expectancies": []},
      )
      b["setup_count"] += 1
      b["trade_count"] += int(s.get("trade_count") or 0)
      b["win_rates"].append(float(s.get("win_rate_pct") or 0))
      b["expectancies"].append(float(s.get("expectancy") or 0))

    summary: list[dict] = []
    for regime, b in buckets.items():
      wrs = b["win_rates"]
      exps = b["expectancies"]
      avg_wr = round(sum(wrs) / len(wrs), 2) if wrs else 0.0
      avg_exp = round(sum(exps) / len(exps), 4) if exps else 0.0
      summary.append(
        {
          "regime": regime,
          "setup_count": b["setup_count"],
          "trade_count": b["trade_count"],
          "avg_win_rate_pct": avg_wr,
          "avg_expectancy": avg_exp,
          "survivability": "strong" if avg_wr >= 50 and avg_exp > 0 else "weak" if avg_wr < 40 else "moderate",
        }
      )
    summary.sort(key=lambda x: x["avg_expectancy"], reverse=True)
    return summary

  @staticmethod
  def _decay_score(expectancy: float, win_rate: float) -> float:
    if expectancy < 0 and win_rate < 45:
      return 0.85
    if expectancy < 0:
      return 0.6
    if win_rate < 40:
      return 0.5
    return round(min(1.0, max(0.0, expectancy + win_rate / 200)), 3)

  @staticmethod
  def _stability(false_breakout_rate: float, win_rate: float) -> float:
    fb_penalty = min(0.4, false_breakout_rate)
    wr_bonus = min(0.3, win_rate / 200)
    return round(max(0.0, min(1.0, 0.7 - fb_penalty + wr_bonus)), 3)

  @staticmethod
  def _edge_label(win_rate: float, expectancy: float, n: int) -> str:
    if n < 5:
      return "insufficient_sample"
    if win_rate >= 55 and expectancy > 0.1:
      return "strong"
    if win_rate >= 45:
      return "moderate"
    return "weak"
