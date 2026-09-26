"use client";

export function OperationalAlerts({
  alerts,
  dataQuality,
}: {
  alerts?: string[];
  dataQuality?: Array<{ symbol: string | null; event_type: string; severity: string }>;
}) {
  const hasAlerts = (alerts?.length ?? 0) > 0;
  const hasDq = (dataQuality?.length ?? 0) > 0;
  if (!hasAlerts && !hasDq) return null;

  return (
    <div className="space-y-2">
      {hasAlerts && (
        <div className="card border-amber-900/50 bg-amber-950/25 text-sm text-amber-100">
          <p className="font-semibold text-amber-200 mb-1">Operational alerts</p>
          <ul className="list-disc pl-4 space-y-0.5">
            {alerts!.map((a) => (
              <li key={a}>{formatAlert(a)}</li>
            ))}
          </ul>
        </div>
      )}
      {hasDq && (
        <div className="card border-red-900/40 bg-red-950/20 text-sm text-red-100">
          <p className="font-semibold mb-1">Data quality</p>
          <ul className="space-y-1 text-xs">
            {dataQuality!.map((e, i) => (
              <li key={`${e.event_type}-${i}`}>
                {e.symbol ?? "feed"} - {e.event_type} - <span className="uppercase">{e.severity}</span>
              </li>
            ))}
          </ul>
          <p className="text-xs text-red-300/80 mt-2">
            Reduce confidence; do not treat signals as normal until resolved.
          </p>
        </div>
      )}
    </div>
  );
}

function formatAlert(code: string): string {
  const map: Record<string, string> = {
    "scanner:degraded": "Scanner performance degraded - review latency",
    "scanner:unhealthy": "Scanner unhealthy - check worker logs",
    scanner_queue_backlog: "Scanner queue backlog - scale workers or reduce watchlist",
    elevated_execution_failures: "Elevated execution failures - review simulation logs",
    data_quality_feed_issues: "Data feed issues detected - signals may be blocked",
  };
  return map[code] ?? code;
}
