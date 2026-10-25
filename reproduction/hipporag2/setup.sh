#!/usr/bin/env bash
# Clone the official HippoRAG2 repo at the commit used in the paper.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO=https://github.com/OSU-NLP-Group/HippoRAG
COMMIT=1438aba3fc44ff10573e5a5e1e7cc3c7f9794aff
DST="$HERE/upstream"

if [ ! -d "$DST/.git" ]; then
  git clone "$REPO" "$DST"
fi
git -C "$DST" fetch --quiet origin
git -C "$DST" checkout --quiet "$COMMIT"
# no patches: the official repo is used as-is

# TODO: environment / dependency installation
echo "HippoRAG2 ready at $DST ($COMMIT)"
