.DEFAULT_GOAL := help
BACKEND := backend
FRONTEND := frontend

.PHONY: help install backend-install frontend-install \
        db-up db-down db-reset db-shell \
        migrate migration downgrade migration-history \
        backend frontend test lint build \
        up down logs ps clean

help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

## ---- Setup ----
install: backend-install frontend-install ## Install backend + frontend deps

backend-install: ## uv sync backend deps
	cd $(BACKEND) && uv sync

frontend-install: ## npm install frontend deps
	cd $(FRONTEND) && npm install

## ---- Database (Postgres in Docker, host port 5433) ----
db-up: ## Start Postgres
	docker compose up -d --wait db

db-down: ## Stop Postgres
	docker compose stop db

db-reset: ## Drop the DB volume, restart Postgres and re-run migrations
	docker compose down -v
	$(MAKE) db-up
	$(MAKE) migrate

db-shell: ## psql into the database
	docker compose exec db psql -U todo -d todo

## ---- Migrations (Alembic) ----
migrate: ## Apply all migrations
	cd $(BACKEND) && uv run alembic upgrade head

migration: ## Autogenerate a migration: make migration m="add foo"
	@test -n "$(m)" || (echo 'usage: make migration m="message"' && exit 1)
	cd $(BACKEND) && uv run alembic revision --autogenerate -m "$(m)"

downgrade: ## Roll back one migration
	cd $(BACKEND) && uv run alembic downgrade -1

migration-history: ## Show migration history
	cd $(BACKEND) && uv run alembic history --verbose

## ---- Run locally ----
backend: db-up migrate ## Run API with reload (starts DB, migrates)
	cd $(BACKEND) && uv run uvicorn app.main:app --reload --port 8000

frontend: ## Run Vite dev server
	cd $(FRONTEND) && npm run dev

## ---- Quality ----
test: ## Run backend tests
	cd $(BACKEND) && uv run pytest

lint: ## Lint frontend
	cd $(FRONTEND) && npm run lint

build: ## Build frontend
	cd $(FRONTEND) && npm run build

## ---- Full stack in Docker ----
up: ## Build and start everything
	docker compose up -d --build

down: ## Stop everything
	docker compose down

logs: ## Tail logs
	docker compose logs -f

ps: ## Show containers
	docker compose ps

clean: ## Remove caches and build output
	find $(BACKEND) -name __pycache__ -type d -prune -exec rm -rf {} +
	rm -rf $(BACKEND)/.pytest_cache $(FRONTEND)/dist
