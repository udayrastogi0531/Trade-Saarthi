"""Streamlit trading dashboard — professional dark UI starter."""

import os
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
API_PREFIX = "/api/v1"

st.set_page_config(
  page_title="AI Trading Assistant",
  page_icon="📊",
  layout="wide",
  initial_sidebar_state="expanded",
)

st.markdown(
  """
  <style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .metric-card {
      background: #1a1f2e;
      border: 1px solid #2d3748;
      border-radius: 8px;
      padding: 16px;
    }
    h1, h2, h3 { color: #f0f0f0 !important; }
  </style>
  """,
  unsafe_allow_html=True,
)


def api_get(path: str) -> dict | list | None:
  try:
    r = requests.get(f"{API_BASE}{API_PREFIX}{path}", timeout=10)
    r.raise_for_status()
    return r.json()
  except Exception as e:
    st.error(f"API error: {e}")
    return None


def api_post(path: str, payload: dict) -> dict | None:
  try:
    r = requests.post(f"{API_BASE}{API_PREFIX}{path}", json=payload, timeout=30)
    r.raise_for_status()
    return r.json()
  except Exception as e:
    st.error(f"API error: {e}")
    return None


st.title("AI Trading Assistant")
st.caption("Probability-based execution · Risk-first · Not financial advice")

health = api_get("/health")
if health:
  cols = st.columns(4)
  cols[0].metric("Status", health.get("status", "—").upper())
  cols[1].metric("Environment", health.get("environment", "—"))
  cols[2].metric("Paper Trading", "ON" if health.get("paper_trading") else "OFF")
  cols[3].metric("Live Execution", "ON" if health.get("execution_enabled") else "OFF")

tab_signal, tab_trades, tab_backtest, tab_chart, tab_portfolio, tab_news, tab_options, tab_summary, tab_opportunities = st.tabs(
  [
    "Signal Analyzer",
    "Trades & PnL",
    "Backtest",
    "Chart",
    "💼 Portfolio Assistant",
    "📰 News Intelligence",
    "⛓️ Option Chain",
    "🌅 Pre-Market Summary",
    "🎯 Watchlist Opportunities"
  ]
)

with tab_signal:
  st.subheader("Analyze Setup")
  col1, col2 = st.columns([2, 1])
  with col1:
    symbol = st.text_input("Symbol", value="RELIANCE").upper()
  with col2:
    exchange = st.selectbox("Exchange", ["NSE", "BSE"])

  if st.button("Analyze Signal", type="primary"):
    with st.spinner("Running full pipeline..."):
      result = api_post(
        "/signals/analyze",
        {"symbol": symbol, "exchange": exchange, "include_ai_reasoning": True},
      )
    if result:
      if result.get("approved"):
        setup = result["setup"]
        st.success(f"APPROVED — {setup['direction']} {setup['symbol']}")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Entry", setup["entry"])
        m2.metric("Stop Loss", setup["stop_loss"])
        m3.metric("Target", setup["target"])
        m4.metric("Confidence", f"{setup['confidence']}%")
        st.json(setup)
      else:
        st.warning("TRADE REJECTED — Capital preserved")
        for reason in result.get("rejection_reasons", []):
          st.write(f"• {reason}")

      if result.get("ai_reasoning"):
        st.subheader("AI Reasoning")
        ai = result["ai_reasoning"]
        st.info(ai.get("explanation", ""))
        st.write(f"**Trend:** {ai.get('trend_structure', '')}")
        st.write(f"**Fake breakout risk:** {ai.get('fake_breakout_probability', 0):.0%}")

with tab_trades:
  st.subheader("Active & Historical Trades")
  trades_data = api_get("/trades/?limit=20")
  analytics = api_get("/trades/analytics")

  if analytics:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Win Rate", f"{analytics.get('win_rate', 0)}%")
    c2.metric("Total PnL", analytics.get("total_pnl", 0))
    c3.metric("Sharpe", analytics.get("sharpe_ratio", 0))
    c4.metric("Closed Trades", analytics.get("trade_count", 0))

  if trades_data and trades_data.get("items"):
    st.dataframe(pd.DataFrame(trades_data["items"]), use_container_width=True)
  else:
    st.info("No trades yet. Run signal analysis with paper trading enabled.")

with tab_backtest:
  st.subheader("Strategy Backtest")
  bt_symbol = st.text_input("Backtest Symbol", value="RELIANCE").upper()
  capital = st.number_input("Initial Capital", value=100_000, step=10_000)
  if st.button("Run Backtest"):
    with st.spinner("Backtesting..."):
      bt = api_post(
        "/backtest/run",
        {"symbol": bt_symbol, "initial_capital": capital},
      )
    if bt:
      st.json(bt.get("metrics", {}))
      if bt.get("sample_trades"):
        st.dataframe(pd.DataFrame(bt["sample_trades"]))

with tab_chart:
  st.subheader("Price Chart")
  chart_symbol = st.text_input("Chart Symbol", value="RELIANCE").upper()
  if st.button("Load Chart"):
    candles = api_post(
      "/market/candles",
      {"symbol": chart_symbol, "exchange": "NSE", "interval": "15m", "limit": 100},
    )
    if candles:
      df = pd.DataFrame(candles)
      df["timestamp"] = pd.to_datetime(df["timestamp"])
      fig = go.Figure(
        data=[
          go.Candlestick(
            x=df["timestamp"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name=chart_symbol,
          )
        ]
      )
"""Streamlit trading dashboard — professional dark UI starter."""

import os
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
API_PREFIX = "/api/v1"

st.set_page_config(
  page_title="AI Trading Assistant",
  page_icon="📊",
  layout="wide",
  initial_sidebar_state="expanded",
)

st.markdown(
  """
  <style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .metric-card {
      background: #1a1f2e;
      border: 1px solid #2d3748;
      border-radius: 8px;
      padding: 16px;
    }
    h1, h2, h3 { color: #f0f0f0 !important; }
  </style>
  """,
  unsafe_allow_html=True,
)


def api_get(path: str) -> dict | list | None:
  try:
    r = requests.get(f"{API_BASE}{API_PREFIX}{path}", timeout=10)
    r.raise_for_status()
    return r.json()
  except Exception as e:
    st.error(f"API error: {e}")
    return None


def api_post(path: str, payload: dict) -> dict | None:
  try:
    r = requests.post(f"{API_BASE}{API_PREFIX}{path}", json=payload, timeout=30)
    r.raise_for_status()
    return r.json()
  except Exception as e:
    st.error(f"API error: {e}")
    return None


st.title("AI Trading Assistant")
st.caption("Probability-based execution · Risk-first · Not financial advice")

health = api_get("/health")
if health:
  cols = st.columns(4)
  cols[0].metric("Status", health.get("status", "—").upper())
  cols[1].metric("Environment", health.get("environment", "—"))
  cols[2].metric("Paper Trading", "ON" if health.get("paper_trading") else "OFF")
  cols[3].metric("Live Execution", "ON" if health.get("execution_enabled") else "OFF")

tab_signal, tab_trades, tab_backtest, tab_chart, tab_portfolio, tab_news, tab_options, tab_summary, tab_opportunities = st.tabs(
  [
    "Signal Analyzer",
    "Trades & PnL",
    "Backtest",
    "Chart",
    "💼 Portfolio Assistant",
    "📰 News Intelligence",
    "⛓️ Option Chain",
    "🌅 Pre-Market Summary",
    "🎯 Watchlist Opportunities"
  ]
)

with tab_signal:
  st.subheader("Analyze Setup")
  col1, col2 = st.columns([2, 1])
  with col1:
    symbol = st.text_input("Symbol", value="RELIANCE").upper()
  with col2:
    exchange = st.selectbox("Exchange", ["NSE", "BSE"])

  if st.button("Analyze Signal", type="primary"):
    with st.spinner("Running full pipeline..."):
      result = api_post(
        "/signals/analyze",
        {"symbol": symbol, "exchange": exchange, "include_ai_reasoning": True},
      )
    if result:
      if result.get("approved"):
        setup = result["setup"]
        st.success(f"APPROVED — {setup['direction']} {setup['symbol']}")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Entry", setup["entry"])
        m2.metric("Stop Loss", setup["stop_loss"])
        m3.metric("Target", setup["target"])
        m4.metric("Confidence", f"{setup['confidence']}%")
        st.json(setup)
      else:
        st.warning("TRADE REJECTED — Capital preserved")
        for reason in result.get("rejection_reasons", []):
          st.write(f"• {reason}")

      if result.get("ai_reasoning"):
        st.subheader("AI Reasoning")
        ai = result["ai_reasoning"]
        st.info(ai.get("explanation", ""))
        st.write(f"**Trend:** {ai.get('trend_structure', '')}")
        st.write(f"**Fake breakout risk:** {ai.get('fake_breakout_probability', 0):.0%}")

with tab_trades:
  st.subheader("Active & Historical Trades")
  trades_data = api_get("/trades/?limit=20")
  analytics = api_get("/trades/analytics")

  if analytics:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Win Rate", f"{analytics.get('win_rate', 0)}%")
    c2.metric("Total PnL", analytics.get("total_pnl", 0))
    c3.metric("Sharpe", analytics.get("sharpe_ratio", 0))
    c4.metric("Closed Trades", analytics.get("trade_count", 0))

  if trades_data and trades_data.get("items"):
    st.dataframe(pd.DataFrame(trades_data["items"]), use_container_width=True)
  else:
    st.info("No trades yet. Run signal analysis with paper trading enabled.")

with tab_backtest:
  st.subheader("Strategy Backtest")
  bt_symbol = st.text_input("Backtest Symbol", value="RELIANCE").upper()
  capital = st.number_input("Initial Capital", value=100_000, step=10_000)
  if st.button("Run Backtest"):
    with st.spinner("Backtesting..."):
      bt = api_post(
        "/backtest/run",
        {"symbol": bt_symbol, "initial_capital": capital},
      )
    if bt:
      st.json(bt.get("metrics", {}))
      if bt.get("sample_trades"):
        st.dataframe(pd.DataFrame(bt["sample_trades"]))

with tab_chart:
  st.subheader("Price Chart")
  chart_symbol = st.text_input("Chart Symbol", value="RELIANCE").upper()
  if st.button("Load Chart"):
    candles = api_post(
      "/market/candles",
      {"symbol": chart_symbol, "exchange": "NSE", "interval": "15m", "limit": 100},
    )
    if candles:
      df = pd.DataFrame(candles)
      df["timestamp"] = pd.to_datetime(df["timestamp"])
      fig = go.Figure(
        data=[
          go.Candlestick(
            x=df["timestamp"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name=chart_symbol,
          )
        ]
      )
      fig.update_layout(
        template="plotly_dark",
        height=500,
        margin=dict(l=0, r=0, t=30, b=0),
        xaxis_rangeslider_visible=False,
      )
      st.plotly_chart(fig, use_container_width=True)

with tab_portfolio:
  st.subheader("💼 Zerodha Kite Portfolio Manager")
  
  if st.button("Refresh Kite Portfolio Sync", type="primary", key="sync_btn"):
    with st.spinner("Connecting to Kite API & updating prices..."):
      portfolio = api_get("/portfolio")
    if portfolio:
      summary = portfolio.get("summary", {})
      invested = summary.get("total_invested_value", 0.0)
      current = summary.get("total_current_value", 0.0)
      pnl = summary.get("total_pnl", 0.0)
      pnl_pct = summary.get("total_pnl_pct", 0.0)

      # 1. Total Portfolio Value Cards
      c1, c2, c3 = st.columns(3)
      c1.metric("Invested Value", f"₹{invested:,.2f}")
      c2.metric("Current Portfolio Value", f"₹{current:,.2f}")
      c3.metric("Total PnL", f"₹{pnl:,.2f}", f"{pnl_pct:+.2f}%")

      # 1.5 Account Intelligence cash/margins cards (Priority 2)
      margins = api_get("/portfolio/margins")
      if margins:
        m_source = margins.get("source", "mock").upper()
        m_available = margins.get("available_cash", 0.0)
        m_utilized = margins.get("margin_utilized", 0.0)
        
        st.subheader(f"💰 Account Intelligence ({m_source} segment)")
        col_cash, col_util, col_pow = st.columns(3)
        col_cash.metric("Available Cash Balance", f"₹{m_available:,.2f}")
        col_util.metric("Utilized Margins", f"₹{m_utilized:,.2f}")
        col_pow.metric("Available Buying Power", f"₹{m_available:,.2f}")

      # 2. Holdings Table
      st.subheader("Holdings & Performance")
      holdings_df = pd.DataFrame(portfolio.get("holdings", []))
      st.dataframe(holdings_df, use_container_width=True)

      # 3. Top Winners / Losers
      if not holdings_df.empty:
        st.subheader("🏆 Portfolio Performance Leaders")
        col_win, col_los = st.columns(2)
        
        winners = holdings_df.sort_values(by="pnl", ascending=False).head(2)
        losers = holdings_df.sort_values(by="pnl").head(2)
        
        with col_win:
          st.success("🟢 Top Winners")
          st.dataframe(winners[["symbol", "quantity", "pnl", "pnl_pct"]], use_container_width=True)
        with col_los:
          st.warning("🔴 Top Losers")
          st.dataframe(losers[["symbol", "quantity", "pnl", "pnl_pct"]], use_container_width=True)

  st.divider()
  st.subheader("🔍 Position decision & Ticker Health Analyzer")
  col_sym, col_qty, col_price = st.columns(3)
  with col_sym:
    p_symbol = st.text_input("Stock Ticker", value="RELIANCE", key="p_sym").upper()
  with col_qty:
    p_qty = st.number_input("Shares Quantity", value=10, step=1)
  with col_price:
    p_price = st.number_input("Avg Cost Price", value=2800.0, step=10.0)

  if st.button("Evaluate Position", key="eval_btn"):
    with st.spinner("Running indicators & scoring health..."):
      position = api_post(
        "/portfolio/analyze-position",
        {"symbol": p_symbol, "quantity": p_qty, "avg_buy_price": p_price, "exchange": "NSE"}
      )
      health_data = api_get(f"/portfolio/health?symbol={p_symbol}")
      
    if position and health_data:
      m_status, m_current, m_pnl, m_health = st.columns(4)
      status_colors = {"HOLD": "🟡 HOLD", "BUY": "🟢 BUY", "REDUCE": "🟠 REDUCE", "EXIT": "🔴 EXIT", "SELL": "🔴 SELL"}
      m_status.metric("Action Directive", status_colors.get(position.get("status", "HOLD"), "HOLD"))
      m_current.metric("Market Price", f"₹{position.get('current_price', 0.0):.2f}")
      
      pnl = position.get("unrealized_pnl", 0.0)
      pnl_pct = position.get("pnl_pct", 0.0)
      m_pnl.metric("Position PnL", f"₹{pnl:,.2f}", f"{pnl_pct:+.2f}%")
      m_health.metric("Stock Health Score", f"{health_data.get('health_score', 50)}/100 ({health_data.get('rating')})")

      # Dynamic Position Management Cards (Priority 4)
      if position.get("position_management"):
        pm = position["position_management"]
        st.subheader("🛡️ Volatility-Based Position Management (Probabilities-First)")
        p_col1, p_col2, p_col3 = st.columns(3)
        p_col1.metric("Dynamic Target Zone", pm.get("target_zone"))
        p_col2.metric("Dynamic Stoploss Zone", pm.get("stoploss_zone"))
        p_col3.metric("Trailing Stop Trigger", f"₹{pm.get('trailing_stop', 0.0):,.2f}")
        st.markdown(f"**Expected Holding Window:** `{pm.get('expected_holding_window')}` | **Review/Exit Assessment Date:** `{pm.get('review_date')}`")

      # Advanced Quantitative Indicators Grid
      st.subheader("📊 Quantitative Indicators Matrix")
      i1, i2, i3, i4 = st.columns(4)
      i1.metric("Trend Score (0-100)", f"{position.get('trend_score', 50)}/100")
      i2.metric("Risk Score (0-100)", f"{position.get('risk_score', 30)}/100")
      i3.metric("News Sentiment Score", f"{position.get('news_sentiment_score', 0.0):+.2f}")
      i4.metric("Relative Strength (vs Nifty)", f"{position.get('relative_strength', 0.0):+.2f}%")

      st.markdown(f"**Volume Strength:** `{position.get('volume_strength', 'Average')}`")
      st.info(position.get("reason_summary", ""))

      # Father Mode Hinglish guidelines
      st.subheader("👴 Father Mode Guide (Simple Explanation)")
      fm = position.get("father_mode", {})
      
      st.markdown(f"**1. Kya Hua? (What happened?)**\n{fm.get('kya_hua', 'Aapka stock range me fasa hai.')}")
      st.markdown(f"**2. Kyun Farq Padta Hai? (Why it matters?)**\n{fm.get('kyun_farq_padta_hai', 'Capital protection priority hai.')}")
      st.markdown(f"**3. Kya Risk/Nuksaan Ho Sakta Hai? (What is the risk?)**\n{fm.get('kya_nuksaan_ho_sakta_hai', 'Support area tootne par niche jaa sakta hai.')}")
      st.markdown(f"**4. Mujhe Kya Karna Chahiye? (Recommended action?)**\n*Mata-Pita ke liye salaa:* `{position.get('status')}` karein.")
      st.markdown(f"**5. Aage Nazar Kahan Rakhein? (What to watch next?)**\n{fm.get('aage_nazar_kahan_rakhein', 'Stop loss and target levels.')}")

with tab_news:
  st.subheader("📰 Macro News & Catalyst Sentiment")
  n_symbol = st.text_input("News Ticker Symbol", value="RELIANCE", key="n_sym").upper()
  if st.button("Collect News & Triggers", type="primary"):
    with st.spinner("Parsing RBI/SEBI/Earnings feeds..."):
      news = api_get(f"/news?symbol={n_symbol}")
    if news:
      for article in news:
        badge = "⚪ NEUTRAL"
        if article.get("sentiment") == "Bullish":
          badge = "🟢 BULLISH"
        elif article.get("sentiment") == "Bearish":
          badge = "🔴 BEARISH"

        st.markdown(f"### {article.get('title')}")
        st.markdown(f"**Source:** {article.get('source')} | **Date:** {article.get('pub_date')} | **Sentiment Badge:** {badge}")
        st.markdown(f"[Source link]({article.get('link')})")
        st.divider()

with tab_options:
  st.subheader("⛓️ Options Greeks & Expiry Risk")
  o_symbol = st.text_input("Options Underlying Ticker", value="RELIANCE", key="o_sym").upper()
  if st.button("Calculate Option Chain Greeks", type="primary"):
    with st.spinner("Computing Black-Scholes variables..."):
      chain = api_get(f"/market/option-chain?symbol={o_symbol}")
    if chain:
      if chain.get("is_synthetic"):
        st.warning(chain.get("disclaimer"))
      st.info(chain.get("hindi_explanation", ""))
      
      c1, c2, c3, c4 = st.columns(4)
      c1.metric("PCR", chain.get("pcr", 1.0))
      c2.metric("Max Pain Strike", f"₹{chain.get('max_pain', 0.0):.0f}")
      c3.metric("Support zone", f"₹{chain.get('support', 0.0):.0f}")
      c4.metric("Resistance zone", f"₹{chain.get('resistance', 0.0):.0f}")

      st.subheader("Options Strikes Matrix (Delta, Gamma, Theta, Vega)")
      st.dataframe(pd.DataFrame(chain.get("chain", [])), use_container_width=True)

with tab_summary:
  st.subheader("🌅 Briefings & Institutional Flow Data")
  brief_type = st.radio("Briefing Type", ["Pre-Market", "Intraday", "Closing"])
  
  brief_map = {"Pre-Market": "pre_market", "Intraday": "intraday", "Closing": "closing"}
  if st.button("Generate Briefing", type="primary", key="brief_btn"):
    with st.spinner("Compiling briefings..."):
      summary = api_get(f"/market/briefing?type={brief_map[brief_type]}")
    if summary:
      st.subheader(summary.get("title", "Market Briefing"))
      st.info(summary.get("briefing_hinglish", ""))
      
      col_n, col_d, col_ns, col_c = st.columns(4)
      n = summary.get("nifty", {})
      d = summary.get("dow", {})
      ns = summary.get("nasdaq", {})
      c = summary.get("crude", {})

      col_n.metric("Nifty 50 close", f"₹{n.get('close', 0.0):.2f}", f"{n.get('change', 0.0):+.2f}%")
      col_d.metric("Dow Jones", f"₹{d.get('close', 0.0):.2f}", f"{d.get('change', 0.0):+.2f}%")
      col_ns.metric("Nasdaq", f"₹{ns.get('close', 0.0):.2f}", f"{ns.get('change', 0.0):+.2f}%")
      col_c.metric("Crude Oil Brent", f"₹{c.get('close', 0.0):.2f}", f"{c.get('change', 0.0):+.2f}%")

      st.subheader("Institutional Net Flows")
      fii = summary.get("fii_dii", {})
      col_f, col_di, col_s = st.columns(3)
      col_f.metric("FII Net Flows (Crores)", f"₹{fii.get('fii_net_crore', 0.0):,.0f} Cr")
      col_di.metric("DII Net Flows (Crores)", f"₹{fii.get('dii_net_crore', 0.0):,.0f} Cr")
      col_s.metric("Flow Sentiment", fii.get("sentiment", "Neutral"))

with tab_opportunities:
  st.subheader("🎯 Buy/Sell Candidates & Spoken Voice Alerts")
  
  col_sc, col_al = st.columns([3, 2])
  
  with col_sc:
    st.subheader("🚀 Opportunity Discovery")
    if st.button("Find Top Buy Candidates", type="primary"):
      with st.spinner("Scanning watchlist..."):
        buys = api_get("/scanner/buy-candidates")
      if buys:
        st.success("🟢 Ranked Buy Candidates")
        st.dataframe(pd.DataFrame(buys)[["symbol", "health_score", "rating", "status", "confidence"]], use_container_width=True)

    if st.button("Identify Top Exit/Sell Candidates", type="primary"):
      with st.spinner("Scanning portfolio..."):
        sells = api_get("/scanner/sell-candidates")
      if sells:
        st.warning("🔴 Ranked Exit / Sell Candidates")
        st.dataframe(pd.DataFrame(sells)[["symbol", "health_score", "status", "pnl_pct", "reason"]], use_container_width=True)
        
  with col_al:
    st.subheader("📢 Active Spoken Alarms")
    if st.button("Refresh Audio Alerts"):
      with st.spinner("Scraping signals..."):
        alerts_data = api_get("/alerts")
      if alerts_data:
        st.markdown(f"**Broadcast Transcript:** *{alerts_data.get('voice_text')}*")
        
        if alerts_data.get("audio_available"):
          audio_file = os.path.join("frontend", "dashboard", "static", "alert.mp3")
          if os.path.exists(audio_file):
            st.audio(audio_file, format="audio/mp3")
            
        st.subheader("🚨 Breakout/Breakdown logs")
        st.dataframe(pd.DataFrame(alerts_data.get("alerts", [])), use_container_width=True)

st.sidebar.markdown("### Risk Policy")
st.sidebar.markdown(
  """
  - Max daily loss: 2%
  - Max drawdown: 10%
  - Min R:R: 1:2
  - Max trades/day: 5
  """
)
st.sidebar.markdown(f"**API:** `{API_BASE}`")
st.sidebar.markdown(f"Updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
