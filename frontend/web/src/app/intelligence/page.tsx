"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiGet } from "@/lib/api";
import { DisciplineBanner } from "@/components/DisciplineBanner";
import { VolatilityAdvisory } from "@/components/VolatilityAdvisory";
import type { ObservabilityHealth, VolatilityContext } from "@/lib/types";

type Panel = {
  market_regime: string;
  approved_signals_count: number;
  rejected_signals_count: number;
  top_setups: Array<{
    symbol: string;
    direction: string;
    confidence: number;
    quality: number;
    setup: string;
    regime: string;
  }>;
  confidence_heatmap: Record<string, number>;
  risk_flags: string[];
  directional_volatility_context?: VolatilityContext;
};

export default function IntelligencePage() {
  const [panel, setPanel] = useState<Panel | null>(null);
  const [health, setHealth] = useState<ObservabilityHealth | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      apiGet<Panel>("/intelligence/panel"),
      apiGet<ObservabilityHealth>("/observability/health"),
    ])
      .then(([p, h]) => {
        setPanel(p);
        setHealth(h);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load intelligence"));
  }, []);

  const total = (panel?.approved_signals_count ?? 0) + (panel?.rejected_signals_count ?? 0);
  const rejectPct = total ? Math.round(((panel?.rejected_signals_count ?? 0) / total) * 100) : 0;

  return (
    <div className="space-y-6 pb-24 px-1">
      <header>
        <Link href="/" className="text-xs text-gray-500 hover:text-white">
          {"<- Dashboard"}
        </Link>
        <h1 className="text-2xl font-bold mt-1">Market Intelligence</h1>
        <p className="text-sm text-gray-400">Regime - setups - risk flags - volatility advisory</p>
      </header>

      <DisciplineBanner
        executionEnabled={health?.execution_enabled}
        paperTrading={health?.paper_trading}
        conservativeMode={health?.conservative_mode}
      />

      {error && <div className="card text-sm text-red-300">{error}</div>}

      {panel && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Card label="Regime" value={panel.market_regime} />
            <Card label="Approved" value={String(panel.approved_signals_count)} />
            <Card label="Rejected" value={String(panel.rejected_signals_count)} />
            <Card label="Reject %" value={`${rejectPct}%`} warn={rejectPct > 55} />
          </div>

          {panel.risk_flags.length > 0 && (
            <div className="card border-amber-900/40 bg-amber-950/20 text-sm">
              <p className="font-semibold text-amber-200 mb-1">Risk flags</p>
              <ul className="list-disc pl-4">
                {panel.risk_flags.map((f) => (
                  <li key={f}>{f}</li>
                ))}
              </ul>
            </div>
          )}

          <VolatilityAdvisory context={panel.directional_volatility_context} />

          <section className="card">
            <h2 className="font-semibold mb-3">Top setups</h2>
            {panel.top_setups.length === 0 ? (
              <p className="text-sm text-gray-500">No approved setups in recent window.</p>
            ) : (
              <ul className="space-y-2 text-sm">
                {panel.top_setups.map((s) => (
                  <li
                    key={`${s.symbol}-${s.setup}`}
                    className="flex flex-wrap justify-between gap-2 border-b border-border/40 pb-2"
                  >
                    <span className="font-medium">
                      {s.symbol} - {s.direction} - {s.setup}
                    </span>
                    <span className="text-gray-400">
                      conf {s.confidence.toFixed(0)} - Q {s.quality.toFixed(0)} - {s.regime}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className="card">
            <h2 className="font-semibold mb-2">Confidence distribution</h2>
            <div className="flex flex-wrap gap-3">
              {Object.entries(panel.confidence_heatmap).map(([bucket, count]) => (
                <div key={bucket} className="bg-surface px-3 py-2 rounded-lg border border-border text-sm">
                  <span className="text-gray-500">{bucket}</span>
                  <span className="ml-2 font-bold">{count}</span>
                </div>
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
}

function Card({ label, value, warn }: { label: string; value: string; warn?: boolean }) {
  return (
    <div className={`card p-4 touch-manipulation ${warn ? "border-amber-800/50" : ""}`}>
      <p className="text-xs text-gray-500 uppercase">{label}</p>
      <p className="text-xl font-bold mt-1 capitalize">{value}</p>
    </div>
  );
}
