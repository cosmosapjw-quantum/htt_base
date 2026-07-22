#!/usr/bin/env bash
set -euo pipefail
if [ "$#" -lt 1 ]; then
  echo "Usage: bash scripts/install_codex_handoff.sh /path/to/htt_base" >&2
  exit 2
fi
REPO="$1"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENDOR_SRC="$PKG/harness_templates/vendor/physmath-gpt56/3.1.0"
VENDOR_DST="$REPO/harness_templates/vendor/physmath-gpt56/3.1.0"

assert_merge_safe_file() {
  local source="$1"
  local destination="$2"
  local label="$3"
  if [ -L "$destination" ]; then
    echo "Refusing to replace a symlinked merge-only asset ($label): $destination" >&2
    exit 1
  fi
  if [ -e "$destination" ] && { [ ! -f "$destination" ] || ! cmp -s "$source" "$destination"; }; then
    echo "Refusing to overwrite a divergent merge-only asset ($label): $destination" >&2
    exit 1
  fi
}

copy_merge_only_file() {
  local source="$1"
  local destination="$2"
  if [ ! -e "$destination" ]; then
    mkdir -p "$(dirname "$destination")"
    cp "$source" "$destination"
  fi
}

assert_merge_safe_tree() {
  local source_root="$1"
  local destination_root="$2"
  local label="$3"
  if find "$source_root" -type l -print -quit | grep -q .; then
    echo "Refusing a merge-only source tree containing symlinks ($label): $source_root" >&2
    exit 1
  fi
  while IFS= read -r -d '' source; do
    local relative="${source#"$source_root"/}"
    assert_merge_safe_file "$source" "$destination_root/$relative" "$label/$relative"
  done < <(find "$source_root" -type f -print0)
}

copy_merge_only_tree() {
  local source_root="$1"
  local destination_root="$2"
  while IFS= read -r -d '' source; do
    local relative="${source#"$source_root"/}"
    copy_merge_only_file "$source" "$destination_root/$relative"
  done < <(find "$source_root" -type f -print0)
}

if [ -e "$VENDOR_DST" ] && ! diff -qr "$VENDOR_SRC" "$VENDOR_DST" >/dev/null; then
  echo "Refusing to overwrite a divergent physmath vendor snapshot: $VENDOR_DST" >&2
  exit 1
fi
for active_pointer in \
  "$REPO/.agent-harness/runtime/ACTIVE_RUN" \
  "$REPO/.agent-harness/ACTIVE_RUN"
do
  if [ -e "$active_pointer" ]; then
    echo "Refusing to replace shared context while an agent-harness run is active: $active_pointer" >&2
    exit 1
  fi
done

# Merge-only assets are preflighted before the first destination write.  An
# existing repository policy or intentional Codex setting must be merged by a
# human; the installer never guesses which side owns a conflicting value.
assert_merge_safe_file "$PKG/AGENTS.md" "$REPO/AGENTS.md" "AGENTS.md"
assert_merge_safe_file "$PKG/AGENTS.md.fragment" "$REPO/AGENTS.md.fragment" "AGENTS.md.fragment"
assert_merge_safe_tree "$PKG/.codex" "$REPO/.codex" ".codex"

mkdir -p "$REPO/.agents" "$REPO/.codex" "$REPO/docs/codex_handoff" "$REPO/scripts/codex_harness" "$REPO/docs/harness" "$REPO/harness_templates/vendor/physmath-gpt56"
copy_merge_only_file "$PKG/AGENTS.md" "$REPO/AGENTS.md"
copy_merge_only_file "$PKG/AGENTS.md.fragment" "$REPO/AGENTS.md.fragment"
cp -R "$PKG/.agents/"* "$REPO/.agents/"
copy_merge_only_tree "$PKG/.codex" "$REPO/.codex"
mkdir -p "$REPO/.agent-harness/scripts"
cp "$PKG/.agent-harness/README.md" "$REPO/.agent-harness/README.md"
cp -R "$PKG/.agent-harness/context" "$REPO/.agent-harness/"
cp -R "$PKG/.agent-harness/templates" "$REPO/.agent-harness/"
cp "$PKG/.agent-harness/scripts/"*.py "$REPO/.agent-harness/scripts/"
cp -R "$PKG/docs/codex_handoff/"* "$REPO/docs/codex_handoff/"
cp -R "$PKG/machine_readable/"* "$REPO/docs/codex_handoff/"
cp -R "$PKG/scripts/codex_harness/"* "$REPO/scripts/codex_harness/"
cp -R "$PKG/harness_templates/docs/harness/"* "$REPO/docs/harness/"
if [ ! -e "$VENDOR_DST" ]; then
  cp -R "$VENDOR_SRC" "$VENDOR_DST"
fi
chmod +x "$REPO/scripts/codex_harness/"*.py || true
python "$REPO/scripts/codex_harness/verify_skill_layout.py" "$REPO"
(
  cd "$REPO"
  python3 .agent-harness/scripts/build_context_pack.py
  python3 .agent-harness/scripts/validate_harness.py
)
python "$REPO/scripts/codex_harness/validate_pr_dag.py" "$REPO/docs/codex_handoff/pr_backlog.yaml"
python "$REPO/harness_templates/vendor/physmath-gpt56/3.1.0/coding/tools/validate_harness.py"
python "$REPO/harness_templates/vendor/physmath-gpt56/3.1.0/research/tools/validate_workspace.py"
echo "Installed v4 Codex handoff skillset into $REPO"
