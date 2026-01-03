#!/usr/bin/env bash
set -euo pipefail

DEFAULT="postgresql+asyncpg://postgres:password@localhost:5432/fortunes"
URL="${DATABASE_URL:-$DEFAULT}"

# require pg_dump
command -v pg_dump >/dev/null 2>&1 || { echo "pg_dump not found. Install postgresql client."; exit 1; }

# Parse and normalize URL using Python (handles percent-encoding, asyncpg scheme, postgres://)
mapfile -t _parts < <(python3 - <<'PY'
import os
from urllib.parse import urlparse, unquote

raw = os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost:5432/fortunes")
if raw.startswith("postgres://"):
    raw = raw.replace("postgres://", "postgresql://", 1)
raw = raw.replace("+asyncpg", "")
p = urlparse(raw)
user = p.username or ""
pw = p.password or ""
host = p.hostname or "localhost"
port = str(p.port) if p.port else ""
dbname = p.path.lstrip("/")
# build connection string without password
conn = "postgresql://"
if user:
    conn += f"{user}@"
conn += host
if port:
    conn += f":{port}"
if dbname:
    conn += f"/{dbname}"
print(pw)
print(conn)
PY
)

PGPASS="${_parts[0]:-}"
CONN="${_parts[1]:-}"

# Backup destination
OUT_DIR="${1:-backups}"
mkdir -p "$OUT_DIR"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT_FILE="${OUT_DIR}/fortunes-${TIMESTAMP}.dump"

# Run pg_dump (custom format). Use PGPASSWORD only for the subprocess to avoid leaking.
if [ -n "$PGPASS" ]; then
  PGPASSWORD="$PGPASS" pg_dump -d "$CONN" -F c -f "$OUT_FILE" --no-owner --no-privileges
else
  pg_dump -d "$CONN" -F c -f "$OUT_FILE" --no-owner --no-privileges
fi

echo "Backup saved to: $OUT_FILE"
