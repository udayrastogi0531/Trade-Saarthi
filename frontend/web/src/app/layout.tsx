import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Trading Intelligence",
  description: "Institutional-grade quantitative trading assistant",
};

const nav = [
  { href: "/research", label: "Research" },
  { href: "/intelligence", label: "Intel" },
  { href: "/scanner", label: "Scanner" },
  { href: "/copilot", label: "Copilot" },
];

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <nav className="border-b border-border bg-panel/80 backdrop-blur sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex flex-wrap items-center justify-between gap-3">
            <Link href="/" className="text-lg font-semibold tracking-tight shrink-0">
              AI Trading <span className="text-accent">Intelligence</span>
            </Link>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
              {nav.map((n) => (
                <Link key={n.href} href={n.href} className="text-accent hover:underline">
                  {n.label}
                </Link>
              ))}
            </div>
            <span className="text-xs text-gray-500 w-full sm:w-auto sm:text-right">
              v4.0.2 - Paper-first - Not financial advice
            </span>
          </div>
        </nav>
        <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8">{children}</main>
      </body>
    </html>
  );
}
