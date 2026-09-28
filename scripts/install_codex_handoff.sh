#!/usr/bin/env bash
set -euo pipefail
if [ "$#" -lt 1 ]; then
  echo "Usage: bash scripts/install_codex_handoff.sh /path/to/htt_base" >&2
  exit 2
fi
REPO="$1"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ "${2:-}" = "--activate" ]; then
  if [ "$(cd "$REPO" && pwd -P)" != "$(cd "$PKG" && pwd -P)" ]; then
    echo "--activate requires the existing repository root" >&2
    exit 2
  fi
  python3 -B "$PKG/scripts/codex_harness/project_runtime.py" activate --repo-root "$REPO"
  exit $?
fi
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
for relative in docs/harness/CURRENT_CODEX_RUNTIME.md docs/harness/LEGACY_SHARED_CONTEXT_V1.md scripts/install_codex_handoff.sh; do
  assert_merge_safe_file "$PKG/$relative" "$REPO/$relative" "$relative"
done

mkdir -p "$REPO/.agents" "$REPO/.codex" "$REPO/docs/codex_handoff" "$REPO/machine_readable" "$REPO/scripts/codex_harness" "$REPO/docs/harness" "$REPO/harness_templates/vendor/physmath-gpt56"
copy_merge_only_file "$PKG/AGENTS.md" "$REPO/AGENTS.md"
copy_merge_only_file "$PKG/AGENTS.md.fragment" "$REPO/AGENTS.md.fragment"
cp -R "$PKG/.agents/"* "$REPO/.agents/"
copy_merge_only_tree "$PKG/.codex" "$REPO/.codex"
mkdir -p "$REPO/.agent-harness/scripts"
cp "$PKG/.agent-harness/README.md" "$REPO/.agent-harness/README.md"
cp -R "$PKG/.agent-harness/context" "$REPO/.agent-harness/"
cp -R "$PKG/.agent-harness/templates" "$REPO/.agent-harness/"
cp "$PKG/.agent-harness/scripts/"*.py "$REPO/.agent-harness/scripts/"
# The claim registry references these exact specifications. Distributing the
# registry without its referenced inputs made clean installs unverifiable.
python3 - "$PKG" "$REPO" <<'PY'
import json
from pathlib import Path
import shutil
import sys
source, target = map(Path, sys.argv[1:])
refs = set()
for line in (source / '.agent-harness/context/CLAIM_REGISTRY.jsonl').read_text().splitlines():
    if line.strip():
        refs.update(ref.split('#', 1)[0] for ref in json.loads(line).get('spec_refs', []))
for ref in sorted(refs):
    src = source / ref
    if not src.resolve().is_relative_to(source.resolve()) or not src.is_file():
        raise SystemExit(f'Invalid specification reference: {ref}')
    dst = target / ref
    if dst.exists() and dst.read_bytes() != src.read_bytes():
        raise SystemExit(f'Refusing divergent specification: {ref}')
for ref in sorted(refs):
    dst = target / ref
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        shutil.copyfile(source / ref, dst)
PY
mkdir -p "$REPO/harness_templates/legacy_hooks"
cp "$PKG/harness_templates/legacy_hooks/"*.py "$PKG/harness_templates/legacy_hooks/README.md" "$REPO/harness_templates/legacy_hooks/"
cp -R "$PKG/docs/codex_handoff/"* "$REPO/docs/codex_handoff/"
# docs/codex_handoff is canonical. machine_readable is a synchronized
# compatibility mirror and must never overwrite the canonical install source.
cp -R "$PKG/scripts/codex_harness/"* "$REPO/scripts/codex_harness/"
python "$REPO/scripts/codex_harness/sync_pr_dag_mirrors.py" --write
cp -R "$PKG/harness_templates/docs/harness/"* "$REPO/docs/harness/"
for relative in docs/harness/CURRENT_CODEX_RUNTIME.md docs/harness/LEGACY_SHARED_CONTEXT_V1.md scripts/install_codex_handoff.sh; do
  copy_merge_only_file "$PKG/$relative" "$REPO/$relative"
done
if [ ! -e "$VENDOR_DST" ]; then
  cp -R "$VENDOR_SRC" "$VENDOR_DST"
fi
chmod +x "$REPO/scripts/codex_harness/"*.py || true
python "$REPO/scripts/codex_harness/verify_skill_layout.py" "$REPO"
(
  cd "$REPO"
  python3 .agent-harness/scripts/build_context_pack.py
  python3 .agent-harness/scripts/build_context_pack.py --current
  python3 .agent-harness/scripts/validate_harness.py
)
python "$REPO/scripts/codex_harness/validate_pr_dag.py" "$REPO/docs/codex_handoff/pr_backlog.yaml"
python "$REPO/harness_templates/vendor/physmath-gpt56/3.1.0/coding/tools/validate_harness.py"
python "$REPO/harness_templates/vendor/physmath-gpt56/3.1.0/research/tools/validate_workspace.py"
echo "Installed v5 Codex handoff skillset into $REPO"
echo "Current v5 project runtime: scripts/codex_harness/project_runtime.py check"
