#!/usr/bin/env bash
# Clone the official MemoryOS repo at the commit used in the paper.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO=https://github.com/BAI-LAB/MemoryOS
COMMIT=587ed7755c7aed179965792830ff1b5ad9a6fa92
DST="$HERE/upstream"

if [ ! -d "$DST/.git" ]; then
  git clone "$REPO" "$DST"
fi
git -C "$DST" fetch --quiet origin
git -C "$DST" checkout --quiet "$COMMIT"
for p in "$HERE"/patches/*.patch; do
  [ -e "$p" ] || continue
  git -C "$DST" apply "$p"
done

# TODO: environment / dependency installation
echo "MemoryOS ready at $DST ($COMMIT)"
