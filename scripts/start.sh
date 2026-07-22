#!/usr/bin/env sh
set -eu
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
if [ -d "$SCRIPT_DIR/app" ]; then
  ROOT="$SCRIPT_DIR"
else
  ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"
fi
export SOCRATLEGAL_ENV_FILE="$ROOT/config/.env"
exec "$ROOT/runtime/uv" run --directory "$ROOT/app" socratlegal-mcp "$@"
