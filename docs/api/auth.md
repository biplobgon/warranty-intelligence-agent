# API Authentication

## Development

API key via header:

```
X-API-Key: <your-key>
```

In development, if `API_KEY` is the default placeholder
(`dev-local-key-change-me`), authentication is **bypassed** for convenience.
In production, the same placeholder triggers a 500 — set a real key.

## Production options (recommended)

The shipped middleware is intentionally minimal. For production deployments,
prefer:

1. **OIDC at the edge** (e.g. Google IAP, AWS ALB OIDC, Cloudflare Access)
   in front of the ingress. The API stays unauthenticated internally; the
   edge enforces identity.
2. **mTLS** via service mesh (Istio / Linkerd) for service-to-service calls.
3. **OAuth 2.1 + JWT bearer tokens** if the API is consumed by external
   third-party apps; validate via a `Depends(jwt_required)` dependency.

## Rotating the API key

- Generate a 32+ byte random token.
- Update the secret (`warranty-api-secrets` in K8s).
- Roll the deployment (`kubectl rollout restart deploy/warranty-api`).
- Communicate the new key to consumers via your secure channel.

## CORS

Configured via `ALLOWED_ORIGINS` env (comma-separated). Default `*` is
for development — restrict in production to your domain(s).

## Rate limiting

Not implemented at the application layer (keep API focused). Apply at:

- Ingress (NGINX `limit_req`, `nginx.ingress.kubernetes.io/limit-rps`)
- API gateway (e.g. Kong, Apigee, Cloud Endpoints)
- WAF (Cloudflare, AWS WAF, Cloud Armor)

See `rate_limits.md` for recommended values.

## Audit

- Failed auth attempts surface as HTTP 401 with the `x-request-id` header set.
- The structured log carries `request_id`, `path`, `method`, and (when known)
  `api_key_id` — NEVER log the raw key.
- Tail aggregator logs for `http_exception` events with `status=401`.
