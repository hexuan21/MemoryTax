#!/usr/bin/env bash
# Clone the official Mem-T repo at the commit used in the paper.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO=https://github.com/yanweiyue/Mem-T
COMMIT=8c2272028f74c2b841aa0fbdf0d324c9d01f6914
DST="$HERE/upstream"

if [ ! -d "$DST/.git" ]; then
  git clone "$REPO" "$DST"
fi
git -C "$DST" fetch --quiet origin
git -C "$DST" checkout --quiet "$COMMIT"
# no patches: the official repo is used as-is

# TODO: environment / dependency installation
echo "Mem-T ready at $DST ($COMMIT)"
