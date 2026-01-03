#!/usr/bin/env bash
set -euo pipefail

DEFAULT="postgresql+asyncpg://postgres:password@localhost:5432/fortunes"
URL="${RESTORE_DATABASE_URL:-${DATABASE_URL:-$DEFAULT}}"
DEBUG="${DEBUG:-}"

if [ -n "$DEBUG" ]; then set -x; fi

# Parse URL -> password and connection URI (without password)
mapfile -t _parts < <(python3 - <<'PY'
import os
from urllib.parse import urlparse
raw = os.environ.get("RESTORE_DATABASE_URL") or os.environ.get("DATABASE_URL") or "postgresql+asyncpg://postgres:password@localhost:5432/fortunes"
if raw.startswith("postgres://"):
    raw = raw.replace("postgres://", "postgresql://", 1)
raw = raw.replace("+asyncpg", "")
p = urlparse(raw)
user = p.username or ""
pw = p.password or ""
host = p.hostname or "localhost"
port = str(p.port) if p.port else ""
dbname = p.path.lstrip("/")
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

# Determine backup file: arg1 or latest in backups/
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<EOF
Usage: $0 [backup-file-or-path] [--yes]
If no backup-file is given, the latest backups/fortunes-*.dump is used.
Set RESTORE_DATABASE_URL to override DATABASE_URL.
Use --yes to skip confirmation.
EOF
  exit 0
fi

BACKUP_ARG="${1:-}"
SKIP_CONFIRM=false
if [ "${2:-}" = "--yes" ] || [ "${1:-}" = "--yes" ]; then
  SKIP_CONFIRM=true
fi

if [ -n "$BACKUP_ARG" ] && [ "$BACKUP_ARG" != "--yes" ]; then
  BACKUP_PATH="$BACKUP_ARG"
else
  # find latest file
  if compgen -G "backups/fortunes-*.dump" > /dev/null; then
    BACKUP_PATH=$(ls -1t backups/fortunes-*.dump | head -n1)
  else
    echo "No backup files found in backups/"
    exit 1
  fi
fi

if [ ! -f "$BACKUP_PATH" ]; then
  echo "Backup file not found: $BACKUP_PATH"
  exit 1
fi

echo "Restore target: $CONN"
echo "Backup file: $BACKUP_PATH"

if [ "$SKIP_CONFIRM" = false ]; then
  read -p "Proceed with restore? This will drop/create objects in the target DB (type 'yes' to confirm): " CONF
  if [ "$CONF" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
  fi
fi

# Run pg_restore. Use PGPASSWORD for subprocess only.
if [ -n "$PGPASS" ]; then
  env PGPASSWORD="$PGPASS" pg_restore -v -d "$CONN" --clean --no-owner --no-privileges "$BACKUP_PATH"
else
  pg_restore -v -d "$CONN" --clean --no-owner --no-privileges "$BACKUP_PATH"
fi

echo "Restore finished."
