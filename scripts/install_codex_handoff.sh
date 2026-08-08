#!/usr/bin/env bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
if [ "$#" -lt 1 ]; then
  echo "Usage: bash scripts/install_codex_handoff.sh /path/to/htt_base" >&2
  exit 2
fi
REPO="$1"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENDOR_SRC="$PKG/harness_templates/vendor/physmath-gpt56/3.1.0"
VENDOR_DST="$REPO/harness_templates/vendor/physmath-gpt56/3.1.0"

assert_safe_destination_directory() {
  local directory="$1"
  local label="$2"
  local probe
  probe="$directory"
  while [ "$probe" != "/" ] && [ "$probe" != "." ]; do
    if [ -L "$probe" ]; then
      echo "Refusing a symlinked installer destination ($label): $probe" >&2
      exit 1
    fi
    if [ -e "$probe" ] && [ ! -d "$probe" ]; then
      echo "Refusing a non-directory installer destination ($label): $probe" >&2
      exit 1
    fi
    local parent
    parent="$(dirname "$probe")"
    if [ "$parent" = "$probe" ]; then
      break
    fi
    probe="$parent"
  done
}

assert_safe_destination_file() {
  local destination="$1"
  local label="$2"
  if [ -L "$destination" ]; then
    echo "Refusing a symlinked installer destination ($label): $destination" >&2
    exit 1
  fi
  assert_safe_destination_directory "$(dirname "$destination")" "$label"
  if [ -e "$destination" ] && [ ! -f "$destination" ]; then
    echo "Refusing a non-regular installer destination ($label): $destination" >&2
    exit 1
  fi
  if [ -f "$destination" ]; then
    local link_count
    if ! link_count="$(stat -c '%h' -- "$destination")"; then
      echo "Refusing an unreadable installer destination ($label): $destination" >&2
      exit 1
    fi
    case "$link_count" in
      ''|*[!0-9]*)
        echo "Refusing an invalid installer destination link count ($label): $destination" >&2
        exit 1
        ;;
    esac
    if [ "$link_count" -ne 1 ]; then
      echo "Refusing a multiply-linked installer destination ($label): $destination" >&2
      exit 1
    fi
  fi
}

assert_merge_safe_file() {
  local source="$1"
  local destination="$2"
  local label="$3"
  assert_safe_destination_file "$destination" "$label"
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
  done < <(
    find "$source_root" -type f \
      ! -path '*/__pycache__/*' \
      ! -name '*.pyc' \
      ! -name '*.pyo' \
      -print0
  )
}

copy_merge_only_tree() {
  local source_root="$1"
  local destination_root="$2"
  while IFS= read -r -d '' source; do
    local relative="${source#"$source_root"/}"
    copy_merge_only_file "$source" "$destination_root/$relative"
  done < <(
    find "$source_root" -type f \
      ! -path '*/__pycache__/*' \
      ! -name '*.pyc' \
      ! -name '*.pyo' \
      -print0
  )
}

assert_replace_safe_tree() {
  local source_root="$1"
  local destination_root="$2"
  local label="$3"
  if find "$source_root" -type l -print -quit | grep -q .; then
    echo "Refusing an installer source tree containing symlinks ($label): $source_root" >&2
    exit 1
  fi
  while IFS= read -r -d '' source; do
    local relative="${source#"$source_root"/}"
    assert_safe_destination_file "$destination_root/$relative" "$label/$relative"
  done < <(
    find "$source_root" -type f \
      ! -path '*/__pycache__/*' \
      ! -name '*.pyc' \
      ! -name '*.pyo' \
      -print0
  )
}

copy_replace_tree() {
  local source_root="$1"
  local destination_root="$2"
  while IFS= read -r -d '' source; do
    local relative="${source#"$source_root"/}"
    mkdir -p "$(dirname "$destination_root/$relative")"
    cp "$source" "$destination_root/$relative"
  done < <(
    find "$source_root" -type f \
      ! -path '*/__pycache__/*' \
      ! -name '*.pyc' \
      ! -name '*.pyo' \
      -print0
  )
}

chmod_known_python_files() {
  local source_root="$1"
  local destination_root="$2"
  while IFS= read -r -d '' source; do
    local relative="${source#"$source_root"/}"
    chmod +x "$destination_root/$relative"
  done < <(find "$source_root" -type f -name '*.py' -print0)
}

CONTEXT_SPEC_INVENTORY=""
if ! CONTEXT_SPEC_INVENTORY="$(
  python3 "$PKG/scripts/codex_harness/context_spec_inventory.py" "$PKG"
)"; then
  exit 1
fi
CONTEXT_SPEC_FILES=()
if [ -n "$CONTEXT_SPEC_INVENTORY" ]; then
  mapfile -t CONTEXT_SPEC_FILES <<< "$CONTEXT_SPEC_INVENTORY"
fi

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

# Preflight every root and file tree that the installer may write.  This is
# deliberately broader than merge-only conflict detection: a non-directory
# ancestor or a symlink in any replaceable tree must stop the install before
# even an empty destination directory is created.
for destination_directory in \
  "$REPO" \
  "$REPO/.agents" \
  "$REPO/.codex" \
  "$REPO/.claude" \
  "$REPO/.prguard" \
  "$REPO/.agent-harness" \
  "$REPO/.agent-harness/context" \
  "$REPO/.agent-harness/generated" \
  "$REPO/.agent-harness/scripts" \
  "$REPO/.agent-harness/templates" \
  "$REPO/docs/codex_handoff" \
  "$REPO/machine_readable" \
  "$REPO/scripts/codex_harness" \
  "$REPO/docs/harness" \
  "$REPO/docs/research_program/long_horizon_rescue" \
  "$REPO/harness_templates/vendor/physmath-gpt56" \
  "$VENDOR_DST"
do
  assert_safe_destination_directory \
    "$destination_directory" \
    "installer destination root"
done
assert_safe_destination_file \
  "$REPO/.agent-harness/README.md" \
  ".agent-harness/README.md"
assert_safe_destination_file \
  "$REPO/.agent-harness/generated/CONTEXT_PACK.md" \
  ".agent-harness/generated/CONTEXT_PACK.md"
assert_replace_safe_tree \
  "$PKG/.agent-harness/context" \
  "$REPO/.agent-harness/context" \
  ".agent-harness/context"
assert_replace_safe_tree \
  "$PKG/.agent-harness/templates" \
  "$REPO/.agent-harness/templates" \
  ".agent-harness/templates"
assert_replace_safe_tree \
  "$PKG/.agent-harness/scripts" \
  "$REPO/.agent-harness/scripts" \
  ".agent-harness/scripts"
assert_replace_safe_tree \
  "$PKG/docs/codex_handoff" \
  "$REPO/docs/codex_handoff" \
  "docs/codex_handoff"
assert_replace_safe_tree \
  "$PKG/scripts/codex_harness" \
  "$REPO/scripts/codex_harness" \
  "scripts/codex_harness"
assert_replace_safe_tree \
  "$PKG/harness_templates/docs/harness" \
  "$REPO/docs/harness" \
  "docs/harness"
assert_replace_safe_tree "$VENDOR_SRC" "$VENDOR_DST" "physmath vendor"
for mirror_name in \
  pr_backlog.yaml \
  pr_backlog.json \
  pr_status.yaml \
  authorized_principals.yaml \
  research_remediation_state.yaml
do
  assert_safe_destination_file \
    "$REPO/machine_readable/$mirror_name" \
    "machine_readable/$mirror_name"
done

# Merge-only assets are preflighted before the first destination write.  An
# existing repository policy or intentional Codex setting must be merged by a
# human; the installer never guesses which side owns a conflicting value.
assert_merge_safe_file "$PKG/AGENTS.md" "$REPO/AGENTS.md" "AGENTS.md"
assert_merge_safe_file "$PKG/AGENTS.md.fragment" "$REPO/AGENTS.md.fragment" "AGENTS.md.fragment"
assert_merge_safe_tree "$PKG/.agents" "$REPO/.agents" ".agents"
assert_merge_safe_tree "$PKG/.codex" "$REPO/.codex" ".codex"
assert_merge_safe_tree "$PKG/.claude" "$REPO/.claude" ".claude"
assert_merge_safe_file "$PKG/.prguard/.gitignore" "$REPO/.prguard/.gitignore" ".prguard/.gitignore"
assert_merge_safe_tree \
  "$PKG/docs/research_program/long_horizon_rescue" \
  "$REPO/docs/research_program/long_horizon_rescue" \
  "docs/research_program/long_horizon_rescue"
assert_merge_safe_file \
  "$PKG/docs/harness/PUBLICATION_INTEGRITY.md" \
  "$REPO/docs/harness/PUBLICATION_INTEGRITY.md" \
  "docs/harness/PUBLICATION_INTEGRITY.md"
assert_merge_safe_file \
  "$PKG/docs/harness/OVERNIGHT_CONTROLLER_PUBLICATION_CONTRACT.md" \
  "$REPO/docs/harness/OVERNIGHT_CONTROLLER_PUBLICATION_CONTRACT.md" \
  "docs/harness/OVERNIGHT_CONTROLLER_PUBLICATION_CONTRACT.md"
for relative in "${CONTEXT_SPEC_FILES[@]}"; do
  assert_merge_safe_file \
    "$PKG/$relative" \
    "$REPO/$relative" \
    "registered context spec/$relative"
done

mkdir -p "$REPO/.agents" "$REPO/.codex" "$REPO/.claude" "$REPO/.prguard" "$REPO/docs/codex_handoff" "$REPO/machine_readable" "$REPO/scripts/codex_harness" "$REPO/docs/harness" "$REPO/docs/research_program/long_horizon_rescue" "$REPO/harness_templates/vendor/physmath-gpt56"
copy_merge_only_file "$PKG/AGENTS.md" "$REPO/AGENTS.md"
copy_merge_only_file "$PKG/AGENTS.md.fragment" "$REPO/AGENTS.md.fragment"
copy_merge_only_tree "$PKG/.agents" "$REPO/.agents"
copy_merge_only_tree "$PKG/.codex" "$REPO/.codex"
copy_merge_only_tree "$PKG/.claude" "$REPO/.claude"
copy_merge_only_file "$PKG/.prguard/.gitignore" "$REPO/.prguard/.gitignore"
copy_merge_only_tree \
  "$PKG/docs/research_program/long_horizon_rescue" \
  "$REPO/docs/research_program/long_horizon_rescue"
copy_merge_only_file \
  "$PKG/docs/harness/PUBLICATION_INTEGRITY.md" \
  "$REPO/docs/harness/PUBLICATION_INTEGRITY.md"
copy_merge_only_file \
  "$PKG/docs/harness/OVERNIGHT_CONTROLLER_PUBLICATION_CONTRACT.md" \
  "$REPO/docs/harness/OVERNIGHT_CONTROLLER_PUBLICATION_CONTRACT.md"
for relative in "${CONTEXT_SPEC_FILES[@]}"; do
  copy_merge_only_file "$PKG/$relative" "$REPO/$relative"
done
mkdir -p "$REPO/.agent-harness/scripts"
cp "$PKG/.agent-harness/README.md" "$REPO/.agent-harness/README.md"
copy_replace_tree \
  "$PKG/.agent-harness/context" \
  "$REPO/.agent-harness/context"
copy_replace_tree \
  "$PKG/.agent-harness/templates" \
  "$REPO/.agent-harness/templates"
copy_replace_tree \
  "$PKG/.agent-harness/scripts" \
  "$REPO/.agent-harness/scripts"
copy_replace_tree \
  "$PKG/docs/codex_handoff" \
  "$REPO/docs/codex_handoff"
# docs/codex_handoff is canonical. machine_readable is a synchronized
# compatibility mirror and must never overwrite the canonical install source.
copy_replace_tree \
  "$PKG/scripts/codex_harness" \
  "$REPO/scripts/codex_harness"
python "$REPO/scripts/codex_harness/sync_pr_dag_mirrors.py" --write
copy_replace_tree \
  "$PKG/harness_templates/docs/harness" \
  "$REPO/docs/harness"
if [ ! -e "$VENDOR_DST" ]; then
  copy_replace_tree "$VENDOR_SRC" "$VENDOR_DST"
fi
chmod_known_python_files \
  "$PKG/scripts/codex_harness" \
  "$REPO/scripts/codex_harness"
chmod_known_python_files \
  "$PKG/.agent-harness/scripts" \
  "$REPO/.agent-harness/scripts"
chmod_known_python_files "$PKG/.codex/hooks" "$REPO/.codex/hooks"
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
