# Kite Portfolio Sync Guide

This document details the synchronization logic and access configuration for importing portfolio data from Zerodha Kite.

## Core Operations

The `KitePortfolioSync` engine (written in `kite_sync.py`) coordinates sync requests:

1. **Authentication:** Uses the access token generated via persistent OAuth DB records or configured `.env` properties:
   ```env
   BROKER_MODE=kite
   KITE_API_KEY=your_key
   KITE_ACCESS_TOKEN=your_token
   ```
2. **Holdings Import:** Pulls all active shares, quantities, average cost price, and computes real-time unrealized gains using live candle data.
3. **Sandbox Fallback:** If Kite is not connected or throws authorization errors, the sync engine automatically delivers a mock portfolio of blue chip equities (`RELIANCE`, `TCS`, `INFY`, `HDFCBANK`, `ITC`) with live price feeds. This guarantees 100% active operational checks.
