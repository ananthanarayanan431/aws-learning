# aws-learning

Todo app: FastAPI + Postgres (backend, managed with [uv](https://docs.astral.sh/uv/) and Alembic) and a Vite/React frontend.

Run `make help` to list every command.

## Local development

```bash
make install    # backend (uv sync) + frontend (npm install)
make backend    # starts Postgres, applies migrations, runs API on :8000
make frontend   # Vite dev server on :5173
make test
```

## Migrations

```bash
make migration m="add foo"   # autogenerate from app/models.py
make migrate                 # apply
make downgrade               # roll back one
```

Postgres is exposed on host port **5433** (not 5432) to avoid clashing with a local Postgres.

## Full stack in Docker

```bash
make up     # migrations run automatically when the backend container starts
make down
```
