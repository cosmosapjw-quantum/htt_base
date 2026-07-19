#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec "$repo_root/venv/bin/python" -B \
  "$repo_root/scripts/codex_harness/pr151_phase.py" "$@"
