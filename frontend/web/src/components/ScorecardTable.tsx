"use client";

import type { RegimeSummaryRow, ScorecardRow } from "@/lib/types";

export function ScorecardTable({ rows }: { rows: ScorecardRow[] }) {
  if (!rows.length) {
    return <p className="text-sm text-gray-500">No scorecard data yet - run paper trades or backtests.</p>;
  }
  return (
    <div className="overflow-x-auto -mx-1">
      <table className="w-full text-sm text-left min-w-[640px]">
        <thead className="text-xs uppercase text-gray-500 border-b border-border">
          <tr>
            <th className="py-2 pr-2">Setup</th>
            <th className="py-2 pr-2">Regime</th>
            <th className="py-2 pr-2">N</th>
            <th className="py-2 pr-2">Win%</th>
            <th className="py-2 pr-2">Expectancy</th>
            <th className="py-2 pr-2">Stability</th>
            <th className="py-2">Edge</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={`${r.setup_type}-${r.regime}`} className="border-b border-border/50">
              <td className="py-2 pr-2 font-medium">{r.setup_type}</td>
              <td className="py-2 pr-2 capitalize text-gray-400">{r.regime}</td>
              <td className="py-2 pr-2">{r.trade_count}</td>
              <td className="py-2 pr-2">{r.win_rate_pct}%</td>
              <td className="py-2 pr-2">{r.expectancy.toFixed(3)}</td>
              <td className="py-2 pr-2">{(r.stability_score * 100).toFixed(0)}%</td>
              <td className="py-2">
                <EdgeBadge quality={r.edge_quality} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function RegimeComparisonTable({ rows }: { rows: RegimeSummaryRow[] }) {
  if (!rows.length) return null;
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="text-xs uppercase text-gray-500 border-b border-border">
          <tr>
            <th className="py-2 text-left">Regime</th>
            <th className="py-2 text-left">Setups</th>
            <th className="py-2 text-left">Trades</th>
            <th className="py-2 text-left">Avg win%</th>
            <th className="py-2 text-left">Survivability</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.regime} className="border-b border-border/40">
              <td className="py-2 capitalize">{r.regime}</td>
              <td className="py-2">{r.setup_count}</td>
              <td className="py-2">{r.trade_count}</td>
              <td className="py-2">{r.avg_win_rate_pct}%</td>
              <td className="py-2 capitalize">
                <SurvivabilityBadge level={r.survivability} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function EdgeBadge({ quality }: { quality: string }) {
  const cls =
    quality === "strong"
      ? "text-emerald-400"
      : quality === "moderate"
        ? "text-amber-300"
        : quality === "insufficient_sample"
          ? "text-gray-500"
          : "text-red-400";
  return <span className={cls}>{quality.replace("_", " ")}</span>;
}

function SurvivabilityBadge({ level }: { level: string }) {
  const cls =
    level === "strong" ? "text-emerald-400" : level === "moderate" ? "text-amber-300" : "text-red-400";
  return <span className={cls}>{level}</span>;
}
