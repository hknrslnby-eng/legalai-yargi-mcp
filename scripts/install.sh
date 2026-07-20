#!/usr/bin/env sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
exec "$ROOT/runtime/uv" run --directory "$ROOT/app" socratlegal install \
  --install-dir "$ROOT/app" --portable-root "$ROOT" --ide all "$@"
