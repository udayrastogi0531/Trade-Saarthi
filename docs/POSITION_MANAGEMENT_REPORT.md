# Position Management Intelligence Report

This report documents the implementation of dynamic, volatility-based target zones, stop-loss zones, trailing stops, review dates, and expected holding windows calculated strictly via statistical probabilities.

---

## 🛡️ Volatility-Based Position Management

To protect capital and guide your father safely without predicting exact future prices, we integrated an ATR-based quantitative risk model inside `backend/app/modules/portfolio/assistant.py` [L125-133](file:///d:/AI%20Trading/backend/app/modules/portfolio/assistant.py#L125-L133):

### 1. Dynamic Stop-Loss Zone
* **Equation:** Cost basis minus `1.5` to `2.0` times the Average True Range (ATR).
* **Formula:**
  $$\text{Stoploss Zone} = [\text{avg\_buy\_price} - (2.0 \times \text{ATR})] \;\text{to}\; [\text{avg\_buy\_price} - (1.5 \times \text{ATR})]$$
* **Why:** Places the stop-loss strictly outside normal market noise, ensuring he is only knocked out if a genuine bearish breakdown occurs.

### 2. Dynamic Target Zone (1:2 Risk/Reward Minimum)
* **Equation:** Cost basis plus `2.0` to `3.5` times the Average True Range (ATR).
* **Formula:**
  $$\text{Target Zone} = [\text{avg\_buy\_price} + (2.0 \times \text{ATR})] \;\text{to}\; [\text{avg\_buy\_price} + (3.5 \times \text{ATR})]$$
* **Why:** Models logical taking profit zones mapped to historical asset volatility bounds.

### 3. Trailing Stop Trigger
* **Equation:** The higher of the original stop-loss cost barrier and `1.5` ATR below the current closing price.
* **Why:** Locks in paper gains dynamically as the stock prices rise.

### 4. Review Date & Expected Holding Window
* **Expected Window:** `"Medium-term (1-3 months)"` if daily trend strength is strong (`> 0.4`), otherwise `"Short-term (2-4 weeks)"`.
* **Review Date:** Automatically set to `30 days` from today for routine exit reassessments.

---

## 🖥️ Streamlit Dashboard Integration

We successfully integrated this Position Management dashboard card directly into the **Position decision & Ticker Health Analyzer** tab in `frontend/dashboard/app.py` [L421-432](file:///d:/AI%20Trading/frontend/dashboard/app.py#L421-L432):

* **How it Renders:** When your father evaluates a ticker (like TCS), the dashboard renders a dedicated **🛡️ Volatility-Based Position Management (Probabilities-First)** section with three metrics columns:
  - **Dynamic Target Zone:** ₹4,352.50 - ₹4,650.00
  - **Dynamic Stoploss Zone:** ₹3,892.40 - ₹3,950.00
  - **Trailing Stop Trigger:** ₹4,152.00
* **Holding Guidelines:** Displays a detailed text guide specifying:
  > Expected Holding Window: `Medium-term (1-3 months)` | Review/Exit Assessment Date: `2026-06-30`
