#!/usr/bin/env bash
# Clone the official SimpleMem repo at the commit used in the paper.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO=https://github.com/aiming-lab/SimpleMem
COMMIT=db80b6a7c591e0ea730a058e9f5fc4eb06572299
DST="$HERE/upstream"

if [ ! -d "$DST/.git" ]; then
  git clone "$REPO" "$DST"
fi
git -C "$DST" fetch --quiet origin
git -C "$DST" checkout --quiet "$COMMIT"
# no patches: the official repo is used as-is

# TODO: environment / dependency installation
echo "SimpleMem ready at $DST ($COMMIT)"
