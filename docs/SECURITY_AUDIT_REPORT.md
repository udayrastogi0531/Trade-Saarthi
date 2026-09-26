# Security audit report (final)

## Authentication & authorization

- **Optional** `X-API-Key` when `API_AUTH_ENABLED=true`. **Production:** enable + rotate keys; never commit keys.
- RBAC helpers exist in `modules/security/auth.py` — **not** universally enforced on every route; treat as **debt** unless extended.

## Audit logging

- `AuditLogger` + `audit_logs` table when `AUDIT_LOG_ENABLED=true`. Ensure high-value actions (capital stage change, emergency shutdown) are logged consistently (extend as needed).

## Secrets

- Broker and AI keys via environment only (`.env` / compose secrets). **No encryption at rest** in repo — rely on host/secret manager.

## Network

- CORS restricted when `DEBUG=false`. Terminate TLS at reverse proxy.

## Recommendations

1. **WAF / bot protection** in front of public API.
2. **mTLS** for internal service-to-service if split deployment.
3. **CSP headers** on Next.js via hosting config.

## Residual risk

Insider misuse of valid API keys — mitigate with RBAC, IP allowlists, and short-lived tokens.
