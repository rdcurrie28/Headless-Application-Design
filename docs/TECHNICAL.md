# Customer Insights: technical guide

The detailed companion to the [project README](../README.md).

Headless backend for a sales "single pane of glass". It federates three sources behind one REST contract so the UI never talks to a database directly.

| Source | Owns | Access |
|---|---|---|
| Snowflake | Entitlements (SKUs), daily usage, product health, propensity scores written by Snowpark ML | read-only role, cached |
| Postgres | Customer master / account teams / primary contact (name, phone, address), rep next-step actions (the app's own writable state) | read + write |
| S3 | Per-customer documents (QBRs, order forms, success plans) | list + presigned GET URLs |

## How it is built, smallest piece first

1. **Sources** (`app/sources/`) — one thin class per system. Each does only three things: `connect`, `close`, `ping`, plus a raw fetch. Snowflake and boto3 are synchronous drivers, so calls run in `asyncio.to_thread`; Postgres uses an `asyncpg` pool. Nothing here knows about customers.
2. **Repositories** (`app/repositories/`) — the only place SQL or S3 keys live. `protocols.py` defines the three contracts (`CustomerRepository`, `InsightsRepository`, `DocumentRepository`). Each has a live implementation and a fake (`fake.py`) with the same signatures.
3. **Schemas** (`app/schemas.py`) — Pydantic models that are the API contract the UI codes against. Repositories return these, never raw rows.
4. **Cache** (`app/cache.py`) — per-key TTL cache with a lock per key, so 20 reps opening the same account fire one warehouse query, not 20. Applied to Snowflake reads only.
5. **Services** (`app/services/`)
   - `CachedInsights` wraps the Snowflake and S3 repositories with the cache.
   - `Customer360Service` fans out all five sections concurrently with `asyncio.gather`. Each section is wrapped in a timeout + try/except, so a suspended warehouse or slow S3 returns `null` for that section plus an entry in `errors[]` rather than failing the whole page. It also computes the summary strip and the recommended motion (`retain`, `expand`, `retain_and_expand`, `nurture`).
   - `PortfolioService` does the cross-source join: top scores from Snowflake, names/owners from Postgres.
6. **Container** (`app/container.py`) — wires it together. Each source is independently `live` or `fake` via env vars, so you can run real Postgres + MinIO locally while Snowflake stays fake.
7. **API** (`app/api/`) — FastAPI routers. `X-API-Key` header auth when `CI_API_KEYS` is set; CORS restricted to `CI_CORS_ORIGINS`.

## Endpoints

| Method | Path | UI panel |
|---|---|---|
| GET | `/healthz` | liveness |
| GET | `/readyz` | per-source ping; 503 if any source is down |
| GET | `/v1/customers?search=&region=&owner=&limit=&offset=` | account picker |
| GET | `/v1/customers/{id}` | header |
| GET | `/v1/customers/{id}/360` | whole page in one call |
| GET | `/v1/customers/{id}/skus` | SKUs by customer, ARR, utilization |
| GET | `/v1/customers/{id}/product-health` | health tiles, worst first |
| GET | `/v1/customers/{id}/propensity` | churn / expansion gauges + drivers |
| GET | `/v1/customers/{id}/documents` | doc list with presigned links |
| GET / POST | `/v1/customers/{id}/actions` | rep next steps |
| GET | `/v1/portfolio/at-risk?min_score=&owner=` | churn watchlist |
| GET | `/v1/portfolio/expansion?min_score=&owner=` | expansion targets |
| POST | `/v1/admin/cache/clear?prefix=` | force refresh after a scoring run |

Interactive docs at `/docs`; the OpenAPI spec at `/openapi.json` can generate a typed client for the front end (e.g. `openapi-typescript`).

## Run it

All-fake, no infrastructure:

```bash
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
curl localhost:8000/v1/customers/C-1005/360
pytest -q
```

Real Postgres + MinIO (S3), fake Snowflake:

```bash
cp .env.example .env
docker compose up --build
curl -H "X-API-Key: dev-key-change-me" localhost:8000/readyz
```

Real Snowflake: run `sql/snowflake/001_sales_insights.sql`, create a service user with key-pair auth granted `INSIGHTS_API_RO`, fill in the `CI_SNOWFLAKE_*` values, and set `CI_SNOWFLAKE_MODE=live`.

## Snowflake objects

- `ENTITLEMENTS`, `USAGE_DAILY` — raw inputs; rename the columns in `snowflake_insights.py` if yours differ.
- `PRODUCT_HEALTH` view — 30-day utilization vs entitlement and 30-over-30 trend, blended 70/30 into a 0–100 score. This formula is a placeholder; swap in your own health logic and the API is unaffected.
- `PROPENSITY_SCORES` — your Snowpark ML batch job appends here (`customer_id, model_name ['churn'|'expansion'], model_version, score, scored_at, top_drivers ARRAY`). `PROPENSITY_LATEST` keeps only the newest score per customer/model. When Cortex arrives, it writes to the same table and nothing downstream changes.

## Front end (`web/`)

React 19 + TypeScript + PatternFly 6, built with Vite.

How it is built, smallest piece first:

1. **Generated types** (`src/api/schema.d.ts`) — produced from the backend's OpenAPI spec by `openapi-typescript`. Regenerate with `npm run gen:api` (backend running) whenever an endpoint or schema changes; any UI code that no longer matches then fails `npm run typecheck`.
2. **Client** (`src/api/client.ts`) — `openapi-fetch` typed against those paths, plus `unwrap`, which turns an error response into a thrown `ApiError`.
3. **Type aliases** (`src/api/types.ts`) — short names (`Customer360`, `SkuEntitlement`, …) for the generated schemas.
4. **Query hooks** (`src/api/hooks.ts`) — one TanStack Query hook per screen need. Results are cached for 60s; logging an action invalidates that account's 360 so it refreshes.
5. **Shared pieces** (`src/components/`) — the PatternFly page shell with masthead and sidebar nav, a loading/error wrapper, and status labels (health, motion, drivers) with the color rules in one place.
6. **Screens** (`src/pages/`)
   - **Accounts** — search + pagination over `/v1/customers`.
   - **At-risk watchlist / Expansion targets** — one component, two modes, with an owner filter, score bars and driver chips.
   - **Customer 360** — header facts and recommended motion, a KPI strip, then cards for SKUs, product health, propensity, next steps (with an "Add" modal that POSTs an action) and documents. Each card is built from the matching section of the single `/360` call; if the API reports that section as failed, only that card shows "temporarily unavailable" and a warning banner names it.

**The API key never reaches the browser.** In dev, the Vite proxy adds `X-API-Key` to `/v1` calls; in Docker, nginx does. The browser only ever calls its own origin, so no CORS setup is needed either.

Run in dev (backend on :8000):

```bash
cd web
cp .env.example .env
npm install
npm run dev
```

Open http://localhost:3000. With Docker, `docker compose up --build` serves the built app at the same address. The `web` service passes `CI_API_KEYS` to nginx as one key, so set a single key there (or a separate `API_KEY`) when using compose.

## Next steps worth doing before production

- Replace API keys with OIDC/JWT from your SSO and filter `/portfolio` and `/customers` by the caller's book of business.
- Move the cache to Redis if you run more than one replica.
- Point `PostgresCustomerRepository` at a Salesforce sync table if the CRM is the system of record for account ownership.
