#!/usr/bin/env bash
# Start a local web server to preview the generated site.
# Usage: bash scripts/serve.sh [port]
#   port  optional, default 8000
set -e

PORT="${1:-8000}"
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SITE_DIR="$REPO_DIR/site"

if [ ! -d "$SITE_DIR" ]; then
  echo "✗ site directory not found: $SITE_DIR" >&2
  exit 1
fi

URL="http://localhost:$PORT/"
echo "→ serving $SITE_DIR on $URL (Ctrl-C to stop)"

if command -v open >/dev/null 2>&1; then
  ( sleep 0.8 && open "$URL" ) &
fi

cd "$SITE_DIR"
exec python3 -m http.server "$PORT" --bind 127.0.0.1
