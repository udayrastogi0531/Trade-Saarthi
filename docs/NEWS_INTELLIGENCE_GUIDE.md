# News Intelligence Guide

The News Intelligence module parses real-time market feeds to classify catalyst triggers and track sentiment.

## Scope of Coverage

* **Stock Specific News:** Company announcements, earnings summaries, and stock triggers.
* **Macroeconomics:** RBI interest rate decisions, SEBI regulatory circulars, and institutional capital flows.
* **Global Benchmarks:** US market indices (Dow Jones, Nasdaq), commodities (Brent Crude Oil), and currency (USDINR).

## Heuristic Sentiment Classification

* **🟢 BULLISH:** Keywords density shows buying patterns, records, and expansions (Sentiment Score > +0.10).
* **🔴 BEARISH:** Keyword density maps penalties, fines, declines, and losses (Sentiment Score < -0.10).
* **⚪ NEUTRAL:** Balanced or informative headlines (Sentiment Score around 0.00).
