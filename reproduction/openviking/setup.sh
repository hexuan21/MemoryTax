#!/usr/bin/env bash
# Clone the official OpenViking repo at the commit used in the paper.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO=https://github.com/volcengine/OpenViking
COMMIT=33043cb1b83d7a69069eea8ac0da3c952666a1e1
DST="$HERE/upstream"

if [ ! -d "$DST/.git" ]; then
  git clone "$REPO" "$DST"
fi
git -C "$DST" fetch --quiet origin
git -C "$DST" checkout --quiet "$COMMIT"
# no patches: the official repo is used as-is

# TODO: environment / dependency installation
echo "OpenViking ready at $DST ($COMMIT)"
