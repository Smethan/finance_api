# Finance Aggregation API

FastAPI backend that aggregates personal finance data from Plaid and exposes a secure REST API that can be consumed by ChatGPT or other clients. The service handles Plaid item linking, stores transactions/holdings/balances in Postgres, and publishes analytics such as net worth and cashflow summaries.

## Highlights
- **Plaid integration** for transactions, account balances, and investment holdings (async + delta sync).
- **PostgreSQL persistence** using SQLAlchemy models with encrypted Plaid access tokens.
- **Analytics endpoints** for accounts, transactions, holdings, net worth history, and cash flow summaries.
- **Background sync pipeline** with APScheduler + worker entry point for nightly refreshes and webhook handling.
- **JWT authentication** suitable for personal use or integration with a ChatGPT custom GPT/plugin.

## Project Structure
```
app/
  api/                # FastAPI routers and dependencies
  core/               # Settings, database, security, and logging helpers
  models/             # SQLAlchemy ORM models
  schemas/            # Pydantic response models
  services/           # Plaid client, repositories, analytics, auth, sync orchestration
  workers/            # Background sync entry point
infra/
  docker-compose.yml  # Local stack (API + Postgres)
  render.yaml         # Render deployment definition
scripts/
  init_db.py          # Create database tables via SQLAlchemy metadata
tests/
  test_app_initialization.py
```

## Prerequisites
- Python 3.11+
- Postgres 15+ (local or managed)
- Plaid developer account (Sandbox keys are fine for testing)
- Optional: Docker Compose for local orchestration

## Setup & Installation
1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install --upgrade pip
   pip install -e ".[dev]"
   ```
3. Copy `.env.example` to `.env` and populate secrets.
   ```bash
   cp .env.example .env
   ```

Important environment variables:
- `PLAID_CLIENT_ID`, `PLAID_SECRET`, `PLAID_ENV`
- `DATABASE_URL` (e.g. `postgresql+asyncpg://postgres:postgres@localhost:5432/finance`)
- `ENCRYPTION_KEY_BASE64` (generate via `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`)
- `JWT_SECRET_KEY`

## Database Bootstrapping
Create tables with the provided script:
```bash
python scripts/init_db.py
```
> For production, adapt this into an Alembic migration workflow.

## Local Development
Start the stack with Docker Compose:
```bash
docker compose -f infra/docker-compose.yml up --build
```
Or run the API directly:
```bash
uvicorn app.main:app --reload
```
The OpenAPI docs are exposed at `http://localhost:8000/docs`.

## Plaid Linking Flow
1. Call `POST /v1/auth/token` with email/external_id to obtain a bearer token.
2. Call `POST /v1/plaid/link-token` (authenticated) to retrieve a Plaid Link token.
3. Complete Plaid Link (host a simple static page) and send the resulting `public_token` to `POST /v1/plaid/item/public-token/exchange`.
4. Trigger an initial sync via `POST /v1/sync/trigger`.

Webhook support (`POST /v1/sync/plaid/webhook`) automatically re-syncs when Plaid notifies updates.

## Key Endpoints
- `GET /v1/accounts` / `GET /v1/accounts/{id}`
- `GET /v1/transactions`
- `GET /v1/holdings`
- `GET /v1/net-worth`
- `GET /v1/cashflow/summary`
- `POST /v1/sync/trigger`
- `POST /v1/plaid/link-token`
- `POST /v1/plaid/item/public-token/exchange`
- `POST /v1/auth/token`

## Background Sync
- APScheduler runs a daily job (cron configurable via `SCHED_BALANCE_REFRESH_CRON`) to refresh items.
- Render cron job (see `infra/render.yaml`) or Fly.io tasks can invoke `python -m app.workers` for scheduled syncs.

## Deployment
- **Render**: Use `infra/render.yaml` to bootstrap a free tier web service and cron job.
- **Fly.io / Railway**: Container builds via the included `Dockerfile`.
- Remember to set environment variables/secrets and configure HTTPS.

## ChatGPT Integration
- Expose `https://{your-domain}/openapi.json`.
- Register the API as a custom GPT or plugin, providing the bearer token as a securely stored secret.
- Suggested prompt instructions for ChatGPT:
  > "You can query `GET /v1/net-worth` for current net worth, `GET /v1/transactions?limit=20` for recent transactions, and `GET /v1/cashflow/summary` to summarize spending."

## Testing & Linting
- Run the lightweight health check test:
  ```bash
  pytest
  ```
- Format & lint suggestions:
  ```bash
  ruff check app tests
  mypy app
  ```

## Next Steps
- Add Alembic migrations and automated CI pipeline.
- Harden auth (Supabase auth, multi-user support) if you plan to share the service.
- Expand analytics (budgeting, category rollups) and caching as your dataset grows.
