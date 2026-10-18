#!/usr/bin/env bash
# Starts the application stack and prints the URL.
# Checks Docker, calls init-env.sh if .env is missing, validates the secret
# key, runs docker compose up -d, waits for the superuser created by
# entrypoint, optionally seeds demo data, prints the URL, opens the browser.
set -euo pipefail

if [ -t 1 ]; then
    RED=$'\033[0;31m'; GREEN=$'\033[0;32m'; YELLOW=$'\033[1;33m'; NC=$'\033[0m'
else
    RED=''; GREEN=''; YELLOW=''; NC=''
fi

err()  { printf '%sERROR:%s %s\n' "$RED" "$NC" "$*" >&2; }
info() { printf '%sOK:%s %s\n' "$GREEN" "$NC" "$*"; }
warn() { printf '%sWARNING:%s %s\n' "$YELLOW" "$NC" "$*" >&2; }

SEED=0
NO_SEED=0
NO_BROWSER=0
NON_INTERACTIVE=0
REBUILD=0

usage() {
    cat <<EOF
Usage: $(basename "$0") [options]

Starts the application stack.

  -s, --seed               Load demo data (skip the prompt)
      --no-seed            Do not load demo data (skip the prompt)
      --no-browser         Do not open the browser automatically
      --non-interactive    No prompts; implies --seed and --no-browser
  -r, --rebuild            Pass --build to docker compose up
  -h, --help               Show this help
EOF
}

while [ $# -gt 0 ]; do
    case "$1" in
        -s|--seed) SEED=1 ;;
        --no-seed) NO_SEED=1 ;;
        --no-browser) NO_BROWSER=1 ;;
        --non-interactive) NON_INTERACTIVE=1 ;;
        -r|--rebuild) REBUILD=1 ;;
        -h|--help) usage; exit 0 ;;
        *) err "Unknown option: $1"; usage >&2; exit 1 ;;
    esac
    shift
done

# Non-interactive when stdin is not a tty, unless the user passed flags.
if [ ! -t 0 ]; then
    NON_INTERACTIVE=1
fi

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

# --- Ensure .env exists ----------------------------------------------------
ENV_FILE="$PROJECT_ROOT/.env"
if [ ! -f "$ENV_FILE" ]; then
    warn "No .env found, generating one..."
    if ! "$SCRIPT_DIR/init-env.sh"; then
        err "Failed to create .env."
        exit 1
    fi
fi

# --- Validate .env ---------------------------------------------------------
if grep -qE '^[[:space:]]*DJANGO_SECRET_KEY[[:space:]]*=[[:space:]]*your-secret' "$ENV_FILE"; then
    err "DJANGO_SECRET_KEY still has the placeholder value in .env."
    err "Delete .env and run this script again to regenerate it."
    exit 1
fi
if ! grep -qE '^[[:space:]]*DJANGO_SECRET_KEY[[:space:]]*=[[:space:]]*[^[:space:]]' "$ENV_FILE"; then
    err "DJANGO_SECRET_KEY is missing or empty in .env."
    err "Delete .env and run this script again to regenerate it."
    exit 1
fi

# --- Read NGINX_PORT -------------------------------------------------------
NGINX_PORT="$(awk -F= '/^[[:space:]]*NGINX_PORT[[:space:]]*=/{gsub(/[[:space:]]/,"",$2); port=$2} END{print port}' "$ENV_FILE")"
[ -z "${NGINX_PORT:-}" ] && NGINX_PORT="80"

# --- Decide whether to seed ------------------------------------------------
DO_SEED=0
if [ "$NO_SEED" -eq 1 ]; then
    DO_SEED=0
elif [ "$SEED" -eq 1 ]; then
    DO_SEED=1
elif [ "$NON_INTERACTIVE" -eq 1 ]; then
    DO_SEED=1
else
    read -r -p "Load demo data? [Y/n] " answer || answer=""
    case "$answer" in
        ""|y|Y|yes|Yes|YES) DO_SEED=1 ;;
        *) DO_SEED=0 ;;
    esac
fi

# --- Start stack -----------------------------------------------------------
cd "$PROJECT_ROOT"

up_args=(compose up -d)
[ "$REBUILD" -eq 1 ] && up_args+=(--build)

echo "Starting containers..."
if ! docker "${up_args[@]}"; then
    err "docker compose up failed."
    err "Run 'docker compose logs' to see details."
    exit 1
fi

# --- Wait for containers to be running -------------------------------------
echo "Waiting for containers to start..."
running=0
for ((i=0; i<30; i++)); do
    sleep 1
    states="$(docker compose ps --format '{{.State}}' 2>/dev/null || true)"
    if [ -n "$states" ] && [ -z "$(echo "$states" | grep -v '^running$' || true)" ]; then
        running=1
        break
    fi
done
if [ "$running" -ne 1 ]; then
    warn "Containers did not reach running state within 30 seconds."
    warn "Run 'docker compose logs' to see what is wrong."
fi

# --- Wait for the superuser created by entrypoint --------------------------
# entrypoint.sh runs migrations and creates the superuser before exec'ing
# the server, but "running" is reported as soon as the process starts.
# Poll for the superuser before seeding to avoid
# "Superuser 'admin' not found".
if [ "$DO_SEED" -eq 1 ] && [ "$running" -eq 1 ]; then
    echo "Waiting for the superuser to be created..."
    probe='from django.contrib.auth import get_user_model; import sys; sys.exit(0 if get_user_model().objects.filter(is_superuser=True).exists() else 1)'
    superuser_ready=0
    for ((i=0; i<180; i++)); do
        sleep 1
        if docker compose exec -T web python src/manage.py shell -c "$probe" >/dev/null 2>&1; then
            superuser_ready=1
            break
        fi
    done
    if [ "$superuser_ready" -ne 1 ]; then
        warn "No superuser found after 180 seconds. Skipping demo data."
        warn "The app is running; you can seed later with:"
        warn "  docker compose exec web python src/manage.py seed_demo"
        DO_SEED=0
    fi
fi

# --- Seed demo data --------------------------------------------------------
if [ "$DO_SEED" -eq 1 ]; then
    echo "Loading demo data..."
    if docker compose exec -T web python src/manage.py seed_demo; then
        info "Demo data loaded."
    else
        warn "seed_demo failed. The app is still running."
        warn "Retry manually with:"
        warn "  docker compose exec web python src/manage.py seed_demo"
    fi
fi

# --- Wait for the app to respond through nginx -----------------------------
# entrypoint.sh creates the superuser before exec'ing gunicorn, so a
# request in that window gets 502 from nginx. Poll for a status below
# 500 so the URL is printed and the browser is opened only when the app
# actually answers. 127.0.0.1 instead of localhost: on some systems
# localhost resolves to ::1 first, and nginx may listen on IPv4 only.
if command -v curl >/dev/null 2>&1; then
    echo "Waiting for the application to respond..."
    app_ready=0
    for ((i=0; i<60; i++)); do
        code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 3 \
            "http://127.0.0.1:${NGINX_PORT}/" 2>/dev/null || echo 000)"
        if [ "$code" -ge 200 ] && [ "$code" -lt 500 ]; then
            app_ready=1
            break
        fi
        sleep 1
    done
    if [ "$app_ready" -ne 1 ]; then
        warn "The application did not respond within 60 seconds."
        warn "Containers are running; open http://localhost:${NGINX_PORT}/ manually and check logs."
    fi
else
    warn "curl not found; skipping HTTP readiness check."
fi

# --- Print URL and next steps ----------------------------------------------
echo ""
printf '%s============================================%s\n' "$GREEN" "$NC"
printf '%s  Application is running%s\n' "$GREEN" "$NC"
printf '%s  Open: http://localhost:%s/%s\n' "$GREEN" "$NGINX_PORT" "$NC"
printf '%s============================================%s\n' "$GREEN" "$NC"
echo ""
echo "  Stop:    docker compose down"
echo "  Reset:   scripts/reset.sh"
echo "  Logs:    docker compose logs -f"
echo ""

# --- Open browser ----------------------------------------------------------
if [ "$NO_BROWSER" -ne 1 ] && [ "$NON_INTERACTIVE" -ne 1 ]; then
    url="http://localhost:${NGINX_PORT}/"
    if command -v xdg-open >/dev/null 2>&1; then
        xdg-open "$url" >/dev/null 2>&1 &
    elif command -v open >/dev/null 2>&1; then
        open "$url" >/dev/null 2>&1 &
    elif command -v python3 >/dev/null 2>&1; then
        python3 -m webbrowser -t "$url" >/dev/null 2>&1 &
    else
        warn "Could not detect a browser opener; open $url manually."
    fi
fi
