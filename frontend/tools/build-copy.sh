#!/usr/bin/env bash
# Build and preview OUTSIDE the working tree.
#
# If another session is already serving this checkout's own `.next`, a `next
# build` run in place would replace the bundle that server is serving, which is
# a change to a live process nobody here owns. So every build and every
# screenshot run happens in a throwaway copy that shares the checkout's
# node_modules by symlink.
#
#   tools/build-copy.sh sync     mirror the source into the throwaway copy
#   tools/build-copy.sh build    sync, then production build
#   tools/build-copy.sh start    serve the built copy on $PORT (foreground)
#   tools/build-copy.sh dev      dev server on $PORT, for the live-data pass
#
# Env is passed through, so NEXT_PUBLIC_API_BASE_URL can be set per run.
# SEATPASS_SRC and SEATPASS_BUILD_DIR move the two ends. The defaults are this
# checkout and a directory under the system temp dir, never inside it.
set -euo pipefail

SRC="${SEATPASS_SRC:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
DST="${SEATPASS_BUILD_DIR:-${TMPDIR:-/tmp}/seatpass-build}"
PORT="${PORT:-3010}"

sync() {
  mkdir -p "$DST"
  rsync -a --delete \
    --exclude node_modules \
    --exclude .next \
    --exclude .git \
    --exclude '.env*' \
    "$SRC"/ "$DST"/
  ln -sfn "$SRC/node_modules" "$DST/node_modules"
  echo "synced $SRC -> $DST"
}

case "${1:-}" in
  sync) sync ;;
  build)
    sync
    cd "$DST"
    npx next build 2>&1 | tail -40
    ;;
  start)
    cd "$DST"
    npx next start -p "$PORT" -H 127.0.0.1
    ;;
  dev)
    sync
    cd "$DST"
    npx next dev -p "$PORT" -H 127.0.0.1
    ;;
  *)
    echo "usage: $0 {sync|build|start|dev}" >&2
    exit 2
    ;;
esac
