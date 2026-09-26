"""Multi-Timeframe Analysis Engine — weighted trend alignment."""

from dataclasses import dataclass

from backend.app.core.logging import get_logger
from backend.app.modules.technical_analysis.engine import TechnicalSnapshot

logger = get_logger(__name__)

# Higher timeframes carry more weight
TF_WEIGHTS: dict[str, float] = {
  "5m": 0.10,
  "15m": 0.15,
  "1h": 0.25,
  "4h": 0.30,
  "1d": 0.20,
}

TF_HIERARCHY = ["5m", "15m", "1h", "4h", "1d"]


@dataclass
class MTFAlignmentResult:
  aligned: bool
  alignment_score: float
  weighted_confidence: float
  dominant_trend: str
  conflicts: list[str]
  timeframe_scores: dict[str, float]
  summary: str


class MTFAnalysisEngine:
  """Lower-TF trades must align with higher-TF trend."""

  def analyze(
    self,
    snapshots: dict[str, TechnicalSnapshot],
    trade_direction: str,
  ) -> MTFAlignmentResult:
    target = "bullish" if trade_direction == "BUY" else "bearish"
    conflicts: list[str] = []
    tf_scores: dict[str, float] = {}
    weighted_sum = 0.0
    weight_total = 0.0

    for tf in TF_HIERARCHY:
      if tf not in snapshots:
        continue
      snap = snapshots[tf]
      weight = TF_WEIGHTS.get(tf, 0.1)
      weight_total += weight

      if snap.is_sideways:
        score = 0.3
        conflicts.append(f"{tf}: sideways")
      elif snap.trend_direction == target:
        score = 0.5 + snap.trend_strength * 0.5
      elif snap.trend_direction == "neutral":
        score = 0.4
        conflicts.append(f"{tf}: neutral vs {target}")
      else:
        score = 0.0
        conflicts.append(f"{tf}: {snap.trend_direction} conflicts with {target}")

      tf_scores[tf] = round(score, 3)
      weighted_sum += score * weight

    alignment_score = weighted_sum / weight_total if weight_total > 0 else 0.0

    higher_tfs = [t for t in ["4h", "1d", "1h"] if t in snapshots]
    higher_aligned = sum(
      1 for t in higher_tfs
      if snapshots[t].trend_direction == target and not snapshots[t].is_sideways
    )
    higher_required = max(1, len(higher_tfs) // 2 + (len(higher_tfs) % 2))
    aligned = alignment_score >= 0.6 and higher_aligned >= higher_required

    dominant = self._dominant_trend(snapshots)
    weighted_confidence = min(95.0, alignment_score * 100)

    summary = (
      f"MTF alignment {alignment_score:.0%} — dominant {dominant}, "
      f"{'PASS' if aligned else 'FAIL'} for {trade_direction}"
    )

    return MTFAlignmentResult(
      aligned=aligned,
      alignment_score=round(alignment_score, 4),
      weighted_confidence=round(weighted_confidence, 2),
      dominant_trend=dominant,
      conflicts=conflicts,
      timeframe_scores=tf_scores,
      summary=summary,
    )

  @staticmethod
  def _dominant_trend(snapshots: dict[str, TechnicalSnapshot]) -> str:
    votes: dict[str, float] = {"bullish": 0, "bearish": 0, "neutral": 0}
    for tf, snap in snapshots.items():
      w = TF_WEIGHTS.get(tf, 0.1)
      votes[snap.trend_direction] = votes.get(snap.trend_direction, 0) + w
    return max(votes, key=votes.get)
