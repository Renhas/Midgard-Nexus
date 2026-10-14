#!/usr/bin/env bash
# Thin wrapper around `docker compose exec web manage.py`.
# Usage: ./scripts/manage.sh seed_demo --clear
set -euo pipefail

cd "$(dirname "$0")/.."

exec docker compose exec web python src/manage.py "$@"
