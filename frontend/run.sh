#!/usr/bin/env bash
# Starts the Vite dev server, installing dependencies first when needed.
set -euo pipefail
cd "$(dirname "$0")"
LOG_TAG=frontend
# shellcheck source=../scripts/log.sh
source ../scripts/log.sh
trap on_exit EXIT

require node "Install Node.js from https://nodejs.org"
require npm "Install Node.js from https://nodejs.org"

# Reinstall when node_modules is missing or older than the lockfile.
if [ ! -d node_modules ] || [ package-lock.json -nt node_modules ]; then
  info "Installing dependencies"
  npm ci --no-audit --no-fund --loglevel=error
  ok "Dependencies installed"
fi

info "Starting Vite dev server on http://localhost:5173 (proxying /api to ${VITE_PROXY_TARGET:-http://localhost:8000})"
exec npm run dev
