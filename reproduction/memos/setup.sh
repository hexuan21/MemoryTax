#!/usr/bin/env bash
# Clone the official MemOS repo at the commit used in the paper.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO=https://github.com/MemTensor/MemOS
COMMIT=f4db521214c29337164ec788bafede7eab236c25
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
echo "MemOS ready at $DST ($COMMIT)"
