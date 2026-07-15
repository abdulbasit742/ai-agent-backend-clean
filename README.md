# AI Agent Backend Clean

A small, deployable Flask API baseline restored from a repository whose application source had been removed. It currently provides a secure user CRUD API and a foundation for later AI-agent features without pretending those features already exist.

## What is included

- Flask application factory and API blueprint
- modern Flask-SQLAlchemy model and queries
- SQLite for local use and PostgreSQL URL support for production
- health/readiness endpoint
- paginated user reads
- validated create, update, and delete operations
- API-key protection for every write operation
- explicit CORS configuration and security headers
- unit/API tests, secret regression check, and GitHub Actions CI
- Gunicorn and Render deployment configuration

## Secure defaults

The API starts in **read-only mode** when `API_WRITE_TOKEN` is empty. Production also refuses to start with a missing, short, or placeholder `SECRET_KEY`, and it rejects wildcard CORS origins.

This is not a complete identity system. The shared write token protects administrative CRUD operations, but a future multi-user product should add real authentication, authorization, audit logs, and token rotation.

## Local setup

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Or on Linux/macOS:

```bash
source .venv/bin/activate
```

Install and configure:

```bash
python -m pip install -r requirements.txt
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Put generated values in `.env` for `SECRET_KEY` and `API_WRITE_TOKEN`, then run:

```bash
python app.py
```

The API is available at `http://127.0.0.1:5000/api`.

## API

| Method | Endpoint | Protection | Purpose |
| --- | --- | --- | --- |
| `GET` | `/api` | public | API metadata |
| `GET` | `/api/health` | public | database and write-mode readiness |
| `GET` | `/api/users` | public | paginated users |
| `GET` | `/api/users/<id>` | public | one user |
| `POST` | `/api/users` | `X-API-Key` | create user |
| `PATCH` | `/api/users/<id>` | `X-API-Key` | update user |
| `DELETE` | `/api/users/<id>` | `X-API-Key` | delete user |

Example:

```bash
curl -X POST http://127.0.0.1:5000/api/users \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_WRITE_TOKEN" \
  -d '{"username":"Abdul Basit","email":"user@example.com"}'
```

Pagination is bounded:

```text
GET /api/users?page=1&per_page=20
```

`per_page` cannot exceed 100.

## Configuration

| Variable | Default | Notes |
| --- | --- | --- |
| `APP_ENV` | `development` | Use `production` when deployed |
| `SECRET_KEY` | generated in development | Required and at least 32 characters in production |
| `API_WRITE_TOKEN` | empty | Empty means all writes return `503` |
| `DATABASE_URL` | `sqlite:///users.db` | Render/Postgres URLs are normalized for psycopg |
| `CORS_ORIGINS` | local Vite origins | Comma-separated; `*` is rejected in production |
| `MAX_CONTENT_LENGTH` | `65536` | Allowed range: 1 KiB to 1 MiB |
| `HOST` | `127.0.0.1` | Used only by `python app.py` |
| `PORT` | `5000` | Used only by `python app.py` |

## Verification

```bash
python -m compileall app.py src tests scripts
python -m unittest discover -s tests -v
python scripts/secret_check.py
```

## Render deployment

`render.yaml` installs the Python dependencies, launches Gunicorn, and uses `/api/health` for health checks. Configure `SECRET_KEY`, `API_WRITE_TOKEN`, `CORS_ORIGINS`, and `DATABASE_URL` in the Render dashboard. Prefer managed PostgreSQL because a service filesystem may not be durable.

## Design references

See [`docs/reference-review.md`](docs/reference-review.md) for the three-repository review and [`docs/security-audit.md`](docs/security-audit.md) for the changed-area audit.
