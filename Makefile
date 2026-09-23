.PHONY: up down migrate db-reset seed embed-model turn probe test check fmt llm-ping api-types mobile mobile-tunnel

ALEMBIC = uv run alembic -c apps/api/alembic.ini

up: migrate
	uv run fastapi dev --host 0.0.0.0 apps/api/src/kindred_api/main.py

down:
	docker compose down

migrate:
	docker compose up -d --wait db ollama
	$(ALEMBIC) upgrade head

# The ledger rejects DELETE, so wiping dev data means rebuilding the schema.
db-reset:
	docker compose up -d --wait db
	$(ALEMBIC) downgrade base
	$(ALEMBIC) upgrade head

embed-model:
	docker compose up -d --wait ollama
	docker compose exec ollama ollama pull qwen3-embedding:0.6b

seed: migrate
	uv run python -m kindred_api.seed curricula/aws-2week.yaml

# make turn ARGS='"What is a bucket policy?" --day 3 --time 10:00'
turn:
	uv run python -m kindred_api.try_turn $(ARGS)

# make probe ARGS='--limit 10'
probe:
	docker compose up -d --wait db ollama
	uv run python -m kindred_api.probes $(ARGS)

test:
	docker compose up -d --wait db
	uv run pytest

check:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy apps/api packages
	uv run mypy conftest.py
	npm --prefix apps/mobile run lint
	cd apps/mobile && npx tsc --noEmit

fmt:
	uv run ruff format .
	uv run ruff check --fix .

llm-ping:
	uv run python -m kindred_api.llm_ping

api-types:
	uv run python -m kindred_api.openapi_export apps/mobile/openapi.json
	cd apps/mobile && npx openapi-ts

mobile:
	cd apps/mobile && npx expo start

mobile-tunnel:
	cd apps/mobile && npx expo start --tunnel
