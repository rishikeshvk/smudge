# Kindred — agent instructions

## What this is
An AI study buddy that learns the same subject as the user, on its own schedule,
and only knows what it has already covered. Plan and philosophy: @docs/plan.md

## Hard invariants — never violate
1. The knowledge ledger is append-only. Never UPDATE or DELETE its rows.
2. All knowledge retrieval goes through one repository function that applies the
   unlock-date filter in SQL. Never write a gated query anywhere else.
3. Components exchange typed Pydantic schemas from `packages/contracts`, never
   free-form text.
4. All time access goes through the Clock service. Never call `datetime.now()`
   or `time.time()` directly outside it.
5. No buddy message is sent without an audit pass.
6. When unsure whether content is locked, fail closed and deflect.
7. API keys live only on the backend. Never log them, never return them to the app.

## Stack and layout
- `apps/api` — FastAPI, Python 3.12, uv.
- `apps/mobile` — React Native + Expo, TypeScript, Android only. Types are
  generated from the API's OpenAPI schema, not hand-written.
- `packages/` — `contracts` (schemas), `gate` (classifier, retrieval, auditor),
  `llm` (provider client), `db` (SQLAlchemy models and engine; migrations live in
  `apps/api/migrations`).
- Postgres + pgvector via Docker. Migrations with alembic; never edit an applied
  migration.
- LLM access is bring-your-own-key: an OpenAI-compatible base URL, API key and a
  model per role, all from config. No provider-specific SDK outside `packages/llm`.
  Model output is schema-validated and retried on parse failure.

## Conventions
- ruff + mypy strict, pytest.
- Conventional commits, one logical change per commit.

## Code style
- Code should read on its own: clear names, small focused functions, early returns.
  Prefer the simplest thing that works; refactor when a second use appears, not before.
- Comments explain *why*, never *what*: only where the code can't say it, one short line.
  No commented-out code, no section banners, no docstrings that repeat the signature.
- Full type hints (Python) and strict TypeScript; avoid `Any`/`any`. Pydantic models at
  boundaries, plain functions and dataclasses inside.
- One concept per module. No `utils`/`helpers` catch-alls; name files after what they hold.
- No speculative code: no unused parameters, flags, config or abstractions "for later".
- Handle errors at boundaries; don't catch what you can't handle or silently swallow it.
- Config comes from settings objects, never inline literals or scattered env reads.
- Add dependencies with `uv add` / `npx expo install` (latest compatible); don't hand-pick
  versions or edit lockfiles. Prefer official generators and templates over hand-written
  boilerplate.
- Formatting and import order belong to the tools (`ruff format`, `expo lint`); don't hand-style.
- Tests check behaviour through public interfaces, one test file per module, named for
  what they prove. No network in unit tests.

## Commands
First run: `cp .env.example .env`, fill in the LLM values, then `uv sync --all-packages`.
- `make up` — Postgres (Docker), migrations, and the API with hot reload on :8000
- `make down` — stop Postgres
- `make migrate` — apply alembic migrations
- `make db-reset` — rebuild the schema, wiping dev data (the ledger can't be deleted from)
- `make test` — pytest
- `make check` — ruff, mypy and expo lint
- `make fmt` — ruff format and autofix
- `make llm-ping` — one real call to the configured LLM endpoint
- `make mobile` — Expo dev server; scan the QR code with Expo Go
- `make mobile-tunnel` — same over an ngrok tunnel, for networks where the phone can't reach the PC

## How to work with me
- I'm building this to learn agentic systems. Use plan mode for any new module:
  propose a design, wait for my approval, then implement.
- One step at a time. Never implement beyond the step I asked for.
- When you make a non-obvious choice, state the alternative you rejected.
- After finishing a task, add a short "what to study from this change" note: the
  key concepts and one thing worth reading further.
