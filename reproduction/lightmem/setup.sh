#!/usr/bin/env bash
# Clone the official LightMem repo at the commit used in the paper.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO=https://github.com/zjunlp/LightMem
COMMIT=8fc9a9179f9170c4a40fc653fcb410375900f26e
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
echo "LightMem ready at $DST ($COMMIT)"
