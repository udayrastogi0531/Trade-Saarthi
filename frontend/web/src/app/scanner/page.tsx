"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { apiGet, apiPost } from "@/lib/api";

type ScannerHealth = {
  status: string;
  latest_run_id?: string;
  avg_latency_ms?: number;
  runs?: Array<{
    run_id: string;
    health: string;
    symbols: number;
    approved: number;
    avg_latency_ms: number;
    errors: string[];
    started_at: string | null;
  }>;
};

type FeedItem = {
  symbol: string;
  approved: boolean;
  rank_score: number;
  quality_score: number;
  regime: string | null;
  structure_score: number;
  duration_ms: number | null;
  rejection_reasons: string[] | null;
  created_at: string;
};

export default function ScannerPage() {
  const [health, setHealth] = useState<ScannerHealth | null>(null);
  const [feed, setFeed] = useState<FeedItem[]>([]);
  const [watchlistMsg, setWatchlistMsg] = useState("");
  const [symbolsInput, setSymbolsInput] = useState("RELIANCE,TCS,INFY,HDFCBANK");
  const [loading, setLoading] = useState(false);
  const [lastRun, setLastRun] = useState<Record<string, unknown> | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const [h, f, w] = await Promise.all([
      apiGet<ScannerHealth>("/scanner/health"),
      apiGet<{ items: FeedItem[] }>("/scanner/feed?limit=15"),
      apiGet<{ watchlists: Array<{ name: string; symbols: string[] }> }>("/scanner/watchlist"),
    ]);
    setHealth(h);
    setFeed(f.items);
    const def = w.watchlists.find((x) => x.name === "default") ?? w.watchlists[0];
    if (def) {
      setSymbolsInput(def.symbols.join(","));
    }
  }, []);

  useEffect(() => {
    refresh().catch(console.error);
  }, [refresh]);

  const runScan = async (asyncJob: boolean) => {
    setLoading(true);
    setJobId(null);
    setLastRun(null);
    try {
      const symbols = symbolsInput
        .split(",")
        .map((s) => s.trim().toUpperCase())
        .filter(Boolean);
      const res = await apiPost<Record<string, unknown>>("/scanner/run", {
        symbols,
        async_job: asyncJob,
      });
      if (asyncJob && res.job_id) {
        setJobId(String(res.job_id));
      } else {
        setLastRun(res);
      }
      await refresh();
    } finally {
      setLoading(false);
    }
  };

  const saveWatchlist = async () => {
    setLoading(true);
    try {
      const symbols = symbolsInput
        .split(",")
        .map((s) => s.trim().toUpperCase())
        .filter(Boolean);
      await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/scanner/watchlist`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name: "default", symbols, scan_interval_minutes: 3 }),
        }
      );
      setWatchlistMsg("Watchlist saved");
      await refresh();
    } catch {
      setWatchlistMsg("Save failed - is the API running?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 pb-24">
      <header>
        <Link href="/" className="text-xs text-gray-500 hover:text-white">
          {"<- Dashboard"}
        </Link>
        <h1 className="text-2xl font-bold mt-1">Watchlist Scanner</h1>
        <p className="text-sm text-gray-400">
          Distributed market intelligence - Probability-based setups only
        </p>
      </header>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <Card label="Health" value={health?.status?.toUpperCase() ?? "--"} />
        <Card
          label="Avg latency"
          value={health?.avg_latency_ms ? `${Math.round(health.avg_latency_ms)} ms` : "--"}
        />
        <Card
          label="Last approved"
          value={
            health?.runs?.[0]
              ? `${health.runs[0].approved}/${health.runs[0].symbols}`
              : "--"
          }
        />
        <Card label="Feed items" value={String(feed.length)} />
      </div>

      <section className="card space-y-4">
        <h2 className="font-semibold">Watchlist</h2>
        <input
          className="w-full bg-black/40 border border-border rounded-lg px-3 py-2 text-sm"
          value={symbolsInput}
          onChange={(e) => setSymbolsInput(e.target.value)}
          placeholder="RELIANCE,TCS,INFY"
        />
        <div className="flex flex-wrap gap-2">
          <button type="button" className="btn-primary" disabled={loading} onClick={() => runScan(false)}>
            Run scan
          </button>
          <button type="button" className="btn-secondary" disabled={loading} onClick={() => runScan(true)}>
            Queue async job
          </button>
          <button type="button" className="btn-secondary" disabled={loading} onClick={saveWatchlist}>
            Save watchlist
          </button>
        </div>
        {watchlistMsg && <p className="text-xs text-gray-500">{watchlistMsg}</p>}
        {jobId && (
          <p className="text-xs text-accent">
            Job queued: {jobId} - poll GET /scanner/jobs/{jobId}
          </p>
        )}
      </section>

      {lastRun && (
        <section className="card">
          <h2 className="font-semibold mb-2">Latest run</h2>
          <pre className="text-xs overflow-auto max-h-48">{JSON.stringify(lastRun, null, 2)}</pre>
        </section>
      )}

      <section className="card">
        <h2 className="font-semibold mb-3">Signal feed (ranked)</h2>
        {feed.length === 0 ? (
          <p className="text-sm text-gray-500">No scanner results yet. Run a scan to populate.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 border-b border-border">
                  <th className="py-2">Symbol</th>
                  <th>Rank</th>
                  <th>Quality</th>
                  <th>Regime</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {feed.map((row) => (
                  <tr key={`${row.symbol}-${row.created_at}`} className="border-b border-border/50">
                    <td className="py-2 font-medium">{row.symbol}</td>
                    <td>{row.rank_score.toFixed(1)}</td>
                    <td>{row.quality_score.toFixed(1)}</td>
                    <td className="capitalize">{row.regime ?? "--"}</td>
                    <td>{row.approved ? "Approved" : "Rejected"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <p className="text-xs text-gray-600">
        Scanner output is probabilistic analysis, not financial advice. No profit guarantees.
      </p>
    </div>
  );
}

function Card({ label, value }: { label: string; value: string }) {
  return (
    <div className="card p-4">
      <p className="text-xs text-gray-500 uppercase">{label}</p>
      <p className="text-xl font-bold mt-1">{value}</p>
    </div>
  );
}
