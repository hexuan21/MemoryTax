#!/usr/bin/env bash
# Clone the official Memory-R2 repo at the commit used in the paper.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO=https://github.com/ahmedehabb/Memory-R2
COMMIT=352896d2260da4e14ae771541e630209486f6777
DST="$HERE/upstream"

if [ ! -d "$DST/.git" ]; then
  git clone "$REPO" "$DST"
fi
git -C "$DST" fetch --quiet origin
git -C "$DST" checkout --quiet "$COMMIT"
# no patches: the official repo is used as-is

# TODO: environment / dependency installation
echo "Memory-R2 ready at $DST ($COMMIT)"
