#!/usr/bin/env bash
# Stops containers and deletes all application data (volumes).
# Leaves .env untouched.
set -euo pipefail

if [ -t 1 ]; then
    RED=$'\033[0;31m'; GREEN=$'\033[0;32m'; YELLOW=$'\033[1;33m'; NC=$'\033[0m'
else
    RED=''; GREEN=''; YELLOW=''; NC=''
fi

err()  { printf '%sERROR:%s %s\n' "$RED" "$NC" "$*" >&2; }
info() { printf '%sOK:%s %s\n' "$GREEN" "$NC" "$*"; }
warn() { printf '%sWARNING:%s %s\n' "$YELLOW" "$NC" "$*" >&2; }

YES=0

usage() {
    cat <<EOF
Usage: $(basename "$0") [-y|--yes] [-h|--help]

Stops containers and deletes all application data (database, uploads,
users). Leaves .env untouched.

  -y, --yes    Skip the confirmation prompt
  -h, --help   Show this help
EOF
}

while [ $# -gt 0 ]; do
    case "$1" in
        -y|--yes) YES=1 ;;
        -h|--help) usage; exit 0 ;;
        *) err "Unknown option: $1"; usage >&2; exit 1 ;;
    esac
    shift
done

# --- Locate project root ---------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/../docker-compose.yml" ]; then
    PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
elif [ -f "$SCRIPT_DIR/docker-compose.yml" ]; then
    PROJECT_ROOT="$SCRIPT_DIR"
else
    err "docker-compose.yml not found next to scripts/."
    exit 1
fi

# --- Docker sanity ---------------------------------------------------------
if ! command -v docker >/dev/null 2>&1; then
    err "Docker is not installed or not in PATH."
    err "Install Docker: https://docs.docker.com/engine/install/"
    exit 1
fi
if ! docker info >/dev/null 2>&1; then
    err "Docker is not running. Start the Docker daemon and try again."
    exit 1
fi

# --- Confirmation ----------------------------------------------------------
if [ "$YES" -ne 1 ]; then
    warn "This will delete ALL application data:"
    echo "  - PostgreSQL database (all users, records, settings)"
    echo "  - uploaded files"
    echo ""
    echo "The .env file and the application code will NOT be touched."
    echo ""
    if [ ! -t 0 ]; then
        err "Not a terminal and -y|--yes was not passed. Aborting."
        exit 1
    fi
    read -r -p "Continue? [y/N] " answer || answer=""
    case "$answer" in
        y|Y|yes|Yes|YES) ;;
        *) echo "Aborted."; exit 0 ;;
    esac
fi

# --- Reset -----------------------------------------------------------------
cd "$PROJECT_ROOT"
echo "Removing containers and volumes..."
if ! docker compose down -v; then
    err "docker compose down -v failed."
    exit 1
fi
info "All data reset."
info "Run scripts/run.sh to start with a clean database."
