#!/usr/bin/env bash
# Clone the official A-Mem repo at the commit used in the paper.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO=https://github.com/agiresearch/a-mem
COMMIT=ceffb860f0712bbae97b184d440df62bc910ca8d
DST="$HERE/upstream"

if [ ! -d "$DST/.git" ]; then
  git clone "$REPO" "$DST"
fi
git -C "$DST" fetch --quiet origin
git -C "$DST" checkout --quiet "$COMMIT"
# no patches: the official repo is used as-is

# TODO: environment / dependency installation
echo "A-Mem ready at $DST ($COMMIT)"
