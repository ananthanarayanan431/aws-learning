#!/usr/bin/env bash
# Waits for Postgres, applies migrations, then starts the API with auto-reload.
# Postgres must be reachable at DATABASE_URL (backend/.env); `make backend` starts it for you.
set -euo pipefail
cd "$(dirname "$0")"
LOG_TAG=backend
# shellcheck source=../scripts/log.sh
source ../scripts/log.sh
trap on_exit EXIT

PORT="${PORT:-8000}"
DB_WAIT_SECONDS="${DB_WAIT_SECONDS:-30}"

require uv "Install it from https://docs.astral.sh/uv/getting-started/installation/"
[ -f .env ] || warn "backend/.env not found, using defaults (copy .env.example to override)"

info "Syncing dependencies"
uv sync --quiet

info "Waiting for database (up to ${DB_WAIT_SECONDS}s)"
if ! uv run --quiet python - "$DB_WAIT_SECONDS" <<'PY'
import asyncio, sys, time
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine
from app.config import settings

async def main(deadline: float) -> int:
    url = make_url(settings.database_url)
    engine = create_async_engine(url)
    last = ""
    while time.monotonic() < deadline:
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return 0
        except Exception as exc:  # noqa: BLE001
            last = f"{type(exc).__name__}: {exc}".splitlines()[0]
            await asyncio.sleep(1)
    print(f"  {url.host}:{url.port}/{url.database} unreachable ({last})", file=sys.stderr)
    return 1

sys.exit(asyncio.run(main(time.monotonic() + float(sys.argv[1]))))
PY
then
  die "Database is not reachable. Start it with 'make db-up' or check DATABASE_URL."
fi
ok "Database is up"

info "Applying migrations"
start=$SECONDS
# Alembic's own INFO lines are noisy; keep them unless it fails.
if out=$(uv run --quiet alembic upgrade head 2>&1); then
  echo "$out" | grep -E "Running upgrade" | sed 's/^INFO  \[alembic.runtime.migration\] /  /' || true
  ok "Migrations up to date ($((SECONDS - start))s)"
else
  echo "$out" >&2
  die "Migration failed"
fi

info "Starting API on http://localhost:${PORT} (docs: /docs)"
exec uv run --quiet uvicorn app.main:app --reload --port "$PORT"
