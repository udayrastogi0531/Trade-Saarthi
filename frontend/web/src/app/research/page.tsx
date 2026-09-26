"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";
import { DisciplineBanner } from "@/components/DisciplineBanner";
import { HealthStrip } from "@/components/HealthStrip";
import { OperationalAlerts } from "@/components/OperationalAlerts";
import { RegimeComparisonTable, ScorecardTable } from "@/components/ScorecardTable";
import type { ObservabilityHealth, ScorecardsResponse } from "@/lib/types";

export default function ResearchPage() {
  const [health, setHealth] = useState<ObservabilityHealth | null>(null);
  const [scorecards, setScorecards] = useState<ScorecardsResponse | null>(null);
  const [edge, setEdge] = useState<Record<string, unknown> | null>(null);
  const [paper, setPaper] = useState<Record<string, unknown> | null>(null);
  const [wf, setWf] = useState<Record<string, unknown> | null>(null);
  const [mc, setMc] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);
  const [bootLoading, setBootLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    setError(null);
    const [h, sc, eq, p] = await Promise.all([
      apiGet<ObservabilityHealth>("/observability/health"),
      apiGet<ScorecardsResponse>("/research/scorecards"),
      apiGet<Record<string, unknown>>("/research/edge-quality"),
      apiGet<Record<string, unknown>>("/paper/summary?days=30"),
    ]);
    setHealth(h);
    setScorecards(sc);
    setEdge(eq);
    setPaper(p);
  };

  useEffect(() => {
    refresh()
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load research data"))
      .finally(() => setBootLoading(false));
  }, []);

  const runWalkForward = async () => {
    setLoading(true);
    setError(null);
    try {
      setWf(await apiPost("/validation/walk-forward", { symbol: "RELIANCE", persist: false }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Walk-forward failed");
    } finally {
      setLoading(false);
    }
  };

  const runMonteCarlo = async () => {
    setLoading(true);
    setError(null);
    try {
      setMc(await apiPost("/validation/monte-carlo", { persist: false }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Monte Carlo failed");
    } finally {
      setLoading(false);
    }
  };

  const analytics = scorecards?.signal_analytics;
  const rejectionPct = analytics?.false_positive_proxy_pct ?? 0;

  return (
    <div className="space-y-6 pb-24">
      <header>
        <Link href="/" className="text-xs text-gray-500 hover:text-white">
          {"<- Dashboard"}
        </Link>
        <h1 className="text-2xl font-bold mt-1">Quant Research</h1>
        <p className="text-sm text-gray-400">
          Evidence-driven validation - Conservative scorecards - Paper trading first
        </p>
      </header>

      <DisciplineBanner
        executionEnabled={health?.execution_enabled}
        paperTrading={health?.paper_trading}
        conservativeMode={health?.conservative_mode}
      />

      {error && (
        <div className="card border-red-900/50 bg-red-950/30 text-sm text-red-200">{error}</div>
      )}

      <HealthStrip health={health} loading={bootLoading} />
      <OperationalAlerts
        alerts={health?.operational_alerts}
        dataQuality={health?.data_quality_recent}
      />

      {analytics && (
        <section className="card">
          <h2 className="font-semibold mb-3">Signal quality</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <Stat label="Approved" value={String(analytics.approved)} />
            <Stat label="Rejected" value={String(analytics.rejected)} />
            <Stat label="Rejection rate" value={`${rejectionPct}%`} hint="Selectivity proxy" />
            <Stat
              label="Calibration"
              value={rejectionPct > 60 ? "Strict" : rejectionPct > 40 ? "Moderate" : "Permissive"}
            />
          </div>
          <p className="text-xs text-gray-500 mt-2">{analytics.note}</p>
        </section>
      )}

      {scorecards && (
        <>
          <section className="card">
            <h2 className="font-semibold mb-3">Strategy scorecards</h2>
            <ScorecardTable rows={scorecards.scorecards} />
          </section>
          {scorecards.regime_summary && scorecards.regime_summary.length > 0 && (
            <section className="card">
              <h2 className="font-semibold mb-2">Regime comparison</h2>
              <p className="text-xs text-gray-500 mb-3">
                Which regimes support survivability - weak regimes warrant smaller size or no trade.
              </p>
              <RegimeComparisonTable rows={scorecards.regime_summary} />
            </section>
          )}
          {scorecards.recent_walk_forward && scorecards.recent_walk_forward.length > 0 && (
            <section className="card text-sm">
              <h2 className="font-semibold mb-2">Recent walk-forward</h2>
              <ul className="space-y-1">
                {scorecards.recent_walk_forward.map((w) => (
                  <li key={w.id} className="text-gray-300">
                    {w.symbol} - stability {w.stability}
                    {w.overfitting && <span className="text-amber-400 ml-2">overfitting</span>}
                    {w.decay && <span className="text-red-400 ml-2">decay</span>}
                  </li>
                ))}
              </ul>
            </section>
          )}
        </>
      )}

      {edge && (
        <section className="card">
          <h2 className="font-semibold mb-2">Edge stability</h2>
          <div className="grid md:grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-xs text-gray-500 uppercase mb-1">Top setups</p>
              <pre className="text-xs overflow-auto max-h-32 bg-surface p-2 rounded">
                {JSON.stringify(edge.top_setups, null, 2)}
              </pre>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase mb-1">Weakest setups</p>
              <pre className="text-xs overflow-auto max-h-32 bg-surface p-2 rounded">
                {JSON.stringify(edge.bottom_setups, null, 2)}
              </pre>
            </div>
          </div>
        </section>
      )}

      {paper && (
        <section className="card">
          <h2 className="font-semibold mb-2">Paper session (30d)</h2>
          <p className="text-sm">
            Opened {String(paper.paper_trades_opened)} - Closed {String(paper.closed_trades)} - Win rate{" "}
            {String(paper.win_rate_pct)}%
          </p>
          <p className="text-xs text-gray-500 mt-2">{String(paper.disclaimer)}</p>
        </section>
      )}

      <section className="card flex flex-wrap gap-2">
        <button type="button" className="btn-primary" disabled={loading} onClick={runWalkForward}>
          {loading ? "Running" : "Walk-forward test"}
        </button>
        <button type="button" className="btn-secondary" disabled={loading} onClick={runMonteCarlo}>
          Monte Carlo risk
        </button>
        <button type="button" className="btn-secondary" disabled={loading} onClick={() => refresh()}>
          Refresh data
        </button>
      </section>

      {wf && (
        <section className="card">
          <h2 className="font-semibold mb-2">Walk-forward result</h2>
          <pre className="text-xs overflow-auto max-h-48 bg-surface p-2 rounded">
            {JSON.stringify((wf as { report?: unknown }).report, null, 2)}
          </pre>
        </section>
      )}
      {mc && (
        <section className="card">
          <h2 className="font-semibold mb-2">Monte Carlo result</h2>
          <pre className="text-xs overflow-auto max-h-48 bg-surface p-2 rounded">
            {JSON.stringify((mc as { report?: unknown }).report, null, 2)}
          </pre>
        </section>
      )}
    </div>
  );
}

function Stat({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="bg-surface rounded-lg p-3 border border-border">
      <p className="text-xs text-gray-500">{label}</p>
      <p className="text-lg font-bold">{value}</p>
      {hint && <p className="text-[10px] text-gray-600">{hint}</p>}
    </div>
  );
}
