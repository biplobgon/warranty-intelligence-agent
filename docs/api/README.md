# API Documentation

The primary, machine-readable contract is published at runtime:

| URL | Purpose |
|---|---|
| `/docs` | Swagger UI (interactive) |
| `/redoc` | ReDoc UI (read-only) |
| `/openapi.json` | OpenAPI 3.1 spec (machine-readable) |

This directory holds the supplemental human-readable docs.

| File | Purpose |
|---|---|
| [endpoints.md](endpoints.md) | Per-endpoint reference + examples |
| [auth.md](auth.md) | API key + production auth options |
| [error_handling.md](error_handling.md) | Error envelope, status codes, retry guidance |
| [rate_limits.md](rate_limits.md) | Rate-limiting + back-pressure |
| [client_examples.md](client_examples.md) | curl / Python / TypeScript examples |
