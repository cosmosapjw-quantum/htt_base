#!/usr/bin/env bash
set -euo pipefail
if [ "$#" -lt 1 ]; then
  echo "Usage: bash scripts/install_codex_handoff.sh /path/to/htt_base" >&2
  exit 2
fi
REPO="$1"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$REPO/.agents" "$REPO/.codex" "$REPO/docs/codex_handoff" "$REPO/scripts/codex_harness" "$REPO/docs/harness"
cp "$PKG/AGENTS.md" "$REPO/AGENTS.md"
cp "$PKG/agent.md" "$REPO/agent.md"
cp -R "$PKG/.agents/"* "$REPO/.agents/"
cp -R "$PKG/.codex/"* "$REPO/.codex/"
cp -R "$PKG/docs/"* "$REPO/docs/codex_handoff/"
cp -R "$PKG/machine_readable/"* "$REPO/docs/codex_handoff/"
cp -R "$PKG/scripts/codex_harness/"* "$REPO/scripts/codex_harness/"
cp -R "$PKG/harness_templates/docs/harness/"* "$REPO/docs/harness/"
chmod +x "$REPO/scripts/codex_harness/"*.py || true
python "$REPO/scripts/codex_harness/verify_skill_layout.py" "$REPO"
python "$REPO/scripts/codex_harness/validate_pr_dag.py" "$REPO/docs/codex_handoff/pr_backlog.yaml"
echo "Installed v3 Codex handoff skillset into $REPO"
