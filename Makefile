.PHONY: up down migrate db-reset seed ingest embed-model turn probe simulate test check fmt llm-ping api-types icons invite users revoke mobile mobile-tunnel mobile-usb mobile-build

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

# Fetches each topic's reading list from the web; stored pages are skipped.
ingest: migrate
	uv run python -m kindred_api.ingest

# make turn ARGS='"What is a bucket policy?" --day 3 --time 10:00'
turn:
	uv run python -m kindred_api.try_turn $(ARGS)

# make probe ARGS='--limit 10'
probe:
	docker compose up -d --wait db ollama
	uv run python -m kindred_api.probes $(ARGS)

# make simulate ARGS='--days 14'. Real LLM calls: about 150 for 14 days.
simulate:
	docker compose up -d --wait db ollama
	uv run python -m kindred_api.simulate $(ARGS)

test:
	docker compose up -d --wait db
	uv run pytest
	npm --prefix apps/mobile test

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

# make invite: a code for a new friend; ARGS='--user 1' for an existing user, '--owner' on a fresh database.
invite:
	uv run python -m kindred_api.accounts invite $(ARGS)

users:
	uv run python -m kindred_api.accounts users

# make revoke ARGS='--user 3': signs them out on every phone and stops their pushes.
revoke:
	uv run python -m kindred_api.accounts revoke $(ARGS)

llm-ping:
	uv run python -m kindred_api.llm_ping

api-types:
	uv run python -m kindred_api.openapi_export apps/mobile/openapi.json
	cd apps/mobile && npx openapi-ts

# Renders the app icon, splash and notification icon from the SVGs in assets/brand (needs rsvg-convert).
# They are native assets: a new development build picks them up.
BRAND = apps/mobile/assets/brand
IMAGES = apps/mobile/assets/images
icons:
	rsvg-convert -w 1024 -h 1024 $(BRAND)/icon.svg -o $(IMAGES)/icon.png
	rsvg-convert -w 48 -h 48 $(BRAND)/icon.svg -o $(IMAGES)/favicon.png
	rsvg-convert -w 1024 -h 1024 $(BRAND)/adaptive-foreground.svg -o $(IMAGES)/android-icon-foreground.png
	rsvg-convert -w 1024 -h 1024 $(BRAND)/monochrome.svg -o $(IMAGES)/android-icon-monochrome.png
	rsvg-convert -w 96 -h 96 $(BRAND)/notification.svg -o $(IMAGES)/notification-icon.png
	rsvg-convert -w 416 -h 416 $(BRAND)/splash-light.svg -o $(IMAGES)/splash-icon.png
	rsvg-convert -w 416 -h 416 $(BRAND)/splash-dark.svg -o $(IMAGES)/splash-icon-dark.png

mobile:
	cd apps/mobile && npx expo start

mobile-tunnel:
	cd apps/mobile && npx expo start --tunnel

# The phone reaches Metro and the API as localhost over a USB cable.
mobile-usb:
	adb reverse tcp:8081 tcp:8081
	adb reverse tcp:8000 tcp:8000
	cd apps/mobile && npx expo start --localhost

# The development build with push notifications; install the APK it links to on the phone.
mobile-build:
	cd apps/mobile && npx eas-cli@latest build --profile development --platform android
