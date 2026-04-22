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
exec python3 -c '
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

port = int(sys.argv[1])
ThreadingHTTPServer(("127.0.0.1", port), NoCacheHandler).serve_forever()
' "$PORT"
