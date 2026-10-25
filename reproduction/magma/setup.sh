#!/usr/bin/env bash
# Clone the official MAGMA repo at the commit used in the paper.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO=https://github.com/FredJiang0324/MAGMA
COMMIT=467cb70b67ac337b22fdb42194d37c04ad701b62
DST="$HERE/upstream"

if [ ! -d "$DST/.git" ]; then
  git clone "$REPO" "$DST"
fi
git -C "$DST" fetch --quiet origin
git -C "$DST" checkout --quiet "$COMMIT"
# no patches: the official repo is used as-is

# TODO: environment / dependency installation
echo "MAGMA ready at $DST ($COMMIT)"
