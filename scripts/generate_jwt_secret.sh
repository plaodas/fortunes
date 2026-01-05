#!/usr/bin/env sh
set -eu

usage() {
  cat <<-USAGE
Usage: $0 [--bytes N] [--env PATH] [--apply]

Options:
  --bytes N    Number of random bytes (default: 32)
  --env PATH   Path to .env file (default: .env)
  --apply      Update the .env file (backs up to .env.bak)
  -h, --help   Show this help
USAGE
}

BYTES=32
ENV_PATH=.env
APPLY=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --bytes) BYTES="$2"; shift 2 ;;
    --env) ENV_PATH="$2"; shift 2 ;;
    --apply) APPLY=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

generate_secret() {
  if command -v openssl >/dev/null 2>&1; then
    # openssl rand -base64 N -> may include +/ and =, convert to URL-safe and strip padding
    openssl rand -base64 "$BYTES" 2>/dev/null | tr '+/' '-_' | tr -d '=' | tr -d '\n'
  else
    # Fallback to Python's secrets
    python - <<PY
import secrets
print(secrets.token_urlsafe($BYTES))
PY
  fi
}

SECRET=$(generate_secret)
# Print dotenv line
printf "JWT_SECRET='%s'\n" "$SECRET"

if [ "$APPLY" -eq 1 ]; then
  if [ -f "$ENV_PATH" ]; then
    cp "$ENV_PATH" "$ENV_PATH.bak"
    # Replace an existing JWT_SECRET line or append if missing
    awk -v s="JWT_SECRET='$SECRET'" '
      BEGIN{r=0}
      /^JWT_SECRET=/ {print s; r=1; next}
      {print}
      END{if(r==0) print s}
    ' "$ENV_PATH.bak" > "$ENV_PATH"
    printf "Updated %s (backup at %s.bak)\n" "$ENV_PATH" "$ENV_PATH"
  else
    printf "JWT_SECRET='%s'\n" "$SECRET" > "$ENV_PATH"
    printf "Created %s\n" "$ENV_PATH"
  fi
fi
