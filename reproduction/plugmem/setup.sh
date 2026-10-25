#!/usr/bin/env bash
# Clone the official PlugMem repo at the commit used in the paper.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO=https://github.com/TIMAN-group/PlugMem
COMMIT=3b2ce75257d40bca8fac3f78e54e22ea41d92529
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
echo "PlugMem ready at $DST ($COMMIT)"
