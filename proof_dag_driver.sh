#!/usr/bin/env bash
# One-node-per-invocation driver for the htt_base sequential proof DAG.
# Default is dry-run: prints the scan and the node it would delegate.
# Use --go to launch one headless Claude Code run for the next eligible node.
#
# usage: proof_dag_driver.sh /path/to/htt_base [--go]
set -euo pipefail

REPO="${1:?usage: proof_dag_driver.sh REPO [--go]}"
GO="${2:-}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCAN="$HERE/proof_dag_status.py"
PROMPT="$HERE/CLAUDE_CODE_SEQUENTIAL_PROOF_PROMPT_KO.md"

python3 -I "$SCAN" "$REPO"
NEXT="$(python3 -I "$SCAN" "$REPO" --json | python3 -I -c 'import json,sys; print(json.load(sys.stdin)["next"] or "")')"

if [[ -z "$NEXT" ]]; then
  echo "no eligible node (all remaining nodes are blocked, held or need an owner decision)"
  exit 0
fi
echo "next node: $NEXT"

if [[ "$GO" != "--go" ]]; then
  echo "dry-run. re-run with --go to delegate $NEXT to Claude Code."
  exit 0
fi

cd "$REPO"
# Headless runs (claude -p) draw from the Agent SDK credit, not interactive plan limits.
claude -p "$(sed "s/^TARGET_NODE=.*/TARGET_NODE=$NEXT/" "$PROMPT")" \
  --permission-mode acceptEdits \
  --max-turns 400
