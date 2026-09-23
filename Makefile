.PHONY: up down test check fmt llm-ping mobile mobile-tunnel

up:
	docker compose up -d --wait db
	uv run fastapi dev --host 0.0.0.0 apps/api/src/kindred_api/main.py

down:
	docker compose down

test:
	uv run pytest

check:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy apps/api packages
	npm --prefix apps/mobile run lint

fmt:
	uv run ruff format .
	uv run ruff check --fix .

llm-ping:
	uv run python -m kindred_api.llm_ping

mobile:
	cd apps/mobile && npx expo start

mobile-tunnel:
	cd apps/mobile && npx expo start --tunnel
