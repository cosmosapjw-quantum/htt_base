#!/usr/bin/env bash
set -euo pipefail

BASE_SHA=ccba350d7b725b227c64436e32af96abfe786449
ARCHIVE_SHA=e5cddee566a5ee30bcc2c3b0a98167c289878622586ec0e55ef1426fe035a4a2
HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(git rev-parse --show-toplevel)

if ! git merge-base --is-ancestor "$BASE_SHA" HEAD; then
  echo "BLOCKED_BY_MOVED_AUTHORITY: accepted PMG-WU-007 head is not an ancestor" >&2
  exit 2
fi
if [[ -n $(git status --porcelain=v1) ]]; then
  echo "BLOCKED_BY_DIRTY_WORKTREE: use a separate clean worktree" >&2
  exit 3
fi

parts=("$HERE"/archive.b64.part-*)
if [[ ${#parts[@]} -ne 3 ]]; then
  echo "BLOCKED_BY_INCOMPLETE_OVERLAY_ARCHIVE: expected 3 parts" >&2
  exit 4
fi

tmp=$(mktemp -d "${TMPDIR:-/tmp}/wu008-overlay.XXXXXX")
trap 'rm -rf "$tmp"' EXIT
cat "${parts[@]}" | base64 --decode > "$tmp/archive.zip"
echo "$ARCHIVE_SHA  $tmp/archive.zip" | sha256sum -c -
unzip -q "$tmp/archive.zip" -d "$tmp/unpacked"
(
  cd "$tmp/unpacked"
  sha256sum -c MANIFEST.sha256
)

while IFS= read -r -d '' source; do
  rel=${source#"$tmp/unpacked/payload/"}
  target="$REPO/$rel"
  if [[ -e "$target" || -L "$target" ]]; then
    if cmp -s "$source" "$target"; then
      continue
    fi
    echo "BLOCKED_BY_TARGET_COLLISION: $rel" >&2
    exit 5
  fi
  mkdir -p "$(dirname "$target")"
  cp "$source" "$target"
done < <(find "$tmp/unpacked/payload" -type f -print0 | sort -z)

echo "OVERLAY_APPLIED"
echo "Next: run the validator and focused tests from CODEX_HANDOFF_PROMPT.md."
