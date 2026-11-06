# ADR 0006: Engineering stack, repository and CI

- Status: accepted
- Date: 2026-11-06

## Context
The screens (Event List, Filters, Event Detail) are designed. Before coding starts on 2026-11-13 we need a repository layout, data-access and mobile data libraries, and a CI approach. The owner confirmed the monorepo, said the library choices only need to fit the current scope, and will host the code on GitHub with GitHub Actions.

## Decision
- **Repository:** GitHub, https://github.com/huynguyenquangce/RunDex (owner's account). Monorepo: `src/backend`, `src/mobile`, `src/docker-compose.yml`, `.github/workflows`, `docs/`, `ai-inputs/`, `scripts/`. No client code or confidential data is ever pushed.
- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2 + Alembic, Pydantic v2, PostgreSQL 16 (`unaccent`, `pg_trgm`), ruff, pytest. Versioned REST `/v1`, keyset pagination, OpenAPI contract committed.
- **Mobile:** Expo + TypeScript (strict), Expo Router, TanStack Query with persisted cache, API types generated from OpenAPI (openapi-typescript), Jest + React Native Testing Library.
- **CI:** GitHub Actions: backend CI (lint, tests with a Postgres service, migrations, OpenAPI drift check, Docker build), mobile CI (typecheck, lint, tests, expo-doctor, API types drift check), security (gitleaks, dependency review, audits), Dependabot.
- **Deferred:** EAS preview builds and any store publishing (needs Expo/Apple accounts); revisit only if time allows.

## Alternatives considered
- Separate repos for backend and mobile: more overhead, harder for reviewers to run; rejected.
- Hand-written API client types: drift risk; rejected in favour of generated types.
- Heavier state libraries (Redux): not needed for this scope.

## Consequences
- One clone runs everything; CI checks both sides and the contract between them.
- The plan in docs/IMPLEMENTATION-PLAN.md is the working plan; libraries can still change if they prove a poor fit (record a new ADR).
- Dependabot ignores the Expo-managed packages (expo, react, react-native, typescript, jest and friends): they must change together with the SDK, and single bumps fail `expo-doctor` in CI. Upgrade them with `npx expo install expo@latest` then `npx expo install --fix`.
- The GitHub repo is outside the KMS Shared Drive; the submission folder must still contain all code, workflows and docs.

## AI involvement
AI proposed the stack and workflows; the owner confirmed the monorepo and the repo, and asked for choices that fit the current scope.
