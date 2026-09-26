"use client";

import type { VolatilityContext } from "@/lib/types";

export function VolatilityAdvisory({ context }: { context: VolatilityContext | null | undefined }) {
  if (!context) return null;
  const warnings = context.warnings ?? [];
  return (
    <section className="card border-violet-900/40 bg-violet-950/15">
      <h2 className="font-semibold text-violet-200 mb-1">Directional volatility advisory</h2>
      <p className="text-xs text-gray-400 mb-3">
        Manual decision support only - not automated options trading. Regime:{" "}
        <span className="capitalize text-gray-200">{context.dominant_regime}</span>
        {context.confidence_reduction_suggested && (
          <span className="ml-2 text-amber-300">- Suggest lower confidence</span>
        )}
      </p>
      {warnings.length > 0 && (
        <ul className="text-sm space-y-1 list-disc pl-4 text-violet-100">
          {warnings.map((w) => (
            <li key={w}>{w}</li>
          ))}
        </ul>
      )}
      {context.momentum_exhaustion_note && (
        <p className="text-sm mt-3 text-amber-200/90">{context.momentum_exhaustion_note}</p>
      )}
      <p className="text-xs text-gray-500 mt-3">{context.disclaimer}</p>
    </section>
  );
}
