#!/usr/bin/env bash
# Creates .env from .env.example with a generated DJANGO_SECRET_KEY.
# Does nothing if .env already exists. Writes UTF-8 without BOM.
# Requires: python3 or python or openssl for key generation.
set -euo pipefail

# --- Colors (disabled when stdout is not a tty) ----------------------------
if [ -t 1 ]; then
    RED=$'\033[0;31m'; GREEN=$'\033[0;32m'; YELLOW=$'\033[1;33m'; NC=$'\033[0m'
else
    RED=''; GREEN=''; YELLOW=''; NC=''
fi

err()  { printf '%sERROR:%s %s\n' "$RED" "$NC" "$*" >&2; }
info() { printf '%sOK:%s %s\n' "$GREEN" "$NC" "$*"; }
warn() { printf '%sWARNING:%s %s\n' "$YELLOW" "$NC" "$*" >&2; }

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

ENV_FILE="$PROJECT_ROOT/.env"
EXAMPLE_FILE="$PROJECT_ROOT/.env.example"

if [ ! -f "$EXAMPLE_FILE" ]; then
    err ".env.example not found at $EXAMPLE_FILE"
    exit 1
fi

if [ -f "$ENV_FILE" ]; then
    info ".env already exists at $ENV_FILE"
    warn "Nothing to do. Delete it manually if you want to regenerate"
    warn "(this will invalidate all sessions and reset cookies)."
    exit 0
fi

# --- Generate a cryptographically strong key -------------------------------
# base64url alphabet (A-Za-z0-9-_), no + / = so it never needs quoting.
gen_key() {
    if command -v python3 >/dev/null 2>&1; then
        python3 -c "import secrets; print(secrets.token_urlsafe(48))"
    elif command -v python >/dev/null 2>&1; then
        python -c "import secrets; print(secrets.token_urlsafe(48))"
    elif command -v openssl >/dev/null 2>&1; then
        openssl rand -base64 48 | tr '+/' '-_' | tr -d '=\n'
    else
        return 1
    fi
}

if ! KEY="$(gen_key)" || [ -z "$KEY" ]; then
    err "Could not generate a key. Need python3, python, or openssl in PATH."
    exit 1
fi

# --- Write .env from .env.example ------------------------------------------
TMP_FILE="$(mktemp)"
trap 'rm -f "$TMP_FILE"' EXIT

awk -v key="$KEY" '
    /^[[:space:]]*DJANGO_SECRET_KEY[[:space:]]*=/ && !done {
        print "DJANGO_SECRET_KEY=" key
        done=1
        next
    }
    { print }
    END {
        if (!done) {
            print "DJANGO_SECRET_KEY=" key
            print "" > "/dev/stderr"
        }
    }
' "$EXAMPLE_FILE" > "$TMP_FILE"

if ! grep -qE '^[[:space:]]*DJANGO_SECRET_KEY[[:space:]]*=' "$EXAMPLE_FILE"; then
    warn "DJANGO_SECRET_KEY line not found in .env.example, appended at the end."
fi

mv "$TMP_FILE" "$ENV_FILE"

info "Created $ENV_FILE"
info "DJANGO_SECRET_KEY generated (48 bytes, base64url)."
warn "It is stored in .env; keep that file private and do not commit it."
