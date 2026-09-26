"""Option Chain Intelligence Engine for computing OI, PCR, IV, Max Pain zones, and Options Greeks."""

import math
import numpy as np
from backend.app.core.logging import get_logger

logger = get_logger(__name__)


class OptionChainEngine:
  """Models options chain statistics (OI, PCR, IV, Max Pain, and Greeks) for free from spot price."""

  @staticmethod
  def _norm_cdf(x: float) -> float:
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

  @staticmethod
  def _norm_pdf(x: float) -> float:
    return math.exp(-0.5 * x**2) / math.sqrt(2.0 * math.pi)

  def _calculate_greeks(self, s: float, k: float, t: float, r: float, iv: float) -> dict:
    # Prevent division by zero
    t = max(0.0001, t)
    iv_dec = max(0.01, iv / 100.0)

    try:
      d1 = (math.log(s / k) + (r + 0.5 * iv_dec**2) * t) / (iv_dec * math.sqrt(t))
      d2 = d1 - iv_dec * math.sqrt(t)

      nd1 = self._norm_cdf(d1)
      nd2 = self._norm_cdf(d2)
      np_d1 = self._norm_pdf(d1)

      call_delta = nd1
      call_theta = (-(s * np_d1 * iv_dec) / (2 * math.sqrt(t)) - r * k * math.exp(-r * t) * nd2) / 365.0

      put_delta = nd1 - 1.0
      put_theta = (-(s * np_d1 * iv_dec) / (2 * math.sqrt(t)) + r * k * math.exp(-r * t) * self._norm_cdf(-d2)) / 365.0

      gamma = np_d1 / (s * iv_dec * math.sqrt(t))
      vega = (s * math.sqrt(t) * np_d1) / 100.0

      return {
        "call_delta": round(float(call_delta), 3),
        "call_theta": round(float(call_theta), 3),
        "put_delta": round(float(put_delta), 3),
        "put_theta": round(float(put_theta), 3),
        "gamma": round(float(gamma), 4),
        "vega": round(float(vega), 3),
      }
    except Exception:
      return {
        "call_delta": 0.5,
        "call_theta": 0.0,
        "put_delta": -0.5,
        "put_theta": 0.0,
        "gamma": 0.0,
        "vega": 0.0,
      }

  def get_strike_interval(self, price: float) -> float:
    if price > 20000:
      return 100.0
    elif price > 5000:
      return 50.0
    elif price > 1000:
      return 20.0
    elif price > 500:
      return 10.0
    elif price > 100:
      return 5.0
    return 1.0

  def calculate_option_chain(self, symbol: str, spot_price: float, daily_volatility_pct: float = 1.5) -> dict:
    try:
      interval = self.get_strike_interval(spot_price)
      atm_strike = round(spot_price / interval) * interval
      
      # Generate 5 strikes above and 5 strikes below ATM
      strikes = [atm_strike + (i * interval) for i in range(-5, 6)]
      
      call_oi = []
      put_oi = []
      call_iv = []
      put_iv = []
      call_change_oi = []
      put_change_oi = []

      total_call_oi = 0
      total_put_oi = 0

      # Simulating Open Interest based on distance from ATM (normally distributed around ATM)
      rng = np.random.default_rng(hash(symbol) % 2**32)
      
      for s in strikes:
        # Base Implied Volatility (IV)
        base_iv = daily_volatility_pct * 15.8
        c_iv = base_iv * (1.0 + (s - spot_price) / spot_price * 0.5)
        p_iv = base_iv * (1.0 - (s - spot_price) / spot_price * 0.5)
        
        call_iv.append(round(c_iv, 2))
        put_iv.append(round(p_iv, 2))

        # OI simulation: higher near ATM, decaying as OTM/ITM increases
        c_oi_factor = np.exp(-((s - (atm_strike + interval)) / (3 * interval))**2)
        p_oi_factor = np.exp(-((s - (atm_strike - interval)) / (3 * interval))**2)
        
        c_oi = int(c_oi_factor * rng.integers(100_000, 1_000_000))
        p_oi = int(p_oi_factor * rng.integers(100_000, 1_000_000))
        
        call_oi.append(c_oi)
        put_oi.append(p_oi)
        
        total_call_oi += c_oi
        total_put_oi += p_oi

        # Change in OI
        call_change_oi.append(int(c_oi * rng.uniform(-0.1, 0.3)))
        put_change_oi.append(int(p_oi * rng.uniform(-0.1, 0.3)))

      pcr = total_put_oi / total_call_oi if total_call_oi > 0 else 1.0

      # Max Pain: Strike where option sellers experience minimum loss
      min_pain = float("inf")
      max_pain_strike = atm_strike
      
      for candidate in strikes:
        pain = 0.0
        for i, s in enumerate(strikes):
          if candidate > s:
            pain += (candidate - s) * call_oi[i]
          if candidate < s:
            pain += (s - candidate) * put_oi[i]
        if pain < min_pain:
          min_pain = pain
          max_pain_strike = candidate

      call_oi_arr = np.array(call_oi)
      put_oi_arr = np.array(put_oi)
      
      resistance_strike = strikes[np.argmax(call_oi_arr)]
      support_strike = strikes[np.argmax(put_oi_arr)]

      # Explanations in simple Hinglish/Hindi
      if pcr > 1.2:
        sentiment_hindi = "Market BOHOT BULLISH hai kyunki log puts jyada buy/write kar rahe hain (Heavy Support base)."
      elif pcr < 0.7:
        sentiment_hindi = "Market BEARISH lag raha hai, calls me heavy writing ho rahi hai (Resistance heavy)."
      else:
        sentiment_hindi = "Market RANGE-BOUND aur NEUTRAL lag raha hai, call aur put buyers balance me hain."

      hindi_explanation = (
        f"Dosto, {symbol} ka spot price abhi ₹{spot_price:.2f} chal raha hai. "
        f"PCR (Put-Call Ratio) {pcr:.2f} hai jiska matlab hai {sentiment_hindi} "
        f"Niche ke level par ₹{support_strike:.0f} ek majboot support zone (Puts heavy OI) dikh raha hai "
        f"aur upar ₹{resistance_strike:.0f} ek strong resistance ka kaam karega. "
        f"Option sellers ka Max Pain strike ₹{max_pain_strike:.0f} par hai, jaha market expiry par settle ho sakta hai."
      )

      # Build chain table with Black-Scholes Greeks
      chain_data = []
      for i, s in enumerate(strikes):
        greeks = self._calculate_greeks(spot_price, s, 30 / 365, 0.065, call_iv[i])
        chain_data.append({
          "strike": s,
          "is_atm": s == atm_strike,
          "call_oi": call_oi[i],
          "call_change_oi": call_change_oi[i],
          "call_iv": call_iv[i],
          "call_delta": greeks["call_delta"],
          "call_theta": greeks["call_theta"],
          "gamma": greeks["gamma"],
          "vega": greeks["vega"],
          "put_oi": put_oi[i],
          "put_change_oi": put_change_oi[i],
          "put_iv": put_iv[i],
          "put_delta": greeks["put_delta"],
          "put_theta": greeks["put_theta"],
        })

      return {
        "symbol": symbol,
        "spot_price": spot_price,
        "atm_strike": atm_strike,
        "pcr": round(pcr, 2),
        "max_pain": max_pain_strike,
        "support": support_strike,
        "resistance": resistance_strike,
        "hindi_explanation": hindi_explanation,
        "chain": chain_data,
        "is_synthetic": True,
        "disclaimer": "DISCLAIMER: This options chain and its Greeks are synthetically modeled from stock spot prices for capital safety simulations. Do NOT execute real options contracts on these simulated parameters.",
      }
    except Exception as e:
      logger.error("option_chain_calculation_failed", symbol=symbol, error=str(e))
      return {}
