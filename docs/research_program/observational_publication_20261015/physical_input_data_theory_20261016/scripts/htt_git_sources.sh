#!/usr/bin/env bash
# Fetch public source codes reproducibly; store exact HEAD and clean-state receipts.
set -euo pipefail
ROOT="${1:-/mnt/extdrive/workdir/htt_open_data}"
mkdir -p "$ROOT/git" "$ROOT/provenance"
for spec in \
  'aniclass|https://github.com/CyrilPitrou/aniclass.git' \
  'PantheonPlus_DataRelease|https://github.com/PantheonPlusSH0ES/DataRelease.git' \
  'bulkflow_estimators|https://github.com/abbew25/Measuring_bulkflows.git'; do
  name="${spec%%|*}"; url="${spec#*|}"; dest="$ROOT/git/$name"
  if [[ -e "$dest" && ! -d "$dest/.git" ]]; then echo "Refusing non-git existing path $dest" >&2; exit 4; fi
  if [[ ! -e "$dest" ]]; then git clone --depth 1 "$url" "$dest"; else
    echo "Existing checkout $dest: preserving pinned state; no git pull";
  fi
  sha="$(git -C "$dest" rev-parse HEAD)"
  dirty="$(git -C "$dest" status --porcelain)"
  [[ -z "$dirty" ]] || { echo "Dirty source tree $dest" >&2; exit 5; }
  printf 'repo=%s\nurl=%s\nhead=%s\n' "$name" "$url" "$sha" > "$ROOT/provenance/${name}_git_receipt.txt"
  echo "SOURCE $name HEAD=$sha"
done
