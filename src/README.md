# Source Code

Monorepo (ADR 0006).

```
src/
  backend/            FastAPI API (Python 3.12), PostgreSQL via Docker Compose
  mobile/             Expo (React Native + TypeScript) app, iOS + Android
  docker-compose.yml  PostgreSQL + API for local development
  .env.example        copy to src/.env (never commit real values)
```

Status: step 1 (scaffold). Backend exposes `GET /health`; the mobile app is the Expo blank TypeScript template. Event schema, list/detail API and screens follow docs/IMPLEMENTATION-PLAN.md.

Conventions: no secrets in code; configuration through environment variables; backend lint/format with ruff, tests with pytest; mobile typecheck with `npm run typecheck`.
