"use client";

type Props = {
  executionEnabled?: boolean;
  paperTrading?: boolean;
  conservativeMode?: boolean;
};

export function DisciplineBanner({ executionEnabled, paperTrading, conservativeMode }: Props) {
  const live = executionEnabled === true;
  return (
    <div className="card border-slate-700/80 bg-slate-900/60 text-sm space-y-2">
      <p className="text-slate-300">
        <span className="font-semibold text-white">Research mode.</span> Evidence-driven analysis only - no
        profit guarantees. Paper trading first; live capital requires staged governance approval.
      </p>
      <div className="flex flex-wrap gap-2 text-xs">
        <Badge ok={paperTrading !== false} label={paperTrading !== false ? "Paper ON" : "Paper OFF"} />
        <Badge ok={!live} label={live ? "Live execution ON" : "Live execution OFF"} warn={live} />
        <Badge ok={conservativeMode !== false} label={conservativeMode !== false ? "Conservative" : "Standard"} />
      </div>
    </div>
  );
}

function Badge({ label, ok, warn }: { label: string; ok: boolean; warn?: boolean }) {
  const cls = warn
    ? "bg-amber-950/50 text-amber-200 border-amber-800/50"
    : ok
      ? "bg-emerald-950/40 text-emerald-200 border-emerald-900/40"
      : "bg-slate-800 text-slate-400 border-slate-700";
  return <span className={`px-2 py-0.5 rounded border ${cls}`}>{label}</span>;
}
