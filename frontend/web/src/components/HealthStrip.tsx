"use client";

import type { ObservabilityHealth } from "@/lib/types";

export function HealthStrip({ health, loading }: { health: ObservabilityHealth | null; loading?: boolean }) {
  if (loading && !health) {
    return <p className="text-sm text-gray-500 animate-pulse">Loading operational health</p>;
  }
  if (!health) return null;

  const queue = health.scanner_queue_depth;
  const queueWarn = queue != null && queue > 50;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
      <Tile label="System" value={health.status} warn={health.status !== "ok"} />
      <Tile label="Redis" value={health.redis ? "OK" : "Down"} warn={!health.redis} />
      <Tile
        label="Scanner"
        value={health.scanner_health}
        warn={["degraded", "unhealthy"].includes(health.scanner_health)}
      />
      <Tile label="Queue" value={queue != null ? String(queue) : "--"} warn={queueWarn} />
      <Tile
        label="Data quality"
        value={health.data_quality_issues ? `${health.data_quality_issues} issue(s)` : "OK"}
        warn={(health.data_quality_issues ?? 0) > 0}
      />
      <Tile label="Exec quality" value={`${Math.round(health.execution_quality_score ?? 0)}%`} />
    </div>
  );
}

function Tile({ label, value, warn }: { label: string; value: string; warn?: boolean }) {
  return (
    <div className={`card p-3 ${warn ? "border-amber-800/60 bg-amber-950/20" : ""}`}>
      <p className="text-[10px] uppercase tracking-wider text-gray-500">{label}</p>
      <p className="text-sm font-semibold mt-0.5 capitalize truncate">{value}</p>
    </div>
  );
}
