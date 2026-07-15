# Security audit — deployable backend restoration

## Scope

- restored missing Flask application code
- configuration and deployment behavior
- user CRUD endpoints
- database access and error handling
- automated tests and CI

## Improvements

- no hardcoded application secrets
- production rejects missing or placeholder `SECRET_KEY`
- write methods are disabled until `API_WRITE_TOKEN` is configured
- write authentication uses constant-time comparison
- CORS defaults to explicit local origins and rejects wildcard production origins
- request bodies are capped at 64 KiB by default
- unknown fields are rejected to reduce over-posting risk
- duplicate identity conflicts are handled without exposing database errors
- generic JSON error responses avoid leaking stack traces
- browser security headers are applied to every response
- committed `.env`, database files, private keys, and common token formats are blocked in CI

## Residual risks

- a shared API token is not a substitute for user authentication or authorization
- automatic `create_all()` is suitable for this small baseline but should be replaced by migrations before schema evolution
- SQLite is suitable for local development; durable production deployments should use managed PostgreSQL
- no rate limiter is included because adding another runtime dependency was not justified for the current scope
