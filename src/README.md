# Source Code

Monorepo (ADR 0006).

```
src/
  backend/            FastAPI API (Python 3.12), PostgreSQL via Docker Compose
  mobile/             Expo (React Native + TypeScript) app, iOS + Android
  docker-compose.yml  PostgreSQL + API for local development
  .env.example        copy to src/.env (never commit real values)
```

Status: step 4 done (mobile wired to the API with plain list/detail screens; designed screens come next). Step 3: Backend has the `events`/`distances` schema (Alembic), a fixture loader (`python -m app.seed <file>`, test data only; the database starts empty and events come from the ingestion pipeline), `GET /v1/events`, `GET /v1/events/{slug}` and `GET /health`, with the OpenAPI contract in `src/openapi/openapi.json`; the mobile app is the Expo blank TypeScript template. List/detail API and screens follow docs/IMPLEMENTATION-PLAN.md.

Conventions: no secrets in code; configuration through environment variables; backend lint/format with ruff, tests with pytest; mobile typecheck with `npm run typecheck`.
