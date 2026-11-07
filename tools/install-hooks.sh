#!/bin/sh
# tools/install-hooks.sh -- point this clone at .githooks, idempotently.
#
# Run it once per clone, from anywhere:
#
#     tools/install-hooks.sh
#
# What it does: `git config --local core.hooksPath .githooks` in the clone that holds
# this script. That is a per-clone setting, stored in .git/config, not committed and not
# pushed -- so every fresh clone needs this run once, and nobody else's clone is touched.
#
# Idempotent by construction: if core.hooksPath is already `.githooks` it says so and
# exits 0 without writing anything. Run it as often as you like.
#
# It does not install into ~/.git-hooks, does not edit the global config, and does not
# touch any repository other than the one it sits in.
set -eu

script_dir=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$script_dir/.." && pwd)

if ! git -C "$root" rev-parse --git-dir >/dev/null 2>&1; then
    echo "install-hooks: $root is not a git repository" >&2
    exit 1
fi

if [ ! -f "$root/.githooks/pre-commit" ]; then
    echo "install-hooks: $root/.githooks/pre-commit is missing; nothing to install" >&2
    exit 1
fi

current=$(git -C "$root" config --local --get core.hooksPath 2>/dev/null || true)

if [ "$current" = ".githooks" ]; then
    echo "install-hooks: core.hooksPath is already .githooks in $root (nothing to do)"
    exit 0
fi

git -C "$root" config --local core.hooksPath .githooks
echo "install-hooks: core.hooksPath = .githooks in $root (was ${current:-unset})"
echo "install-hooks: commits in this clone now run .githooks/pre-commit"
