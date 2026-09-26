# JSX SANITIZATION REPORT (v4.0.2)

## Scope
Sanitized frontend TSX/JSX sources in frontend/web/src to remove non-ASCII and corrupted characters that caused JSX parsing failures.

## Sanitization Actions
- Replaced common Unicode punctuation with ASCII equivalents (em dash, bullets, arrows, ellipsis).
- Removed residual non-ASCII control bytes and mojibake sequences.
- Normalized corrupted strings and placeholders to valid ASCII text.
- Restored JSX-safe text nodes for dashboard links using explicit string literals.

## Files Updated
- frontend/web/src/app/page.tsx
- frontend/web/src/app/research/page.tsx
- frontend/web/src/app/intelligence/page.tsx
- frontend/web/src/app/scanner/page.tsx
- frontend/web/src/app/copilot/page.tsx
- frontend/web/src/components/DisciplineBanner.tsx
- frontend/web/src/components/HealthStrip.tsx
- frontend/web/src/components/OperationalAlerts.tsx
- frontend/web/src/components/ScorecardTable.tsx
- frontend/web/src/components/VolatilityAdvisory.tsx

## Verification
- Non-ASCII scan: no remaining non-ASCII characters in frontend/web/src.
- JSX parsing: restored valid JSX text nodes and attribute strings.
