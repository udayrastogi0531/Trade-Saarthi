"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";

type Health = { status: string; paper_trading: boolean; execution_enabled: boolean };

export default function DashboardPage() {
  const [health, setHealth] = useState<Health | null>(null);
  const [signals, setSignals] = useState<unknown[]>([]);
  const [scanner, setScanner] = useState<unknown>(null);
  const [analytics, setAnalytics] = useState<unknown>(null);
  const [symbol, setSymbol] = useState("RELIANCE");
  const [loading, setLoading] = useState(false);
  const [regime, setRegime] = useState<unknown>(null);
  const hasRegime = regime != null;
  const hasScanner = scanner != null;

  useEffect(() => {
    apiGet<Health>("/health").then(setHealth).catch(console.error);
    apiGet<{ items: unknown[] }>("/trades/?limit=10")
      .then((d) => setSignals(d.items))
      .catch(() => {});
    apiGet("/analytics/journal").then(setAnalytics).catch(() => {});
  }, []);

  const analyze = async () => {
    setLoading(true);
    try {
      const res = await apiPost("/signals/analyze", {
        symbol,
        exchange: "NSE",
        include_ai_reasoning: true,
      });
      setSignals([res, ...signals.slice(0, 9)]);
    } finally {
      setLoading(false);
    }
  };

  const runScanner = async () => {
    setLoading(true);
    try {
      const res = await apiPost("/scanner/run", {});
      setScanner(res);
    } finally {
      setLoading(false);
    }
  };

  const detectRegime = async () => {
    const res = await apiPost("/regime/detect", { symbol });
    setRegime(res);
  };

  return (
    <div className="space-y-8">
      <header>
        <h1 className="text-3xl font-bold tracking-tight">Trading Intelligence</h1>
        <p className="text-gray-400 mt-1">
          Probability-based execution - Multi-TF alignment - Regime-aware risk
        </p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Metric label="Status" value={health?.status?.toUpperCase() ?? "--"} />
        <Metric label="Paper" value={health?.paper_trading ? "ON" : "OFF"} />
        <Metric label="Execution" value={health?.execution_enabled ? "LIVE" : "OFF"} />
        <Metric
          label="Journal Win Rate"
          value={`${(analytics as { overall_win_rate?: number })?.overall_win_rate ?? 0}%`}
        />
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <section className="card lg:col-span-2">
          <h2 className="text-lg font-semibold mb-4">TradingView Chart</h2>
          <div className="h-96 rounded-lg overflow-hidden border border-border bg-black">
            <iframe
              title="TradingView"
              className="w-full h-full"
              src={`https://s.tradingview.com/widgetembed/?symbol=NSE%3A${symbol}&interval=15&theme=dark&style=1&locale=en`}
            />
          </div>
        </section>

        <section className="card space-y-4">
          <h2 className="text-lg font-semibold">Signal Analyzer</h2>
          <input
            className="w-full bg-surface border border-border rounded-lg px-3 py-2"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
          />
          <button
            onClick={analyze}
            disabled={loading}
            className="w-full bg-accent hover:bg-blue-600 rounded-lg py-2 font-medium transition"
          >
            Analyze Signal
          </button>
          <button
            onClick={runScanner}
            disabled={loading}
            className="w-full border border-border hover:bg-surface rounded-lg py-2 transition"
          >
            Run Watchlist Scanner
          </button>
          <button onClick={detectRegime} className="w-full text-sm text-gray-400 hover:text-white">
            Detect Market Regime
          </button>
          {hasRegime && (
            <pre className="text-xs bg-surface p-3 rounded overflow-auto max-h-40">
              {JSON.stringify(regime, null, 2)}
            </pre>
          )}
        </section>
      </div>

      {hasScanner && (
        <section className="card">
          <h2 className="text-lg font-semibold mb-2">Scanner Results</h2>
          <pre className="text-xs overflow-auto">{JSON.stringify(scanner, null, 2)}</pre>
        </section>
      )}

      <section className="card">
        <h2 className="text-lg font-semibold mb-4">Signal Feed & AI Reasoning</h2>
        <pre className="text-xs overflow-auto max-h-96">{JSON.stringify(signals, null, 2)}</pre>
      </section>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="card">
      <p className="text-xs text-gray-500 uppercase tracking-wider">{label}</p>
      <p className="text-2xl font-bold mt-1">{value}</p>
    </div>
  );
}
