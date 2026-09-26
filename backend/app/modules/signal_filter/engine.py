"""Signal Quality Filter Engine — reduce false positives."""

from dataclasses import dataclass

from backend.app.config import get_settings
from backend.app.core.logging import get_logger
from backend.app.modules.market_regime.engine import MarketRegime, RegimeType
from backend.app.modules.mtf_analysis.engine import MTFAlignmentResult
from backend.app.modules.technical_analysis.engine import TechnicalSnapshot
from backend.app.schemas.trade import TradeSetup

logger = get_logger(__name__)


@dataclass
class FilterResult:
  passed: bool
  quality_score: float
  rejection_reasons: list[str]
  checks: dict


class SignalFilterEngine:
  """Advanced filtering before signal approval."""

  def __init__(self) -> None:
    self._settings = get_settings()

  def evaluate(
    self,
    setup: TradeSetup,
    snap: TechnicalSnapshot,
    regime: MarketRegime,
    mtf: MTFAlignmentResult,
    spread_pct: float = 0.05,
    news_risk: bool = False,
    fake_breakout_risk: float = 0.0,
  ) -> FilterResult:
    reasons: list[str] = []
    checks: dict[str, bool] = {}
    score = 50.0

    # Volume / liquidity
    vol_ratio = snap.indicators.get("volume_ratio", 1.0)
    if setup.setup_type in ("breakout", "momentum") and not snap.volume_spike:
      reasons.append("Weak volume breakout — insufficient participation")
      checks["volume"] = False
    else:
      checks["volume"] = True
      score += 10 if snap.volume_spike else 0

    min_liq = self._settings.min_liquidity_volume_ratio
    if vol_ratio < min_liq:
      reasons.append(f"Low liquidity — volume ratio {vol_ratio:.2f} below {min_liq}")
      checks["liquidity"] = False
    else:
      checks["liquidity"] = True
      score += min(10, vol_ratio * 5)

    if fake_breakout_risk > self._settings.max_fake_breakout_risk:
      reasons.append(f"Elevated fake breakout probability ({fake_breakout_risk:.0%})")
      checks["fake_breakout"] = False
      score -= 15
    else:
      checks["fake_breakout"] = True

    atr_pct = snap.atr_pct if hasattr(snap, "atr_pct") else snap.indicators.get("atr_pct", 0)
    if atr_pct > self._settings.volatility_anomaly_atr_pct:
      reasons.append(f"Volatility anomaly — ATR {atr_pct:.1f}% exceeds safe threshold")
      checks["volatility"] = False
    else:
      checks["volatility"] = True

    # MTF alignment
    if not mtf.aligned:
      reasons.append(f"Timeframe conflict: {mtf.summary}")
      checks["mtf"] = False
    else:
      checks["mtf"] = True
      score += mtf.alignment_score * 20

    # Risk/reward
    if setup.risk_reward < self._settings.min_risk_reward:
      reasons.append(f"Poor R:R {setup.risk_reward:.2f}")
      checks["risk_reward"] = False
    else:
      checks["risk_reward"] = True
      score += min(15, (setup.risk_reward - 2) * 5)

    # Regime compatibility
    if regime.regime in (RegimeType.CHOPPY, RegimeType.LOW_VOLATILITY):
      reasons.append(f"Unfavorable regime: {regime.regime.value}")
      checks["regime"] = False
    elif setup.setup_type not in regime.allowed_setups and regime.allowed_setups:
      reasons.append(f"Setup {setup.setup_type} not suited for {regime.regime.value}")
      checks["regime"] = False
    else:
      checks["regime"] = True
      score += 10

    # Spread
    if spread_pct > 0.15:
      reasons.append(f"High spread conditions ({spread_pct:.2f}%)")
      checks["spread"] = False
    else:
      checks["spread"] = True

    # News risk window
    if news_risk or regime.regime == RegimeType.NEWS_DRIVEN:
      reasons.append("News-risk period — avoid new entries")
      checks["news"] = False
    else:
      checks["news"] = True

    # Confidence threshold
    if setup.confidence < self._settings.signal_confidence_threshold:
      reasons.append(
        f"Confidence {setup.confidence}% below threshold "
        f"{self._settings.signal_confidence_threshold}%"
      )
      checks["confidence"] = False
    else:
      checks["confidence"] = True
      score += (setup.confidence - 70) * 0.3

    if self._settings.conservative_mode and setup.setup_type in ("breakout", "momentum"):
      if regime.regime in (RegimeType.CHOPPY, RegimeType.LOW_VOLATILITY):
        reasons.append("Conservative mode: breakout/momentum blocked in choppy/low-vol regime")
        checks["conservative_regime"] = False

    quality_score = round(max(0, min(100, score)), 2)
    min_quality = self._settings.min_signal_quality_score
    if self._settings.conservative_mode:
      min_quality = max(min_quality, 75.0)
    passed = (
      len(reasons) == 0
      and quality_score >= min_quality
      and mtf.alignment_score >= self._settings.min_mtf_alignment_score
    )

    if not passed and quality_score < self._settings.min_signal_quality_score:
      reasons.append(
        f"Quality score {quality_score} below minimum {self._settings.min_signal_quality_score}"
      )

    logger.info(
      "signal_filter",
      symbol=setup.symbol,
      passed=passed,
      quality_score=quality_score,
    )

    return FilterResult(
      passed=passed,
      quality_score=quality_score,
      rejection_reasons=reasons,
      checks=checks,
    )
